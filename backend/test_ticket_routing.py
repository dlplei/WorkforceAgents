"""
Unit test for HR ticket auto-assignment based on Ulrich HR 3-tier delivery model.
"""
import pytest
import os
import sys
import uuid

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import resolve_ticket_assignee, create_hr_ticket, query_hr_tickets, init_db, DEFAULT_EMPLOYEE_ID
from services.hr_adapter import get_hr_adapter

init_db()


def test_resolve_ticket_assignee_transfer_hrbp():
    # E10293 is 张明 in Tech Dept, HRBP is 王芳
    assignee = resolve_ticket_assignee(
        employee_id=DEFAULT_EMPLOYEE_ID,
        category="转岗调动",
        title="撤销转岗申请 TRF-144",
        description="因家庭原因希望撤回转岗申请"
    )
    assert assignee == "王芳 (对口 HRBP)", f"Expected 王芳 (对口 HRBP), got {assignee}"


def test_resolve_ticket_assignee_keywords_hrbp():
    # Category is 综合咨询, but description mentions 撤销调动申请
    assignee = resolve_ticket_assignee(
        employee_id=DEFAULT_EMPLOYEE_ID,
        category="综合咨询",
        title="TRF-144 作废咨询",
        description="请问如何撤销已经提报的内部调动审批 TRF-144？"
    )
    assert assignee == "王芳 (对口 HRBP)", f"Expected 王芳 (对口 HRBP), got {assignee}"


def test_resolve_ticket_assignee_specialists():
    # Housing fund -> 动态解析具备 SystemRole.HR 的在岗专员刘洋
    assignee_fund = resolve_ticket_assignee(
        employee_id=DEFAULT_EMPLOYEE_ID,
        category="社保公积金",
        title="上海公积金跨城转移",
        description="需要将北京公积金转出"
    )
    assert assignee_fund == "刘洋 (招聘与员工关系专员)"

    # Payroll -> 动态解析具备 SystemRole.FINANCE 的在职财务专员陈敏
    assignee_pay = resolve_ticket_assignee(
        employee_id=DEFAULT_EMPLOYEE_ID,
        category="薪酬福利",
        title="加班津贴核算复议",
        description="上月加班费似乎未计入"
    )
    assert assignee_pay == "陈敏 (财务专员 / 报销审核)"


def test_resolve_ticket_assignee_dynamic_role_based():
    """验证派单引擎基于系统角色与组织关系的纯动态特性，无任何名字硬编码"""
    from db.database import find_hrbp_for_employee, find_specialist_by_role, SystemRole
    # 动态匹配 HRBP
    hrbp = find_hrbp_for_employee("E10293")
    assert hrbp is not None
    assert SystemRole.HRBP.value in hrbp.roles

    # 动态匹配财务专家
    fin = find_specialist_by_role(SystemRole.FINANCE, department_hint="财务部")
    assert fin is not None
    assert SystemRole.FINANCE.value in fin.roles

    # 动态匹配 HRSSC 运营专员
    ssc = find_specialist_by_role(SystemRole.HR, department_hint="人力资源部", exclude_roles=[SystemRole.HRBP.value])
    assert ssc is not None
    assert SystemRole.HR.value in ssc.roles
    assert SystemRole.HRBP.value not in ssc.roles


def test_create_ticket_auto_assignment():
    test_id = f"TICK-AUTOTEST-{uuid.uuid4().hex[:8]}"
    # Test database creation with auto-assignment
    ticket = create_hr_ticket(
        ticket_id=test_id,
        employee_id=DEFAULT_EMPLOYEE_ID,
        applicant="张明",
        category="转岗调动",
        title="撤销 TRF-144 调动申请",
        description="请 HR 协助终止正在审批流转中的 TRF-144 调动单"
    )
    assert ticket["assigned_to"] == "王芳 (对口 HRBP)"

    fetched_list = query_hr_tickets(employee_id=DEFAULT_EMPLOYEE_ID, ticket_id=test_id)
    assert len(fetched_list) > 0
    assert fetched_list[0]["assigned_to"] == "王芳 (对口 HRBP)"


def test_create_ticket_explicit_assignment():
    test_id = f"TICK-EXPLICIT-{uuid.uuid4().hex[:8]}"
    # Explicitly specified assignee should be preserved
    ticket = create_hr_ticket(
        ticket_id=test_id,
        employee_id=DEFAULT_EMPLOYEE_ID,
        applicant="张明",
        category="综合咨询",
        title="一般咨询",
        description="咨询年休假折算",
        assigned_to="指定专员A"
    )
    assert ticket["assigned_to"] == "指定专员A"


def test_adapter_create_ticket():
    adapter = get_hr_adapter()
    res = adapter.create_ticket(
        employee_id=DEFAULT_EMPLOYEE_ID,
        applicant="张明",
        category="员工关怀与申诉",
        title="撤销转岗申请",
        description="希望联系 HRBP 王芳协助关闭 TRF-144"
    )
    assert res["assigned_to"] == "王芳 (对口 HRBP)"


