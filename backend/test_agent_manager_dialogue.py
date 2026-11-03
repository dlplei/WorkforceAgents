"""
测试主管对话式自然语言审批工具调度与执行闭环
"""
import asyncio
import unittest
from agent.tools import registry
from db.database import set_current_employee_id, get_employee, MOCK_EMPLOYEES

class TestAgentManagerDialogue(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # 设当前员工为李伟（主管）
        set_current_employee_id("E10001")
        MOCK_EMPLOYEES["E10293"].leave_balance.annual = 7
        try:
            from db.database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE leave_balances SET annual = 7.0 WHERE employee_id = 'E10293';")
                    cur.execute("UPDATE approvals SET status = 'pending' WHERE id = 'APR-001';")
                    conn.commit()
        except Exception:
            pass

    async def test_tool_query_pending_approvals(self):
        """测试主管工具 query_pending_approvals"""
        tool = registry.get("query_pending_approvals")
        self.assertIsNotNone(tool)
        res = await registry.execute("query_pending_approvals", {})
        self.assertTrue(res.success)
        self.assertIn("pending_approvals", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        print("\n[Tool Test] query_pending_approvals 返回待办数量:", res.data["count"])

    async def test_tool_review_approval_by_applicant_name(self):
        """测试主管工具 review_approval_request (通过姓名自动匹配单号并审批扣减)"""
        tool = registry.get("review_approval_request")
        self.assertIsNotNone(tool)

        emp_before = get_employee("E10293")
        bal_before = emp_before.leave_balance.annual

        # 主管说"同意张明的请假" -> Agent 调度 review_approval_request(decision="approved", applicant_name="张明")
        res = await registry.execute(
            "review_approval_request",
            {
                "decision": "approved",
                "applicant_name": "张明",
                "comment": "同意，注意休假期间交接好前端代码分支"
            }
        )
        self.assertTrue(res.success)
        self.assertIn("审批单", res.data.get("message", ""))
        self.assertEqual(res.data["approval"]["status"], "approved")

        emp_after = get_employee("E10293")
        self.assertLess(emp_after.leave_balance.annual, bal_before)
        print(f"[Tool Test] 对话式审批执行成功！申请人年假已扣减: {bal_before} -> {emp_after.leave_balance.annual}")

if __name__ == "__main__":
    unittest.main()
