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
from services.permission_service import PermissionService
from services.policy_config import infer_city_tier, get_travel_rates
from db.database import (
    get_current_employee,
    check_duplicate_document,
    check_duplicate_leave,
    create_document,
    normalize_doc_type,
)
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
        if target_emp_id and not PermissionService.can_access_target_employee(current_emp, target_emp_id, tool_name=name):
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
    emp_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id", "E10293")
    emp_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name", "张明")
    emp_mgr = emp.get("manager") if isinstance(emp, dict) else getattr(emp, "manager", "王经理")

    start_date = params.get("start_date", "").strip()
    end_date = params.get("end_date", "").strip()
    leave_type = params.get("leave_type", "annual")
    reason = params.get("reason", "")

    # 前置业务防重校验：排他区间重叠检测
    dup_check = check_duplicate_leave(emp_id, start_date, end_date)
    if dup_check:
        logger.warning(f"🛡️ [休假防重拦截] 员工 {emp_id} 申请 {start_date} 至 {end_date} 冲突: {dup_check['message']}")
        return {
            "success": False,
            "error": dup_check["message"],
            "data": {
                "message": dup_check["message"],
                "conflict": dup_check
            }
        }

    try:
        created = adapter.submit_leave_request(
            employee_id=emp_id,
            applicant=emp_name,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            approver=f"{emp_mgr} (直属主管)"
        )
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "data": {"message": str(e)}
        }

    return {
        "success": True,
        "data": {
            "request_id": created.get("id"),
            "status": "pending_approval",
            "approver": emp_mgr,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "message": f"休假申请已提交，等待 {emp_mgr} 审批",
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
    status = params.get("status")
    applicant_name = params.get("applicant_name")
    approval_type = params.get("approval_type")
    scope = params.get("scope")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    time_range = params.get("time_range")

    # 快捷相对时间推断（基于企业当前系统日期）
    from datetime import datetime as dt, timedelta
    now = dt.now()
    if time_range:
        tr = str(time_range).lower()
        if "7" in tr or "week" in tr or "周" in tr:
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif "30" in tr or "month" in tr or "月" in tr:
            if "last" in tr or "上" in tr:
                first_this_month = dt(now.year, now.month, 1)
                last_month_end = first_this_month - timedelta(days=1)
                start_date = dt(last_month_end.year, last_month_end.month, 1).strftime("%Y-%m-%d")
                end_date = last_month_end.strftime("%Y-%m-%d")
            else:
                start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
                end_date = now.strftime("%Y-%m-%d")
        elif "year" in tr or "年" in tr:
            start_date = f"{now.year}-01-01"
            end_date = f"{now.year}-12-31"

    approvals = adapter.get_approvals(
        employee_id=emp["id"],
        request_id=request_id,
        status=status,
        scope=scope,
        applicant_name=applicant_name,
        start_date=start_date,
        end_date=end_date,
        approval_type=approval_type,
    )
    return {
        "success": True, 
        "data": {
            "approvals": approvals,
            "total": len(approvals),
            "filters": {
                "request_id": request_id,
                "status": status,
                "applicant_name": applicant_name,
                "start_date": start_date,
                "end_date": end_date,
                "scope": scope,
            }
        }
    }


registry.register(
    name="query_approval_status",
    description="多维查询审批流程状态与历史记录。支持按单号、审批状态、时间区间、申请人姓名或单据类型灵活查询。用户即使没有提供具体单号，也可直接调用此工具查询近期的审批或名下待办，严禁向用户生硬索要单号！",
    parameters={
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "申请单号（可选，如 APR-001）"},
            "status": {"type": "string", "description": "审批状态筛选：pending(待审批), approved(已通过), rejected(已驳回), all(全部)"},
            "applicant_name": {"type": "string", "description": "申请人姓名（如主管查询指定员工‘张明’的申请，可选）"},
            "approval_type": {"type": "string", "description": "单据类型关键字，如'年假'、'差旅'、'证明'等（可选）"},
            "time_range": {"type": "string", "description": "快捷时间区间：'last_7_days'(近7天), 'this_month'(本月), 'last_month'(上月), 'this_year'(今年)"},
            "start_date": {"type": "string", "description": "起始日期，格式 YYYY-MM-DD（可选）"},
            "end_date": {"type": "string", "description": "截止日期，格式 YYYY-MM-DD（可选）"},
            "scope": {"type": "string", "description": "查询视角：'my_requests'(我提交的), 'my_approvals'(我经办审批的), 'all'(全部)"},
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
    tier = params.get("city_tier") or infer_city_tier(params.get("destination", ""))
    emp = get_current_employee()
    level = emp["level"]

    acc_rate, meal_rate = get_travel_rates(tier, level)

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
    emp = get_current_employee()
    emp_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id", "E10293")
    emp_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name", "张明")

    raw_doc_type = params.get("doc_type", "employment_proof")
    purpose = params.get("purpose", "办理业务")
    raw_lang = params.get("language", "中文")
    language = "英文" if any(k in str(raw_lang).lower() for k in ["英", "en", "english"]) else "中文"
    norm_doc_type = normalize_doc_type(raw_doc_type)

    # 1. 业务防重校验：在途单据防重与 30 天冷静期校验 (POL-005)
    dup_info = check_duplicate_document(emp_id, norm_doc_type, purpose)
    if dup_info:
        logger.warning(f"🛡️ [证明防重拦截] 员工 {emp_id} 重复申请 {norm_doc_type} ({purpose}): {dup_info['message']}")
        return {
            "success": False,
            "error": dup_info["message"],
            "data": {
                "blocked": True,
                "reason": dup_info["type"],
                "existing_id": dup_info.get("existing_doc", {}).get("id"),
            },
        }

    # 2. 正常落库入库
    doc_id = f"DOC-{int(_time.time())}"
    create_document(
        doc_id=doc_id,
        employee_id=emp_id,
        applicant=emp_name,
        doc_type=norm_doc_type,
        purpose=purpose,
        language=language,
        status="processing",
        metadata={"source": "agent_hitl", "params": params},
    )

    return {
        "success": True,
        "data": {
            "document_id": doc_id,
            "type": norm_doc_type,
            "purpose": purpose,
            "language": language,
            "employee": emp_name,
            "status": "processing",
            "estimated_time": "1-2个工作日",
            "message": f"【{norm_doc_type}】申请已成功提交（单号：{doc_id}），预计1-2个工作日内完成盖章与电子件签发",
        },
    }


registry.register(
    name="generate_document",
    description="生成各类证明文件（在职证明、收入证明、离职证明等）。默认语言版本为中文，仅当用户明确要求英文时才开具英文版。",
    parameters={
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "description": "证明类型",
                "enum": ["在职证明", "收入证明", "离职证明", "实习证明"],
            },
            "purpose": {
                "type": "string",
                "description": "用途（如：签证、贷款、购房、子女入学等）",
            },
            "language": {
                "type": "string",
                "description": "语言版本：'中文' 或 '英文'。若用户未特别说明英文，一律默认为'中文'",
                "enum": ["中文", "英文"],
            },
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

# 9. 主管查询待审批单
async def handle_query_pending_approvals(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    approver_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name")
    approver_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id")
    pending = adapter.get_pending_approvals(approver_name or approver_id)
    return {
        "success": True,
        "data": {
            "approver": approver_name,
            "count": len(pending),
            "pending_approvals": pending
        }
    }


registry.register(
    name="query_pending_approvals",
    description="查询名下等待当前主管或审批人审核的单据列表（如员工请假、出差等申请）。",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_query_pending_approvals,
)


# 10. 主管执行审批决策
async def handle_review_approval_request(params: dict) -> dict:
    adapter = get_hr_adapter()
    emp = get_current_employee()
    approver_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name")
    approval_id = params.get("approval_id")
    decision = params.get("decision", "approved")
    comment = params.get("comment", "已阅，同意")

    if not approval_id:
        pending = adapter.get_pending_approvals(approver_name)
        target_applicant = params.get("applicant_name")
        target_type = params.get("approval_type") or params.get("type")
        if target_applicant:
            matched = [p for p in pending if p.get("applicant") == target_applicant]
            # 意图智能感知：根据 comment 或类型参数优先匹配对应类别的待审单据
            comment_text = params.get("comment", "")
            if "假" in comment_text or (target_type and "假" in target_type):
                leave_matched = [p for p in matched if "假" in (p.get("approval_type") or "") or p.get("approval_type") in ("annual", "sick", "personal", "leave") or str(p.get("id", "")).startswith("APR-")]
                if leave_matched:
                    matched = leave_matched
            elif "报销" in comment_text or (target_type and "报销" in target_type):
                exp_matched = [p for p in matched if "报销" in (p.get("approval_type") or "") or str(p.get("id", "")).startswith("EXP-")]
                if exp_matched:
                    matched = exp_matched
            elif "调动" in comment_text or "转岗" in comment_text or (target_type and ("调动" in target_type or "转岗" in target_type)):
                trf_matched = [p for p in matched if "调动" in (p.get("approval_type") or "") or str(p.get("id", "")).startswith("TRF-")]
                if trf_matched:
                    matched = trf_matched
            if matched:
                approval_id = matched[0].get("id")
        elif len(pending) == 1:
            approval_id = pending[0].get("id")

    if not approval_id:
        return {"success": False, "error": "未指定需要审批的审批单号 (approval_id)，请指明具体单号或申请人姓名。"}

    res = adapter.process_approval(
        approval_id=approval_id,
        approver_name_or_id=approver_name,
        decision=decision,
        comment=comment
    )
    if not res.get("success", True):
        return {
            "success": False,
            "error": res.get("message", "审批执行失败"),
            "data": {
                "message": res.get("message", "审批执行失败"),
                "approval": res.get("approval", {})
            }
        }
    return {
        "success": True,
        "data": {
            "message": res.get("message", ""),
            "approval": res.get("approval", {}),
            "leave_balance_deducted": res.get("leave_balance_deducted")
        }
    }


registry.register(
    name="review_approval_request",
    description="主管或审批人对员工提交的待办单据进行审核判定（通过或驳回）。审批通过会自动扣减申请人假期余额并更新日历日程。",
    parameters={
        "type": "object",
        "properties": {
            "approval_id": {
                "type": "string",
                "description": "待审批单号，例如 'APR-001'。若不确定可通过 query_pending_approvals 先行查询",
            },
            "decision": {
                "type": "string",
                "description": "审批决策：'approved'（通过/同意）或 'rejected'（驳回/拒绝）",
                "enum": ["approved", "rejected"],
            },
            "comment": {
                "type": "string",
                "description": "主管审批意见或批注说明",
            },
            "applicant_name": {
                "type": "string",
                "description": "申请人姓名（如张明，可用于自动定位匹配单号）",
            },
        },
        "required": ["decision"],
    },
    category="action",
    permission_level="autonomous",
    handler=handle_review_approval_request,
)


# 11. 提交差旅申请 (Travel Lifecycle Request)
async def handle_submit_travel_request(params: dict) -> dict:
    import datetime as _dt
    adapter = get_hr_adapter()
    emp = get_current_employee()
    emp_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id", "E10293")
    emp_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name", "张明")
    emp_level = emp["level"] if isinstance(emp, dict) else getattr(emp, "level", "P6")
    emp_manager = getattr(emp, "manager", None) or (emp.get("manager") if isinstance(emp, dict) else "李伟")

    dest = params.get("destination", "上海")
    start_date = params.get("start_date", "")
    end_date = params.get("end_date", "")
    purpose = params.get("purpose", "因公出差与客户交流")
    transportation = params.get("transportation")
    if not transportation:
        if emp_level in ("P6", "P7"):
            transportation = "高铁一等座 / 航班经济舱"
        elif emp_level in ("P8", "M1", "M2"):
            transportation = "高铁商务座 / 航班商务舱"
        else:
            transportation = "高铁二等座 / 航班经济舱"

    days = 1
    if start_date and end_date:
        try:
            d1 = _dt.date.fromisoformat(start_date)
            d2 = _dt.date.fromisoformat(end_date)
            diff = (d2 - d1).days + 1
            if diff > 0:
                days = diff
        except Exception:
            pass

    tier = params.get("city_tier") or infer_city_tier(dest)
    accommodation = {
        "一线": {"P5": 400, "P6": 600, "P7": 600, "P8": 1000},
        "二线": {"P5": 300, "P6": 500, "P7": 500, "P8": 800},
        "三线及以下": {"P5": 250, "P6": 400, "P7": 400, "P8": 600},
    }
    meal = {"一线": 100, "二线": 80, "三线及以下": 60}
    acc_rate = accommodation.get(tier, {}).get(emp_level, 600)
    meal_rate = meal.get(tier, 100)
    nights = max(0, days - 1)
    std_budget = float(nights * acc_rate + days * meal_rate)
    estimated_budget = float(params.get("estimated_budget") or std_budget)

    try:
        created = adapter.submit_travel_request(
            employee_id=emp_id,
            applicant=emp_name,
            destination=dest,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            estimated_budget=estimated_budget,
            transportation=transportation,
            approver=emp_manager
        )
        return {
            "success": True,
            "data": {
                "approval_id": created["id"],
                "employee": emp_name,
                "destination": dest,
                "city_tier": tier,
                "duration": f"{start_date} 至 {end_date} (共{days}天)",
                "estimated_budget": estimated_budget,
                "transportation": transportation,
                "purpose": purpose,
                "approver": emp_manager,
                "status": "pending",
                "message": f"差旅申请已成功提交（单号：{created['id']}），已流转至直属主管【{emp_manager}】审批",
            }
        }
    except Exception as e:
        return {"success": False, "error": f"提交差旅申请失败: {str(e)}"}


registry.register(
    name="submit_travel_request",
    description="提交正式出差/差旅申请。涉及差旅审批流程与预算预扣，这是一个需要确认的高风险写操作，会创建审批流程。",
    parameters={
        "type": "object",
        "properties": {
            "destination": {"type": "string", "description": "出差目的地城市（如：上海、深圳、成都、杭州等）"},
            "start_date": {"type": "string", "description": "出差开始日期，格式 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "出差结束日期，格式 YYYY-MM-DD"},
            "purpose": {"type": "string", "description": "出差主要事由与业务目标说明"},
            "estimated_budget": {"type": "number", "description": "预估总差旅预算金额（元），未提供时系统按职级与城市差标自动测算"},
            "transportation": {"type": "string", "description": "建议或拟乘交通方式（如：高铁一等座、航班经济舱）"},
        },
        "required": ["destination", "start_date", "end_date", "purpose"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_submit_travel_request,
)


# 12. 提交员工调动/转岗申请 (Internal Mobility / Transfer Request)
async def handle_submit_transfer_request(params: dict) -> dict:
    import datetime as _dt
    adapter = get_hr_adapter()
    emp = get_current_employee()
    emp_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id", "E10293")
    emp_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name", "张明")
    cur_dept = emp["department"] if isinstance(emp, dict) else getattr(emp, "department", "技术研发部")
    cur_loc = emp["location"] if isinstance(emp, dict) else getattr(emp, "location", "北京")
    cur_pos = emp["position"] if isinstance(emp, dict) else getattr(emp, "position", "高级前端工程师")
    emp_manager = getattr(emp, "manager", None) or (emp.get("manager") if isinstance(emp, dict) else "李伟")

    target_dept = params.get("target_department", cur_dept)
    target_loc = params.get("target_location", cur_loc)
    target_pos = params.get("target_position", cur_pos)
    effective_date = params.get("effective_date", "")
    reason = params.get("reason", "个人发展与岗位调动")

    # 司龄合规前置检查（《POL-004 员工调动管理办法》：入职满1年）
    hire_date_str = emp.get("hire_date") if isinstance(emp, dict) else getattr(emp, "hire_date", "2022-03-15")
    try:
        hire_d = _dt.date.fromisoformat(hire_date_str)
        today = _dt.date.today()
        tenure_months = (today.year - hire_d.year) * 12 + (today.month - hire_d.month)
        if tenure_months < 12:
            return {
                "success": False,
                "error": f"不满足调动政策资格要求：根据《POL-004 员工调动管理办法》，在岗工作需满1年，当前在岗约 {tenure_months} 个月。"
            }
    except Exception:
        pass

    is_cross_city = (target_loc != cur_loc)
    approver = f"{emp_manager} (转出主管) / 王芳 (HRBP)"
    if is_cross_city:
        approver += " / 薪酬委员会"

    try:
        created = adapter.submit_transfer_request(
            employee_id=emp_id,
            applicant=emp_name,
            target_department=target_dept,
            target_location=target_loc,
            target_position=target_pos,
            effective_date=effective_date,
            reason=reason,
            approver=approver
        )
        return {
            "success": True,
            "data": {
                "approval_id": created["id"],
                "employee": emp_name,
                "from_department": f"{cur_dept} ({cur_loc})",
                "to_department": f"{target_dept} ({target_loc})",
                "target_position": target_pos,
                "effective_date": effective_date,
                "is_cross_city": is_cross_city,
                "benefits_notice": "根据《POL-004》享有最高2万元异地搬迁补贴与首月房补，社保公积金次月转移" if is_cross_city else "同城岗位调动，社保公积金及薪资保持平移",
                "approver": approver,
                "status": "pending",
                "message": f"调动/转岗申请已成功提交（单号：{created['id']}），已启动双向主管与 HRBP 审批协同流转",
            }
        }
    except Exception as e:
        return {"success": False, "error": f"提交调动申请失败: {str(e)}"}


registry.register(
    name="submit_transfer_request",
    description="提交内部转岗/调动申请（如从北京调往上海分公司、同城跨部门等）。涉及跨部门组织架构、人事合同与异地补贴审批，这是一个高风险确认操作，会创建审批流程。",
    parameters={
        "type": "object",
        "properties": {
            "target_department": {"type": "string", "description": "拟调往的目标部门（如：技术研发部、业务产品部、华东销售部等）"},
            "target_location": {"type": "string", "description": "拟调往的目标工作城市（如：上海、北京、深圳等）"},
            "target_position": {"type": "string", "description": "拟任职位名称（如未变动可保持原职级岗位）"},
            "effective_date": {"type": "string", "description": "期望调动生效日期，格式 YYYY-MM-DD"},
            "reason": {"type": "string", "description": "申请调动原因与业务诉求说明"},
        },
        "required": ["target_department", "target_location", "effective_date", "reason"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_submit_transfer_request,
)

async def handle_submit_expense_claim(params: dict) -> dict:
    """处理员工费用与差旅报销申请提交"""
    adapter = get_hr_adapter()
    emp = get_current_employee()
    emp_id = emp["id"] if isinstance(emp, dict) else getattr(emp, "id", "E10293")
    emp_name = emp["name"] if isinstance(emp, dict) else getattr(emp, "name", "张明")
    emp_mgr = getattr(emp, "manager", None) or (emp.get("manager") if isinstance(emp, dict) else "李伟")

    amount = params.get("amount")
    category = params.get("category", "差旅报销")
    description = params.get("description", "")
    invoice_count = params.get("invoice_count", 1)
    travel_request_id = params.get("travel_request_id")

    try:
        amt = float(amount)
        if amt <= 0:
            return {"success": False, "error": "报销金额必须大于 0 元"}
    except (ValueError, TypeError):
        return {"success": False, "error": "报销金额格式不合法，请输入有效数字"}

    inv_cnt = max(1, int(invoice_count or 1))

    exp_approver = f"{emp_mgr} (直属主管) / 陈敏 (财务复核)"
    approval = adapter.submit_expense_claim(
        employee_id=emp_id,
        applicant=emp_name,
        amount=amt,
        category=category,
        description=description,
        invoice_count=inv_cnt,
        travel_request_id=travel_request_id,
        approver=exp_approver
    )

    return {
        "success": True,
        "data": {
            "status": "submitted",
            "approval_id": approval.get("id"),
            "approval_type": approval.get("approval_type", "差旅报销"),
            "applicant": emp_name,
            "amount": amt,
            "category": category,
            "invoice_count": inv_cnt,
            "travel_request_id": travel_request_id,
            "approver": approval.get("approver") or exp_approver,
            "current_status": "pending",
            "is_duplicate": approval.get("is_duplicate", False),
            "message": f"费用报销申请【{approval.get('id')}】已成功提报！金额 ¥{amt:.2f}，已流转至直属主管【{emp_mgr}】审批及财务专员【陈敏】复核。",
        }
    }


async def handle_query_org_chart(params: dict) -> dict:
    """处理组织架构与汇报链关系查询"""
    adapter = get_hr_adapter()
    employee_name_or_id = params.get("employee_name_or_id")
    query_type = params.get("query_type", "full")
    chart = adapter.query_org_chart(
        employee_name_or_id=employee_name_or_id,
        query_type=query_type
    )
    return {
        "success": True,
        "data": chart
    }


registry.register(
    name="submit_expense_claim",
    description="提交差旅或日常费用报销申请（如差旅交通、住宿、餐费、培训认证考试等报销）。这是一个涉及财务支出的确认操作（HITL），会创建审批流程。",
    parameters={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "报销总金额（元，必须大于0）"},
            "category": {"type": "string", "description": "报销类别（如：差旅报销、日常报销、培训认证报销），默认为差旅报销"},
            "description": {"type": "string", "description": "费用产生事由及明细说明（如：上海客户支持往返交通与住宿费）"},
            "invoice_count": {"type": "integer", "description": "随附发票或凭证张数，默认为 1"},
            "travel_request_id": {"type": "string", "description": "关联的出差预申请审批单号（如 TRV-123，若无则留空）"},
        },
        "required": ["amount", "description"],
    },
    category="action",
    permission_level="confirmation",
    handler=handle_submit_expense_claim,
)

registry.register(
    name="query_org_chart",
    description="查询企业组织架构与汇报链关系。可查询指定员工或当前员工的直属主管、向上汇报链条、直接下属、同部门同事以及对口 HRBP 信息。",
    parameters={
        "type": "object",
        "properties": {
            "employee_name_or_id": {"type": "string", "description": "员工姓名或工号（如'张明'、'李伟'、'E10293'），默认查询当前登录员工"},
            "query_type": {
                "type": "string",
                "enum": ["full", "reporting_line", "team_members", "department_overview"],
                "description": "查询类型：'full' 综合信息，'reporting_line' 汇报线，'team_members' 团队成员及下属，'department_overview' 部门结构",
            },
        },
    },
    category="query",
    permission_level="readonly",
    handler=handle_query_org_chart,
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
        
        # 兼容 "中文"、"zh"、"英文"、"en" 等不同写法，未指明或包含中文词根时默认为中文版
        raw_lang = str(arguments.get("language", "中文")).strip().lower()
        if any(keyword in raw_lang for keyword in ["英", "en", "english"]):
            lang_label = "英文版 (电子公章)"
            arguments["language"] = "英文"
        else:
            lang_label = "中文版 (电子公章)"
            arguments["language"] = "中文"

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

    elif tool_name == "submit_travel_request":
        import datetime as _dt
        dest = arguments.get("destination", "未指定")
        start_date = arguments.get("start_date", "未指定")
        end_date = arguments.get("end_date", "未指定")
        purpose = arguments.get("purpose", "因公出差")
        transportation = arguments.get("transportation", "高铁一等座 / 航班经济舱")

        days = 1
        if start_date != "未指定" and end_date != "未指定":
            try:
                d1 = _dt.date.fromisoformat(start_date)
                d2 = _dt.date.fromisoformat(end_date)
                days = max(1, (d2 - d1).days + 1)
            except Exception:
                pass

        tier = infer_city_tier(dest)
        acc_standards = {"一线": 600, "二线": 500, "三线及以下": 400}
        meal_standards = {"一线": 100, "二线": 80, "三线及以下": 60}
        nights = max(0, days - 1)
        std_budget = nights * acc_standards.get(tier, 500) + days * meal_standards.get(tier, 80)
        user_budget = arguments.get("estimated_budget")
        budget_str = f"¥{user_budget}" if user_budget else f"¥{std_budget} (按《POL-003》{tier}城市差标预估)"

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="员工出差差旅申请核实与确认 (HITL)",
            category="travel",
            summary={
                "出差员工": f"{emp_name} ({emp_id})",
                "出差目的地": f"{dest} ({tier}城市)",
                "出行周期": f"{start_date} 至 {end_date} (共 {days} 天)",
                "出差主要事由": purpose,
                "拟乘交通": transportation,
                "预估差旅差标": budget_str,
                "审批流转": f"直属主管【{emp_mgr}】审批",
                "生效机制": "确认后自动写入 HR 差旅系统审批台账",
            },
            raw_arguments=arguments,
            status="pending",
            risk_level="medium",
            created_at=ts,
        )

    elif tool_name == "submit_transfer_request":
        target_dept = arguments.get("target_department", emp_dept)
        target_loc = arguments.get("target_location", "未指定")
        target_pos = arguments.get("target_position", "保持原岗位")
        effective_date = arguments.get("effective_date", "未指定")
        reason = arguments.get("reason", "个人发展")

        cur_loc = getattr(emp, "location", None) or (emp.get("location") if isinstance(emp, dict) else "北京")
        is_cross = (target_loc != cur_loc and target_loc != "未指定")
        policy_notice = "跨城异地调动：享有最高2万元搬迁补贴与首月房补；社保公积金次月转移至新城市" if is_cross else "同城部门调动：社保公积金与基本薪资标准平移"

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="员工内部调动/转岗申请核验 (HITL)",
            category="transfer",
            summary={
                "申请员工": f"{emp_name} ({emp_id})",
                "当前岗位": f"{emp_dept} · {getattr(emp, 'position', '高级前端工程师')} ({cur_loc})",
                "拟调往部门": f"{target_dept} · {target_loc} (拟任: {target_pos})",
                "期望生效日期": effective_date,
                "调动事由": reason,
                "政策合规预检": "司龄已满1年，符合《POL-004 员工调动管理办法》申请资格",
                "福利与人事须知": policy_notice,
                "审批协同流转": f"转出主管【{emp_mgr}】 + 目标部门总监 + HRBP 王芳会签",
            },
            raw_arguments=arguments,
            status="pending",
            risk_level="high",
            created_at=ts,
        )
    elif tool_name == "submit_expense_claim":
        amount = float(arguments.get("amount") or 0.0)
        category = arguments.get("category", "差旅报销")
        description = arguments.get("description", "业务差旅费用报销")
        invoice_count = int(arguments.get("invoice_count") or 1)
        travel_req_id = arguments.get("travel_request_id")

        return HitlActionRequest(
            action_id=action_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            title="员工费用与差旅报销提报核实 (HITL)",
            category="expense",
            summary={
                "报销员工": f"{emp_name} ({emp_id})",
                "报销类别": category,
                "报销总金额": f"¥{amount:.2f}",
                "发票凭据": f"{invoice_count} 张 (须为正规合规税务发票)",
                "费用事由": description,
                "关联出差审批": travel_req_id if travel_req_id else "无 (非关联合并出差)",
                "政策合规提示": "按《POL-003》出差结束后5个工作日内报销，超标部分需事先审批",
                "流转审批人": f"直属主管【{emp_mgr}】审批 / 陈敏 (财务复核)",
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


