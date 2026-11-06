"""
差旅申请 (submit_travel_request) 与 员工调动 (submit_transfer_request) 全链路业务与 HITL 测试套件
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.tools import registry, build_hitl_action_request
from main import app
from db import database
from services.hr_adapter import get_hr_adapter
from services.cache_service import invalidate_cache_on_write


def test_tool_registration():
    """验证工具已成功注册且为 confirmation 权限级别"""
    travel_tool = registry.get("submit_travel_request")
    assert travel_tool is not None, "submit_travel_request 工具未注册"
    assert travel_tool["permission_level"] == "confirmation", "差旅工具必须为 confirmation 权限级别"
    assert travel_tool["category"] == "action"

    transfer_tool = registry.get("submit_transfer_request")
    assert transfer_tool is not None, "submit_transfer_request 工具未注册"
    assert transfer_tool["permission_level"] == "confirmation", "调动工具必须为 confirmation 权限级别"
    assert transfer_tool["category"] == "action"
    print("✅ 1. 工具注册与权限等级校验通过")


def test_travel_hitl_card_generation():
    """测试差旅申请 HITL 卡片构建"""
    database.set_current_employee_id("E10293")
    travel_args = {
        "destination": "上海",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "purpose": "参加华东区大客户技术研讨与支持",
        "transportation": "高铁一等座",
    }
    hitl_req = build_hitl_action_request("submit_travel_request", travel_args)
    assert hitl_req.category == "travel"
    assert hitl_req.risk_level == "medium"
    assert "上海" in hitl_req.summary["出差目的地"]
    assert "3" in hitl_req.summary["出行周期"] or "共 3 天" in hitl_req.summary["出行周期"]
    assert "李伟" in hitl_req.summary["审批流转"]
    print("✅ 2. 差旅申请 HITL 确认卡片结构验证通过")


def test_transfer_hitl_card_generation():
    """测试员工调动申请 HITL 卡片构建"""
    database.set_current_employee_id("E10293")
    transfer_args = {
        "target_department": "华东研发中心",
        "target_location": "上海",
        "target_position": "高级全栈工程师",
        "effective_date": "2026-12-01",
        "reason": "配合华东业务线研发交付，个人申请驻沪工作",
    }
    hitl_req = build_hitl_action_request("submit_transfer_request", transfer_args)
    assert hitl_req.category == "transfer"
    assert hitl_req.risk_level == "high"
    assert "上海" in hitl_req.summary["拟调往部门"]
    assert "搬迁补贴" in hitl_req.summary["福利与人事须知"]
    assert "王芳" in hitl_req.summary["审批协同流转"]
    print("✅ 3. 员工调动申请 HITL 确认卡片结构验证通过")


def test_travel_and_transfer_hitl_action_execution():
    """测试通过 /api/hitl/action 接口确认执行落库"""
    client = TestClient(app)

    # 1. 执行差旅申请
    travel_payload = {
        "action_id": "hitl_submit_travel_request_test_1001",
        "tool_name": "submit_travel_request",
        "decision": "approve",
        "arguments": {
            "destination": "深圳",
            "start_date": "2026-11-16",
            "end_date": "2026-11-18",
            "purpose": "深圳总装厂现场排期调试",
            "transportation": "航班经济舱",
            "estimated_budget": 2800,
        },
    }
    resp = client.post("/api/hitl/action", json=travel_payload, headers={"X-Employee-Id": "E10293"})
    assert resp.status_code == 200, f"差旅落库失败: {resp.text}"
    travel_data = resp.json()
    assert travel_data["success"] is True
    travel_approval_id = travel_data["data"]["approval_id"]
    assert travel_approval_id.startswith("TRV-")
    print(f"✅ 4.1 差旅申请确认落库成功，单号: {travel_approval_id}")

    # 2. 执行调动申请
    transfer_payload = {
        "action_id": "hitl_submit_transfer_request_test_1002",
        "tool_name": "submit_transfer_request",
        "decision": "approve",
        "arguments": {
            "target_department": "技术研发部",
            "target_location": "上海",
            "target_position": "资深前端专家",
            "effective_date": "2026-12-01",
            "reason": "家庭常驻地变更，申请转岗至上海分部",
        },
    }
    resp2 = client.post("/api/hitl/action", json=transfer_payload, headers={"X-Employee-Id": "E10293"})
    assert resp2.status_code == 200, f"调动落库失败: {resp2.text}"
    transfer_data = resp2.json()
    assert transfer_data["success"] is True
    transfer_approval_id = transfer_data["data"]["approval_id"]
    assert transfer_approval_id.startswith("TRF-")
    print(f"✅ 4.2 调动申请确认落库成功，单号: {transfer_approval_id}")

    # 3. 验证主管视角 (李伟 E10001) 能够在待办审批中看到新提交的差旅与调动单据
    adapter = get_hr_adapter()
    manager_pendings = adapter.get_pending_approvals("李伟")
    pending_ids = [p.get("id") for p in manager_pendings]
    assert travel_approval_id in pending_ids, "主管待办中未能检索到新提交的差旅单"
    assert transfer_approval_id in pending_ids, "主管待办中未能检索到新提交的调动单"
    print(f"✅ 4.3 主管待办审批列表中成功查询到新单据 ({travel_approval_id}, {transfer_approval_id})")

    # 4. 主管李伟批准差旅单
    review_resp = adapter.process_approval(
        approval_id=travel_approval_id,
        approver_name_or_id="李伟",
        decision="approved",
        comment="出差事由充分，准予出差",
    )
    assert review_resp["success"] is True
    assert review_resp["approval"]["status"] == "approved"
    print(f"✅ 4.4 主管成功审批通过差旅单 {travel_approval_id}")


def test_cache_invalidation_on_new_tools():
    """测试差旅与调动写操作的缓存主动淘汰 (Evict-on-Write)"""
    evicted_travel = invalidate_cache_on_write("submit_travel_request", employee_id="E10293")
    assert isinstance(evicted_travel, int)

    evicted_transfer = invalidate_cache_on_write("submit_transfer_request", employee_id="E10293")
    assert isinstance(evicted_transfer, int)
    print("✅ 5. 差旅与调动写操作主动淘汰机制 (Evict-on-Write) 验证通过")


if __name__ == "__main__":
    print("\n========== 开始 差旅与内部调动 全链路业务与 HITL 测试 ==========")
    test_tool_registration()
    test_travel_hitl_card_generation()
    test_transfer_hitl_card_generation()
    test_travel_and_transfer_hitl_action_execution()
    test_cache_invalidation_on_new_tools()
    print("🎉 所有 差旅与调动全案扩展测试 全部顺利通过！\n")
