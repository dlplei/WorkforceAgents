"""
Tool Calling 框架 - 可插拔工具注册与执行
集成 HR 服务适配器（PostgreSQL / ServiceNow）与向量化政策检索
"""
import time
import json
import os
import logging
from typing import Dict, Callable, Any, Optional, List
from models import ToolResult, HitlActionRequest
from services.hr_adapter import get_hr_adapter
from db.database import get_current_employee
from agent.knowledge import retrieve_knowledge

logger = logging.getLogger(__name__)



# ============ 工具注册表 ============

class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, dict] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        category: str,
        permission_level: str,
        handler: Callable,
    ):
        """注册工具"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "category": category,
            "permission_level": permission_level,
            "handler": handler,
        }

    def get(self, name: str) -> Optional[dict]:
        """获取工具"""
        return self._tools.get(name)

    def get_all(self) -> List[dict]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_for_llm(self) -> List[dict]:
        """获取 LLM 格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, arguments: dict) -> ToolResult:
        """执行工具（具备 RBAC 权限与越权操作硬性校验）"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' not found",
                execution_time=0.0,
            )

        # RBAC 权限硬性校验：普通员工仅能操作或查询本人数据，严禁跨工号越权访问
        current_emp = get_current_employee()
        current_emp_id = current_emp["id"] if isinstance(current_emp, dict) else getattr(current_emp, "id", "E10293")
        current_emp_name = current_emp["name"] if isinstance(current_emp, dict) else getattr(current_emp, "name", "张明")
        target_emp_id = arguments.get("employee_id")
        if target_emp_id and str(target_emp_id).strip() != current_emp_id:
            logger.warning(f"🔒 [RBAC 越权拦截] 员工 {current_emp_id} 试图访问他人工号: {target_emp_id} 的工具 {name}")
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"【权限拦截 (RBAC)】当前登录员工【{current_emp_name} ({current_emp_id})】无权访问或操作其他员工（工号: {target_emp_id}）的数据。根据企业数据安全与保密管理办法，普通员工仅限办理与查看本人名下事务。",
                execution_time=0.0,
            )

        start = time.perf_counter()
        try:
            result = await tool["handler"](arguments)
            return ToolResult(
                tool_name=name,
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                execution_time=time.perf_counter() - start,
            )
        except Exception as e:
            return ToolResult(
                tool_name=name,
                success=False,
                error=str(e),
                execution_time=time.perf_counter() - start,
            )


# 全局注册表
registry = ToolRegistry()


# ============ 注册内置工具 ============

# 1. 查询假期余额
async def handle_query_leave_balance(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp_id = params.get("employee_id") or get_current_employee()["id"]
    emp = adapter.get_employee_profile(emp_id)
    if not emp:
        return {"success": False, "error": f"员工 {emp_id} 不存在"}

    balances = adapter.get_leave_balance(emp_id)
    leave_type = params.get("leave_type")
    if leave_type:
        balance = balances.get(leave_type, 0)
        return {"success": True, "data": {"employee": emp["name"], "leave_type": leave_type, "balance": balance}}
    return {
        "success": True,
        "data": {
            "employee": emp["name"],
            "leave_balance": balances,
        },
    }


registry.register(
    name="query_leave_balance",
    description="查询指定员工的假期余额，包括年假、病假、事假等。如果不指定员工ID，则查询当前登录员工。",
    parameters={
        "type": "object",
        "properties": {
            "employee_id": {"type": "string", "description": "员工ID，不填则查询当前员工"},
            "leave_type": {
                "type": "string",
                "description": "假期类型：annual(年假)/sick(病假)/personal(事假)，不填则查询全部",
                "enum": ["annual", "sick", "personal"],
            },
        },
        "required": [],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_query_leave_balance,
)


# 2. 查询员工信息
async def handle_query_employee_profile(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp_id = params.get("employee_id") or get_current_employee()["id"]
    emp = adapter.get_employee_profile(emp_id)
    if not emp:
        return {"success": False, "error": "员工不存在"}
    return {
        "success": True,
        "data": {
            "id": emp["id"],
            "name": emp["name"],
            "department": emp["department"],
            "position": emp["position"],
            "level": emp["level"],
            "location": emp["location"],
            "manager": emp["manager"],
            "hire_date": emp["hire_date"],
            "contract_type": emp["contract_type"],
            "benefits": emp["benefits"],
        },
    }


registry.register(
    name="query_employee_profile",
    description="查询员工的基本信息，包括部门、职位、汇报关系、入职日期等。",
    parameters={
        "type": "object",
        "properties": {
            "employee_id": {"type": "string", "description": "员工ID"},
        },
        "required": ["employee_id"],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_query_employee_profile,
)


# 3. 检索政策
async def handle_search_policy(params: dict) -> dict:
    results = retrieve_knowledge(
        query=params["query"],
        top_k=int(params.get("top_k", 3)),
        category_filter=params.get("category"),
    )
    return {
        "success": True,
        "data": [
            {
                "doc_id": r.doc_id,
                "title": r.title,
                "content": r.content,
                "score": r.score,
                "category": r.category,
            }
            for r in results
        ],
    }


registry.register(
    name="search_policy",
    description="检索企业政策知识库，返回与查询相关的政策条款。支持按类别过滤。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "查询关键词或问题"},
            "category": {
                "type": "string",
                "description": "政策类别过滤",
                "enum": ["休假", "差旅", "调动", "服务", "考勤", "福利"],
            },
            "top_k": {"type": "string", "description": "返回结果数量，默认3"},
        },
        "required": ["query"],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_search_policy,
)


# 4. 检查日历冲突
async def handle_check_calendar(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    start_date = params["start_date"]
    end_date = params["end_date"]
    conflicts = adapter.check_calendar_conflicts(emp["id"], start_date, end_date)
    return {
        "success": True,
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "conflicts": conflicts,
            "has_conflict": len(conflicts) > 0,
        },
    }


registry.register(
    name="check_calendar",
    description="检查指定日期范围内是否有日历冲突（会议、项目里程碑等）。",
    parameters={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "开始日期，格式 YYYY-MM-DD（基于当前系统年份推断）"},
            "end_date": {"type": "string", "description": "结束日期，格式 YYYY-MM-DD（基于当前系统年份推断）"},
        },
        "required": ["start_date", "end_date"],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_check_calendar,
)


# 5. 提交休假申请
async def handle_submit_leave_request(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    created = adapter.submit_leave_request(
        employee_id=emp["id"],
        applicant=emp["name"],
        leave_type=params.get("leave_type", "annual"),
        start_date=params.get("start_date", ""),
        end_date=params.get("end_date", ""),
        reason=params.get("reason", ""),
        approver=emp["manager"]
    )
    return {
        "success": True,
        "data": {
            "request_id": created.get("id"),
            "status": "pending_approval",
            "approver": emp["manager"],
            "leave_type": params.get("leave_type"),
            "start_date": params.get("start_date"),
            "end_date": params.get("end_date"),
            "message": f"休假申请已提交，等待 {emp['manager']} 审批",
        },
    }


registry.register(
    name="submit_leave_request",
    description="提交休假申请。这是一个需要确认的操作，会创建审批流程。",
    parameters={
        "type": "object",
        "properties": {
            "leave_type": {"type": "string", "description": "假期类型", "enum": ["annual", "sick", "personal"]},
            "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD（基于当前系统年份推断）"},
            "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD（基于当前系统年份推断）"},
            "reason": {"type": "string", "description": "请假原因"},
        },
        "required": ["leave_type", "start_date", "end_date"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_submit_leave_request,
)


# 6. 查询审批状态
async def handle_query_approval_status(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    request_id = params.get("request_id")
    approvals = adapter.get_approvals(emp["id"], request_id)
    return {"success": True, "data": {"approvals": approvals}}


registry.register(
    name="query_approval_status",
    description="查询审批流程状态。",
    parameters={
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "申请单号"},
        },
        "required": [],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_query_approval_status,
)


# 7. 计算差旅预算
async def handle_calculate_travel_budget(params: dict) -> dict:
    days = int(params["days"])
    tier = params["city_tier"]
    emp = get_current_employee()
    level = emp["level"]

    accommodation = {
        "一线": {"P5": 400, "P6": 600, "P7": 600, "P8": 1000},
        "二线": {"P5": 300, "P6": 500, "P7": 500, "P8": 800},
        "三线及以下": {"P5": 250, "P6": 400, "P7": 400, "P8": 600},
    }
    meal = {"一线": 100, "二线": 80, "三线及以下": 60}

    acc_rate = accommodation.get(tier, {}).get(level, 400)
    meal_rate = meal.get(tier, 80)

    return {
        "success": True,
        "data": {
            "destination": params["destination"],
            "days": days,
            "employee_level": level,
            "accommodation_per_night": acc_rate,
            "meal_per_day": meal_rate,
            "total_accommodation": acc_rate * (days - 1),
            "total_meal": meal_rate * days,
            "total_budget": acc_rate * (days - 1) + meal_rate * days,
            "note": "交通费需根据实际出行方式另行计算",
        },
    }


registry.register(
    name="calculate_travel_budget",
    description="根据出差目的地、天数和员工级别计算差旅预算（住宿+餐饮+交通标准）。",
    parameters={
        "type": "object",
        "properties": {
            "destination": {"type": "string", "description": "目的地城市"},
            "days": {"type": "string", "description": "出差天数"},
            "city_tier": {"type": "string", "description": "城市级别", "enum": ["一线", "二线", "三线及以下"]},
        },
        "required": ["destination", "days", "city_tier"],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_calculate_travel_budget,
)


# 8. 生成证明文件
async def handle_generate_document(params: dict) -> dict:
    import time as _time
    doc_id = f"DOC-{int(_time.time())}"
    emp = get_current_employee()
    return {
        "success": True,
        "data": {
            "document_id": doc_id,
            "type": params.get("doc_type"),
            "employee": emp["name"],
            "status": "processing",
            "estimated_time": "1-2个工作日",
            "message": f"{params.get('doc_type')}申请已提交，预计1-2个工作日内完成",
        },
    }


registry.register(
    name="generate_document",
    description="生成各类证明文件（在职证明、收入证明等）。",
    parameters={
        "type": "object",
        "properties": {
            "doc_type": {"type": "string", "description": "证明类型", "enum": ["在职证明", "收入证明", "离职证明"]},
            "purpose": {"type": "string", "description": "用途（如：贷款、签证等）"},
            "language": {"type": "string", "description": "语言版本", "enum": ["中文", "英文"]},
        },
        "required": ["doc_type"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_generate_document,
)


# 9. 创建 HR 服务工单 (Service Request / ServiceNow Sync)
async def handle_create_hr_ticket(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    category = params.get("category", "综合咨询")
    title = params.get("title", "")
    description = params.get("description", "")
    priority = params.get("priority", "medium")

    ticket = adapter.create_ticket(
        employee_id=emp["id"],
        applicant=emp["name"],
        category=category,
        title=title,
        description=description,
        priority=priority
    )
    ext_sync = f"（已同步外部工单: {ticket.get('external_system_id')}）" if ticket.get("external_system_id") else ""
    return {
        "success": True,
        "data": {
            "ticket_id": ticket.get("id"),
            "category": category,
            "title": title,
            "priority": priority,
            "status": "open",
            "applicant": emp["name"],
            "message": f"HR服务工单创建成功{ext_sync}，HR服务专员将在1个工作日内处理并联系您",
            "external_id": ticket.get("external_system_id")
        }
    }


registry.register(
    name="create_hr_ticket",
    description="创建 HR 服务工单（如社保公积金跨城转移、薪酬福利核算复议、考勤打卡申诉、员工关怀与维权、工卡门禁补办等），支持持久化及同步至 ServiceNow。",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "工单分类",
                "enum": ["社保公积金", "薪酬福利", "证明开具", "行政工卡", "综合咨询", "员工关怀与申诉"]
            },
            "title": {"type": "string", "description": "工单简短标题"},
            "description": {"type": "string", "description": "工单详细诉求与说明"},
            "priority": {
                "type": "string",
                "description": "优先级",
                "enum": ["low", "medium", "high", "urgent"]
            },
        },
        "required": ["category", "title", "description"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_create_hr_ticket,
)


# ============ HITL 辅助构建器 ============

def build_hitl_action_request(
    tool_name: str,
    arguments: dict,
    tool_call_id: Optional[str] = None
) -> HitlActionRequest:
    """为 confirmation 级写操作工具构建人机协同 (HITL) 结构化确认凭据"""
    emp = get_current_employee()
    ts = int(time.time() * 1000)
    action_id = f"hitl_{tool_name}_{ts}"

    emp_name = getattr(emp, "name", None) or (emp.get("name") if isinstance(emp, dict) else "张明")
    emp_id = getattr(emp, "id", None) or (emp.get("id") if isinstance(emp, dict) else "E10293")
    emp_dept = getattr(emp, "department", None) or (emp.get("department") if isinstance(emp, dict) else "研发部")
    emp_mgr = getattr(emp, "manager", None) or (emp.get("manager") if isinstance(emp, dict) else "王经理")

    if tool_name == "submit_leave_request":
        leave_type_names = {
            "annual": "年假 (带薪)",
            "sick": "带薪病假",
            "personal": "事假 (无薪)",
            "marriage": "婚假",
            "maternity": "产假",
            "paternity": "陪产假",
            "bereavement": "丧假",
        }
        lt = arguments.get("leave_type", "annual")
        lt_label = leave_type_names.get(lt, lt)
        start_date = arguments.get("start_date", "未指定")
        end_date = arguments.get("end_date", "未指定")
        reason = arguments.get("reason", "个人休假")

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="请假申请审批核实 (Human-in-the-Loop)",
            category="leave",
            summary={
                "申请员工": f"{emp_name} ({emp_id})",
                "所属部门": emp_dept,
                "假期类型": lt_label,
                "请假周期": f"{start_date} 至 {end_date}",
                "请假事由": reason,
                "直属审批人": emp_mgr,
                "生效机制": "提交后将写入 HR 数据库并流转审批",
            },
            raw_arguments=arguments,
            status="pending",
            risk_level="medium",
            created_at=ts,
        )

    elif tool_name == "generate_document":
        doc_type_names = {
            "employment_proof": "在职证明",
            "income_proof": "收入证明",
            "internship_proof": "实习证明",
            "leaving_proof": "离职证明",
        }
        dt = arguments.get("doc_type", "employment_proof")
        dt_label = doc_type_names.get(dt, dt)
        purpose = arguments.get("purpose", "办理业务")
        lang = arguments.get("language", "zh")
        lang_label = "中文版 (电子公章)" if lang == "zh" else "英文版 (电子公章)"

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="HR 正式人事证明开具确认",
            category="document",
            summary={
                "申请员工": f"{emp_name} ({emp_id})",
                "证明类别": dt_label,
                "开具用途": purpose,
                "语言版本": lang_label,
                "印章效力": "企业人事部电子公章 (具有法律效力)",
            },
            raw_arguments=arguments,
            status="pending",
            risk_level="low",
            created_at=ts,
        )

    elif tool_name == "create_hr_ticket":
        cat = arguments.get("category", "综合咨询")
        title = arguments.get("title", "HR咨询")
        priority = arguments.get("priority", "medium")
        priority_labels = {"low": "普通", "medium": "中等", "high": "高优先", "urgent": "紧急 (2小时内响应)"}
        desc = arguments.get("description", "")

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="HR 运营服务工单提交确认",
            category="ticket",
            summary={
                "申请员工": f"{emp_name} ({emp_id})",
                "工单业务分类": cat,
                "工单标题": title,
                "紧急程度": priority_labels.get(priority, priority),
                "诉求说明": desc,
                "流转目标": "HR 共享服务中心 (SSC) / ServiceNow",
            },
            raw_arguments=arguments,
            status="pending",
            risk_level="medium",
            created_at=ts,
        )

    # 兜底通用 HITL 动作
    return HitlActionRequest(
        action_id=action_id,
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        title=f"高敏感操作授权确认: {tool_name}",
        category="general",
        summary={
            "执行员工": f"{emp_name} ({emp_id})",
            "工具名称": tool_name,
            "参数载荷": json.dumps(arguments, ensure_ascii=False),
        },
        raw_arguments=arguments,
        status="pending",
        risk_level="medium",
        created_at=ts,
    )


