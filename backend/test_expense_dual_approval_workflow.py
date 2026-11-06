import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from db import database
from services.hr_adapter import get_hr_adapter


def test_exp_977_routing_to_finance():
    """验证 EXP-977 报销申请在主管审批后正确流转至财务复核"""
    database.init_db()
    adapter = get_hr_adapter()

    # 1. 检查数据库中 EXP-977 的流转状态
    with database.get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, applicant, approval_type, status, approver, comment FROM approvals WHERE id = 'EXP-977';")
            row = cur.fetchone()
            assert row is not None, "EXP-977 应当存在于 approvals 表中"
            data = dict(row)
            assert data["status"] == "pending", f"EXP-977 主管初审后应保持 pending 待财务复核，当前为: {data['status']}"
            assert "陈敏" in data["approver"] or "财务" in data["approver"], f"EXP-977 当前待办人应为财务复核，当前为: {data['approver']}"
            assert "直属主管" in data["comment"] and "李伟" in data["comment"], f"EXP-977 批注应包含直属主管李伟初审意见，当前为: {data['comment']}"

    # 2. 李伟（直属主管）查询待审批列表：由于主管已审核完毕，李伟名下不应再积压 EXP-977
    manager_pendings = adapter.get_pending_approvals("李伟")
    manager_pending_ids = [p.get("id") or p.get("approval_id") for p in manager_pendings]
    assert "EXP-977" not in manager_pending_ids, "李伟待审批列表中不应再重复显示已流转给财务复核的 EXP-977"

    # 3. 陈敏（财务专员）查询待审批列表：EXP-977 必须在财务待办池中
    finance_pendings = adapter.get_pending_approvals("陈敏")
    finance_pending_ids = [p.get("id") or p.get("approval_id") for p in finance_pendings]
    assert "EXP-977" in finance_pending_ids, "陈敏待审批列表中必须包含已由主管初审通过、等待财务复核的 EXP-977"

    # 4. 财务专员陈敏执行终审复核（pass）
    review_res = adapter.process_approval(
        approval_id="EXP-977",
        approver_name_or_id="陈敏",
        decision="approved",
        comment="发票明细核验无误，符合差旅报销合规标准，准予报销出纳付款。"
    )
    assert review_res.get("success") is True
    appr = review_res.get("approval", {})
    assert appr.get("status") == "approved", "财务专员终审通过后，EXP-977 状态应更新为 approved 终审办结"
    assert "财务复核" in appr.get("comment", "")
    assert "准予报销" in appr.get("comment", "")

    # 5. 再次查询财务待办：EXP-977 应当从陈敏的待办中消除
    finance_pendings_after = adapter.get_pending_approvals("陈敏")
    finance_pending_ids_after = [p.get("id") or p.get("approval_id") for p in finance_pendings_after]
    assert "EXP-977" not in finance_pending_ids_after, "办结后 EXP-977 应当从陈敏待办列表中移除"


def test_new_expense_claim_dual_approval_lifecycle():
    """验证全新提报的费用报销单 主管初审 -> 流转财务复核 -> 财务终审 的完整生命周期与权限边界"""
    database.init_db()
    adapter = get_hr_adapter()

    # 1. 提交新差旅报销单
    new_exp = adapter.submit_expense_claim(
        employee_id="E10293",
        applicant="张明",
        amount=1580.0,
        category="差旅报销",
        description="杭州客户拜访差旅发票报销",
        invoice_count=2,
        approver="李伟 (直属主管) / 陈敏 (财务复核)"
    )
    exp_id = new_exp["id"]
    assert new_exp["status"] == "pending"

    # 【权限边界校验 1】：在直属主管审批通过之前，财务专员陈敏绝对不应该看到该差旅报销单！
    fin_pendings_before = adapter.get_pending_approvals("陈敏")
    fin_pending_ids_before = [p.get("id") for p in fin_pendings_before]
    assert exp_id not in fin_pending_ids_before, "直属主管审批前，财务陈敏绝不能提前看到该差旅报销单！"

    # 【权限边界校验 2】：财务专员陈敏绝不能看到年假申请、调休申请或转岗申请！
    assert "APR-001" not in fin_pending_ids_before, "年假申请绝不应该流转至财务专员待办中！"
    for p in fin_pendings_before:
        assert p.get("approval_type") not in ("年假", "调休", "转岗调动", "出差"), f"财务待办中出现了非财务类单据: {p}"

    # 2. 直属主管李伟待办列表应查到新单据
    mgr_pendings = adapter.get_pending_approvals("李伟")
    assert exp_id in [p.get("id") for p in mgr_pendings], "新提报单据必须在主管李伟的待办中等待初审"

    # 3. 主管李伟审批通过 -> 触发流转引擎
    step1_res = adapter.process_approval(
        approval_id=exp_id,
        approver_name_or_id="李伟",
        decision="approved",
        comment="出差行程属实，票据金额符合公司差旅报销标准，请财务复核。"
    )
    assert step1_res.get("success") is True
    appr_step1 = step1_res.get("approval", {})
    # 状态必须依然为 pending，且审批人流转为财务陈敏
    assert appr_step1.get("status") == "pending", "主管初审后状态应保持 pending 流转财务"
    assert "陈敏" in appr_step1.get("approver", ""), "审批人字段应流转为陈敏 (财务复核)"
    assert "财务专员【陈敏】复核" in step1_res.get("message", "")

    # 4. 主管待办中已无该单据（因为已交接给下一级）
    mgr_pendings_after = adapter.get_pending_approvals("李伟")
    assert exp_id not in [p.get("id") for p in mgr_pendings_after]

    # 5. 直属主管审批通过后，财务陈敏的待办中此时才能查到该单据！
    fin_pendings_now = adapter.get_pending_approvals("陈敏")
    assert exp_id in [p.get("id") for p in fin_pendings_now], "主管审批通过后，财务陈敏待办中必须出现该单据"
    fin_item = [p for p in fin_pendings_now if p.get("id") == exp_id][0]
    assert "直属主管[李伟]审批通过" in fin_item.get("comment", "")

    # 6. 财务专员陈敏复核终审通过
    step2_res = adapter.process_approval(
        approval_id=exp_id,
        approver_name_or_id="陈敏",
        decision="approved",
        comment="发票真伪及抵扣合规，核准报销款项。"
    )
    assert step2_res.get("success") is True
    appr_step2 = step2_res.get("approval", {})
    assert appr_step2.get("status") == "approved", "财务复核通过后单据终结并置为 approved"
    assert "财务复核通过" in step2_res.get("message", "")
