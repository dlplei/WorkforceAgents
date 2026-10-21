"""
Mock 数据 - 员工、审批、日历等
"""
from models import EmployeeProfile, LeaveBalance
from typing import Dict, List


# ============ Mock 员工数据 ============

mock_employees: Dict[str, EmployeeProfile] = {
    "E10293": EmployeeProfile(
        id="E10293",
        name="张明",
        department="技术研发部",
        position="高级前端工程师",
        level="P6",
        location="北京",
        manager="李伟",
        hire_date="2022-03-15",
        contract_type="全职",
        leave_balance=LeaveBalance(annual=7, sick=5, personal=2),
        benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作"],
    ),
    "E10456": EmployeeProfile(
        id="E10456",
        name="王芳",
        department="人力资源部",
        position="HRBP",
        level="P7",
        location="上海",
        manager="赵静",
        hire_date="2020-08-01",
        contract_type="全职",
        leave_balance=LeaveBalance(annual=12, sick=8, personal=3),
        benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"],
    ),
}

# 默认登录员工
CURRENT_EMPLOYEE_ID = "E10293"


def get_current_employee() -> EmployeeProfile:
    """获取当前登录员工"""
    return mock_employees[CURRENT_EMPLOYEE_ID]


# ============ Mock 审批数据 ============

mock_approvals = [
    {"id": "APR-001", "type": "年假申请", "status": "pending", "applicant": "张明", "date": "2026-01-15"},
    {"id": "APR-002", "type": "差旅报销", "status": "approved", "applicant": "张明", "date": "2026-01-10"},
]


# ============ Mock 日历数据 ============

mock_calendar_events = [
    {"date": "2026-01-20", "title": "项目评审会", "type": "meeting"},
    {"date": "2026-01-22", "title": "Sprint Planning", "type": "meeting"},
    {"date": "2026-02-01", "title": "春节假期开始", "type": "holiday"},
]
