"""
test_phase2_complete_workflow.py
验证 Phase 2 全业务工作流：
1. submit_expense_claim（差旅与日常报销提报、HITL 门禁卡片、主管待办集成、缓存失效）
2. query_org_chart（员工向上汇报链、主管直接下属、同组团队成员、对口 HRBP）
3. 差旅与内部调动全链路回归验证
"""

import sys
import asyncio
from pathlib import Path

# 将工程根目录与 backend 目录加入 sys.path
backend_dir = Path(__file__).parent.resolve()
root_dir = backend_dir.parent.resolve()
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

import pytest
from backend.db import database
from backend.agent.tools import (
    build_hitl_action_request,
    handle_submit_expense_claim,
    handle_query_org_chart,
    handle_submit_travel_request,
    handle_submit_transfer_request,
)
from backend.services.cache_service import invalidate_cache_on_write


def test_submit_expense_claim_validation_and_hitl():
    """测试报销申请的参数验证及 HITL 门禁卡片构建"""
    database.set_current_employee_id("E10293")

    err_res = asyncio.run(handle_submit_expense_claim({"amount": 0, "description": "无金额申请"}))
    assert err_res.get("success") is False

    err_res2 = asyncio.run(handle_submit_expense_claim({"amount": -50, "description": "负数金额申请"}))
    assert err_res2.get("success") is False

    raw_args = {
        "amount": 1680.50,
        "category": "差旅报销",
        "description": "上海客户技术架构攻坚差旅报销（往返高铁+2晚住宿）",
        "invoice_count": 3,
        "travel_request_id": "TRV-888"
    }
    hitl_req = build_hitl_action_request("submit_expense_claim", raw_args)
    assert hitl_req.category == "expense"
    assert hitl_req.status == "pending"
    assert "¥1680.50" in hitl_req.summary["报销总金额"]
    assert "3 张" in hitl_req.summary["发票凭据"]
    assert "TRV-888" in hitl_req.summary["关联出差审批"]
    assert "李伟" in hitl_req.summary["流转审批人"]


def test_submit_expense_claim_execution_and_approvals():
    """测试报销申请落库及主管审批流转"""
    database.set_current_employee_id("E10293")

    result = asyncio.run(handle_submit_expense_claim({
        "amount": 1250.00,
        "category": "差旅报销",
        "description": "上海峰会出差住宿及餐补",
        "invoice_count": 2,
        "travel_request_id": "TRV-999"
    }))

    assert result.get("success") is True
    data = result["data"]
    assert data["status"] == "submitted"
    approval_id = data["approval_id"]
    assert approval_id.startswith("EXP-")
    assert data["applicant"] == "张明"
    assert data["approver"] == "李伟"

    pending_list = database.query_pending_approvals_for_manager("李伟")
    exp_approvals = [a for a in pending_list if a.get("id") == approval_id or a.get("approval_id") == approval_id]
    assert len(exp_approvals) >= 1
    exp_app = exp_approvals[0]
    assert "¥1250.00" in exp_app.get("reason", "")
    assert exp_app.get("applicant") == "张明"

    invalidated_count = invalidate_cache_on_write("submit_expense_claim", employee_id="E10293")
    assert isinstance(invalidated_count, int)


def test_query_org_chart_reporting_line():
    """测试员工向上汇报链查询 (张明 -> 李伟 -> 赵静)"""
    database.set_current_employee_id("E10293")

    res = asyncio.run(handle_query_org_chart({"employee_name_or_id": "张明", "query_type": "reporting_line"}))
    assert res.get("success") is True
    chart = res["data"]
    assert chart["target_employee"]["name"] == "张明"
    assert chart["target_employee"]["department"] == "技术研发部"

    rep_line = chart["reporting_line"]
    assert len(rep_line) >= 3, "张明的向上汇报链应至少包含: 张明本人 -> 李伟 -> 赵静"
    assert rep_line[0]["name"] == "张明" and rep_line[0]["relation"] == "本人"
    assert rep_line[1]["name"] == "李伟" and rep_line[1]["relation"] == "直属主管"
    assert rep_line[2]["name"] == "赵静" and "主管" in rep_line[2]["relation"]


def test_query_org_chart_direct_reports_and_hrbp():
    """测试主管下属查询及对口 HRBP 解析"""
    res = asyncio.run(handle_query_org_chart({"employee_name_or_id": "李伟", "query_type": "team_members"}))
    assert res.get("success") is True
    chart = res["data"]
    direct_report_names = [d["name"] for d in chart["direct_reports"]]
    assert "张明" in direct_report_names, "张明应在李伟的直属下属列表中"
    assert "钱浩" in direct_report_names, "钱浩应在李伟的直属下属列表中"

    hrbp = chart["hrbp"]
    assert hrbp is not None
    assert hrbp["name"] == "王芳"
    assert "HRBP" in hrbp["position"]

    summary = chart["summary"]
    assert "李伟" in summary
    assert "技术研发部" in summary
    assert "王芳" in summary


def test_full_regression_travel_transfer():
    """验证出差与调动流程无回归缺陷"""
    database.set_current_employee_id("E10293")

    trv = asyncio.run(handle_submit_travel_request({
        "destination": "上海",
        "start_date": "2026-07-01",
        "end_date": "2026-07-03",
        "purpose": "华东大客户支持",
        "estimated_budget": 1600.0,
    }))
    assert trv["success"] is True
    assert trv["data"]["city_tier"] == "一线"

    trf = asyncio.run(handle_submit_transfer_request({
        "target_department": "技术研发部 (上海)",
        "target_location": "上海",
        "target_position": "资深前端开发专家",
        "effective_date": "2026-08-01",
        "reason": "业务拓展与个人常驻",
    }))
    assert trf["success"] is True
    assert trf["data"]["is_cross_city"] is True


