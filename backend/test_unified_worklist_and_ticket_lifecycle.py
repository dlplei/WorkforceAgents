import unittest
from fastapi.testclient import TestClient
from main import app
from db import database
from services.hr_adapter import get_hr_adapter
from agent.tools import registry


class TestUnifiedWorklistAndTicketLifecycle(unittest.TestCase):
    """测试统一工作台待办中心 (Unified Inbox) 与 HR 服务工单生命周期流转"""

    def setUp(self):
        self.client = TestClient(app)
        database.init_db()

    def test_zhangming_cancel_ticket_workflow(self):
        """
        完整测试场景：
        1. 张明提报工单：申请撤销已审批内部调动单 TRF-846
        2. 验证工单自动智能路由给王芳 (HRBP)
        3. 王芳打开待办中心 (GET /api/approvals/pending)，成功看到该工单待办
        4. 李伟 (主管) 和陈敏 (财务) 无法看到该工单（基于角色的数据隔离）
        5. 王芳执行办结 (POST /api/approvals/{ticket_id}/action)，验证工单办结且 TRF-846 自动联动作废
        """
        adapter = get_hr_adapter()

        # 先确保存在待撤销的 TRF-846 调动单 (模拟此前已通过的主管/HRBP审批单)
        with database.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO approvals (id, employee_id, applicant, approval_type, status, request_date, start_date, approver, reason)
                    VALUES ('TRF-846', 'E10293', '张明', '转岗调动', 'approved', '2026-04-10', '2026-05-01', '王芳', '转入AI平台组')
                    ON CONFLICT (id) DO UPDATE SET status = 'approved';
                    """
                )
                conn.commit()

        # 1. 张明提报工单
        ticket = database.create_hr_ticket(
            ticket_id="TICK-TEST-9901",
            employee_id="E10293",
            applicant="张明",
            category="转岗调动",
            title="申请撤销已审批内部调动单 TRF-846",
            description="由于原团队重点项目推进需要，经协商申请撤销 TRF-846 调动单，保留在原团队。",
            priority="high",
            external_system_id="TRF-846"
        )
        self.assertEqual(ticket["id"], "TICK-TEST-9901")
        self.assertIn("王芳", ticket.get("assigned_to", ""))

        # 2. 王芳视角查看待办中心 (GET /api/approvals/pending)
        res_hrbp = self.client.get(
            "/api/approvals/pending",
            headers={"X-Employee-Id": "E10456"}  # 王芳
        )
        self.assertEqual(res_hrbp.status_code, 200)
        hrbp_pending = res_hrbp.json()
        ticket_item = next((item for item in hrbp_pending if item["id"] == "TICK-TEST-9901"), None)
        self.assertIsNotNone(ticket_item, "王芳待办列表中必须包含张明提交的撤销工单")
        self.assertEqual(ticket_item["applicant"], "张明")
        self.assertTrue(ticket_item.get("is_ticket", False))
        self.assertIn("TRF-846", ticket_item.get("reason", ""))

        # 3. 数据隔离校验：李伟 (主管) 和陈敏 (财务) 不能看到该工单
        res_mgr = self.client.get(
            "/api/approvals/pending",
            headers={"X-Employee-Id": "E10001"}  # 李伟
        )
        mgr_pending = res_mgr.json()
        self.assertIsNone(next((item for item in mgr_pending if item["id"] == "TICK-TEST-9901"), None))

        res_fin = self.client.get(
            "/api/approvals/pending",
            headers={"X-Employee-Id": "E10501"}  # 陈敏
        )
        fin_pending = res_fin.json()
        self.assertIsNone(next((item for item in fin_pending if item["id"] == "TICK-TEST-9901"), None))

        # 4. 王芳执行办结核准
        action_res = self.client.post(
            "/api/approvals/TICK-TEST-9901/action",
            headers={"X-Employee-Id": "E10456"},
            json={
                "decision": "approved",
                "comment": "已与双方主管沟通确认，核准作废调动单并办结工单。"
            }
        )
        self.assertEqual(action_res.status_code, 200)
        action_data = action_res.json()
        self.assertTrue(action_data["success"])
        self.assertIn("TRF-846", action_data["message"])

        # 5. 校验工单状态已变为 resolved
        tks = database.query_hr_tickets(ticket_id="TICK-TEST-9901")
        self.assertEqual(len(tks), 1)
        self.assertEqual(tks[0]["status"], "resolved")
        self.assertIn("核准作废", tks[0].get("comment", ""))

        # 6. 校验 TRF-846 单据状态已联动更新为 cancelled
        with database.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status, comment FROM approvals WHERE id = 'TRF-846';")
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["status"], "cancelled", "TRF-846 调动单必须已联动标记为 cancelled")
                self.assertIn("TICK-TEST-9901", row["comment"])

    def test_agent_dialogue_ticket_resolution(self):
        """测试王芳通过 Agent 对话工具 review_approval_request 自动匹配张明的待办工单并办结"""
        database.create_hr_ticket(
            ticket_id="TICK-TEST-9902",
            employee_id="E10293",
            applicant="张明",
            category="转岗调动",
            title="申请撤销内部调动工单",
            description="测试对话流匹配",
            priority="medium",
            assigned_to="王芳 (对口 HRBP)"
        )

        database.set_current_employee_id("E10456")  # 王芳
        import asyncio
        res = asyncio.run(
            registry.execute(
                "review_approval_request",
                {
                    "applicant_name": "张明",
                    "comment": "同意撤销工单，办理结案",
                    "decision": "approved"
                }
            )
        )
        self.assertTrue(res.success)
        tks = database.query_hr_tickets(ticket_id="TICK-TEST-9902")
        self.assertEqual(tks[0]["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
