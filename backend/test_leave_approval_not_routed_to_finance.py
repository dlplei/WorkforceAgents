import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from db import database
from services.hr_adapter import get_hr_adapter


def test_apr569_state_and_balance_consistency():
    """验证 APR-569 数据修复与状态一致性：主管赵静已办结，不挂在陈敏待办，年假额度正确扣除"""
    database.init_db()
    adapter = get_hr_adapter()

    # 1. 验证 APR-569 在数据库中的状态
    conn = database.get_db_connection()
    assert conn is not None
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM approvals WHERE id = 'APR-569';")
        apr = cur.fetchone()
        assert apr is not None
        assert apr["status"] == "approved", f"APR-569 状态应为 approved，实际为 {apr['status']}"
        assert apr["approver"] == "赵静", f"APR-569 审批人应为主管赵静，实际为 {apr['approver']}"
        assert "陈敏" not in apr["approver"], "APR-569 审批人不应包含财务陈敏"
        assert "赵静" in apr["comment"] and "通过" in apr["comment"]

        # 验证王芳年假余额已扣除 1 天 (初始 12 - 1 = 11)
        cur.execute("SELECT annual FROM leave_balances WHERE employee_id = 'E10456';")
        lb = cur.fetchone()
        assert float(lb["annual"]) == 11.0, f"王芳年假余额应为 11.0 天，实际为 {lb['annual']}"
    conn.close()

    # 2. 验证财务陈敏待办列表中绝不包含 APR-569
    finance_pendings = adapter.get_pending_approvals("陈敏")
    finance_pending_ids = [p.get("id") or p.get("approval_id") for p in finance_pendings]
    assert "APR-569" not in finance_pending_ids, "财务专员陈敏的待审批列表中绝对不应包含请假单 APR-569"

    # 3. 验证王芳待办列表 (作为HRBP) 绝不包含 APR-569
    hrbp_pendings = adapter.get_pending_approvals("王芳")
    hrbp_pending_ids = [p.get("id") or p.get("approval_id") for p in hrbp_pendings]
    assert "APR-569" not in hrbp_pending_ids, "王芳待办列表中绝对不应包含已办结的年假单 APR-569"


def test_leave_approval_workflow_bypasses_finance():
    """验证请假单完整生命周期：提报时仅流转主管，主管审批通过后立即置为 approved 办结并扣减年假，绝不流转给财务"""
    database.init_db()
    adapter = get_hr_adapter()

    # 1. 员工提报年假
    test_leave = adapter.submit_leave_request(
        employee_id="E10293",
        applicant="张明",
        leave_type="annual",
        start_date="2026-12-01",
        end_date="2026-12-01",
        reason="测试年假单直属主管办结逻辑",
        approver="李伟"
    )
    leave_id = test_leave["id"]

    try:
        # 初始状态为 pending，审批人为主管李伟
        assert test_leave["status"] == "pending"
        assert "陈敏" not in test_leave.get("approver", "")

        # 2. 主管李伟查询待审批列表：包含该请假单
        mgr_pendings = adapter.get_pending_approvals("李伟")
        mgr_ids = [p.get("id") or p.get("approval_id") for p in mgr_pendings]
        assert leave_id in mgr_ids

        # 3. 财务陈敏查询待审批列表：绝不包含该请假单
        fin_pendings = adapter.get_pending_approvals("陈敏")
        fin_ids = [p.get("id") or p.get("approval_id") for p in fin_pendings]
        assert leave_id not in fin_ids

        # 4. 主管李伟审批通过该请假单
        review_res = database.update_approval_status(
            approval_id=leave_id,
            approver_name_or_id="李伟",
            decision="approved",
            comment="项目进度可控，同意休假"
        )
        assert review_res.get("success") is True
        updated_appr = review_res.get("approval", {})

        # 5. 校验状态：必须直接变更为 approved（终态），绝对不能是 pending 流转财务！
        assert updated_appr.get("status") == "approved", f"请假单主管审批后应为 approved，实际为 {updated_appr.get('status')}"
        assert updated_appr.get("approver") == "李伟", f"审批人应为主管李伟，实际为 {updated_appr.get('approver')}"
        assert "陈敏" not in updated_appr.get("approver", ""), "请假单审批人绝不能流转给财务陈敏"
        assert "流转至财务" not in updated_appr.get("comment", "")

        # 6. 再次验证财务陈敏待办：依然没有该单据
        fin_pendings_after = adapter.get_pending_approvals("陈敏")
        fin_ids_after = [p.get("id") or p.get("approval_id") for p in fin_pendings_after]
        assert leave_id not in fin_ids_after

    finally:
        # 清理测试数据
        with database.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM approvals WHERE id = %s;", (leave_id,))
                cur.execute("DELETE FROM calendar_events WHERE employee_id = 'E10293' AND event_date = '2026-12-01';")
                conn.commit()
