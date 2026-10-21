"""
Tool Calling 框架 - 可插拔工具注册与执行
"""
import time
import json
from typing import Dict, Callable, Any, Optional, List
from models import ToolResult
from mock_data import get_current_employee, mock_employees, mock_approvals, mock_calendar_events
from agent.knowledge import retrieve_knowledge


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
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' not found",
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
    emp_id = params.get("employee_id") or get_current_employee().id
    emp = mock_employees.get(emp_id)
    if not emp:
        return {"success": False, "error": f"员工 {emp_id} 不存在"}

    leave_type = params.get("leave_type")
    if leave_type:
        balance = getattr(emp.leave_balance, leave_type, None)
        return {"success": True, "data": {"employee": emp.name, "leave_type": leave_type, "balance": balance}}
    return {
        "success": True,
        "data": {
            "employee": emp.name,
            "leave_balance": {
                "annual": emp.leave_balance.annual,
                "sick": emp.leave_balance.sick,
                "personal": emp.leave_balance.personal,
            },
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
    emp = mock_employees.get(params.get("employee_id", ""))
    if not emp:
        return {"success": False, "error": "员工不存在"}
    return {
        "success": True,
        "data": {
            "id": emp.id,
            "name": emp.name,
            "department": emp.department,
            "position": emp.position,
            "level": emp.level,
            "location": emp.location,
            "manager": emp.manager,
            "hire_date": emp.hire_date,
            "contract_type": emp.contract_type,
            "benefits": emp.benefits,
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
    start_date = params["start_date"]
    end_date = params["end_date"]
    conflicts = [e for e in mock_calendar_events if start_date <= e["date"] <= end_date]
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
            "start_date": {"type": "string", "description": "开始日期，格式 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "结束日期，格式 YYYY-MM-DD"},
        },
        "required": ["start_date", "end_date"],
    },
    category="query",
    permission_level="autonomous",
    handler=handle_check_calendar,
)


# 5. 提交休假申请
async def handle_submit_leave_request(params: dict) -> dict:
    import time as _time
    request_id = f"LV-{int(_time.time())}"
    emp = get_current_employee()
    return {
        "success": True,
        "data": {
            "request_id": request_id,
            "status": "pending_approval",
            "approver": emp.manager,
            "leave_type": params.get("leave_type"),
            "start_date": params.get("start_date"),
            "end_date": params.get("end_date"),
            "message": f"休假申请已提交，等待 {emp.manager} 审批",
        },
    }


registry.register(
    name="submit_leave_request",
    description="提交休假申请。这是一个需要确认的操作，会创建审批流程。",
    parameters={
        "type": "object",
        "properties": {
            "leave_type": {"type": "string", "description": "假期类型", "enum": ["annual", "sick", "personal"]},
            "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
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
    request_id = params.get("request_id")
    if request_id:
        return {
            "success": True,
            "data": {
                "request_id": request_id,
                "status": "pending_approval",
                "current_approver": get_current_employee().manager,
                "submitted_at": "2026-01-15T10:30:00",
            },
        }
    return {"success": True, "data": {"approvals": mock_approvals}}


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
    level = emp.level

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
            "employee": emp.name,
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
