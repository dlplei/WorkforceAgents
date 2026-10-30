"""
原生 HITL (Human-in-the-Loop) 交互卡片工作流端到端回归测试
"""
import asyncio
import os
import sys

# 注入 backend 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.tools import registry, build_hitl_action_request
from agent.engine import AgentEngine
from main import app
from fastapi.testclient import TestClient


def test_build_hitl_action_request():
    """测试不同业务工具的结构化 HITL 载荷构建"""
    # 1. 休假申请
    leave_args = {
        "leave_type": "annual",
        "start_date": "2026-10-08",
        "end_date": "2026-10-10",
        "reason": "国庆长假探亲与个人休整",
    }
    req = build_hitl_action_request("submit_leave_request", leave_args)
    assert req.action_id.startswith("hitl_submit_leave_request_")
    assert req.category == "leave"
    assert req.risk_level == "medium"
    assert "年假" in req.summary["假期类型"]
    assert "2026-10-08 至 2026-10-10" in req.summary["请假周期"]
    print("✅ 1. 休假申请 HITL 载荷构建测试通过")

    # 2. 证明开具
    doc_args = {
        "doc_type": "employment_proof",
        "purpose": "申请申根旅游签证",
        "language": "zh",
    }
    doc_req = build_hitl_action_request("generate_document", doc_args)
    assert doc_req.category == "document"
    assert "在职证明" in doc_req.summary["证明类别"]
    assert "电子公章" in doc_req.summary["印章效力"]
    print("✅ 2. 证明开具 HITL 载荷构建测试通过")

    # 3. HR 工单
    ticket_args = {
        "category": "社保公积金",
        "title": "跨省社保转移转移单办理咨询",
        "priority": "high",
        "description": "请协助开具社保参保凭证并提供转移接收函",
    }
    ticket_req = build_hitl_action_request("create_hr_ticket", ticket_args)
    assert ticket_req.category == "ticket"
    assert ticket_req.summary["工单业务分类"] == "社保公积金"
    print("✅ 3. 工单提报 HITL 载荷构建测试通过")


def test_hitl_action_api():
    """测试 FastAPI /api/hitl/action 接口的审批决策执行"""
    client = TestClient(app)

    # 1. 测试拒绝取消
    reject_payload = {
        "action_id": "hitl_mock_001",
        "tool_name": "submit_leave_request",
        "decision": "reject",
        "arguments": {"leave_type": "annual", "start_date": "2026-10-08", "end_date": "2026-10-09"},
    }
    resp = client.post("/api/hitl/action", json=reject_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["success"] is True
    print("✅ 4. /api/hitl/action 拒绝取消操作验证通过")

    # 2. 测试批准执行入库
    approve_payload = {
        "action_id": "hitl_mock_002",
        "tool_name": "submit_leave_request",
        "decision": "approve",
        "arguments": {
            "leave_type": "annual",
            "start_date": "2026-11-02",
            "end_date": "2026-11-03",
            "reason": "个人年假单测",
        },
    }
    resp2 = client.post("/api/hitl/action", json=approve_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "approved"
    assert data2["success"] is True
    assert "request_id" in data2["data"]
    print(f"✅ 5. /api/hitl/action 批准执行成功，写入单号: {data2['data']['request_id']}")


if __name__ == "__main__":
    print("\n========== 开始 原生 HITL 工作流回归测试 ==========")
    test_build_hitl_action_request()
    test_hitl_action_api()
    print("🎉 所有 原生 HITL 工作流与门禁测试 全部通过！\n")
