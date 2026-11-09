"""
主管审批闭环与多身份感知自动化单元测试
"""
import unittest
from fastapi.testclient import TestClient
from main import app
from db.database import MOCK_EMPLOYEES, get_employee

class TestManagerApproval(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # 确保基础数据状态与幂等性
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

    def test_list_all_employees(self):
        """测试获取全员列表 (Persona Switcher)"""
        res = self.client.get("/api/employees")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 3)
        ids = [e["id"] for e in data]
        self.assertIn("E10293", ids)
        self.assertIn("E10001", ids)
        self.assertIn("E10456", ids)

    def test_persona_switch_header(self):
        """测试 X-Employee-Id 动态切换上下文"""
        # 1. 默认身份应为张明
        res_default = self.client.get("/api/employee")
        self.assertEqual(res_default.status_code, 200)
        self.assertEqual(res_default.json()["name"], "张明")

        # 2. 传递 X-Employee-Id: E10001 应为李伟
        res_manager = self.client.get("/api/employee", headers={"X-Employee-Id": "E10001"})
        self.assertEqual(res_manager.status_code, 200)
        self.assertEqual(res_manager.json()["name"], "李伟")
        self.assertEqual(res_manager.json()["level"], "M1")

    def test_manager_pending_approvals_and_action(self):
        """测试主管查看待办单据，并一键批准通过，校验余额原子扣减副作用"""
        # 1. 主管查看待审批
        res = self.client.get("/api/approvals/pending", headers={"X-Employee-Id": "E10001"})
        self.assertEqual(res.status_code, 200)
        pending = res.json()
        self.assertIsInstance(pending, list)
        self.assertGreaterEqual(len(pending), 1)
        target = next((p for p in pending if p.get("id") == "APR-001"), pending[0])
        app_id = target["id"]

        # 记录张明当前的年假余额
        emp_before = get_employee("E10293")
        annual_before = emp_before.leave_balance.annual

        # 2. 主管执行审批通过
        action_payload = {
            "decision": "approved",
            "comment": "经评估项目进度无风险，同意休假。"
        }
        res_action = self.client.post(
            f"/api/approvals/{app_id}/action",
            headers={"X-Employee-Id": "E10001"},
            json=action_payload
        )
        self.assertEqual(res_action.status_code, 200)
        act_data = res_action.json()
        self.assertTrue(act_data["success"])
        self.assertEqual(act_data["approval"]["status"], "approved")

        # 3. 校验申请人张明的年假余额是否已自动扣减
        emp_after = get_employee("E10293")
        self.assertLess(emp_after.leave_balance.annual, annual_before)
        print(f"\n[Test Pass] 审批通过前后年假扣减: {annual_before} 天 -> {emp_after.leave_balance.annual} 天")

    def test_manager_cross_role_lookup_apr001(self):
        """测试主管李伟直接通过单号 APR-001 跨角色查询下属单据（彻底解决历史报空 Bug）"""
        res = self.client.get(
            "/api/approvals?request_id=APR-001",
            headers={"X-Employee-Id": "E10001"}
        )
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertTrue(len(items) >= 1)
        self.assertEqual(items[0]["id"], "APR-001")
        self.assertEqual(items[0]["applicant"], "张明")
        self.assertEqual(items[0]["approver"], "李伟")

    def test_query_approvals_multi_dimensions(self):
        """测试多维条件组合检索（免单号、按申请人、按状态与起止日期复合查询）"""
        # 1. 主管按申请人姓名免单号查询
        res_by_name = self.client.get(
            "/api/approvals?applicant_name=张明",
            headers={"X-Employee-Id": "E10001"}
        )
        self.assertEqual(res_by_name.status_code, 200)
        items = res_by_name.json()
        self.assertGreaterEqual(len(items), 1)
        for item in items:
            self.assertEqual(item["applicant"], "张明")

        # 2. 按日期区间过滤
        res_by_date = self.client.get(
            "/api/approvals?start_date=2026-01-01&end_date=2026-05-31",
            headers={"X-Employee-Id": "E10001"}
        )
        self.assertEqual(res_by_date.status_code, 200)
        items_date = res_by_date.json()
        self.assertIsInstance(items_date, list)
        self.assertGreaterEqual(len(items_date), 1)

    def test_approval_history_endpoint(self):
        """测试审批中心历史流水归档接口 (/api/approvals/history)"""
        # 1. 测试主管视角 (李伟)
        res = self.client.get(
            "/api/approvals/history",
            headers={"X-Employee-Id": "E10001"}
        )
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        for h in history:
            self.assertIn(h.get("status"), ("approved", "rejected", "已批准", "已驳回"))
            self.assertIsNotNone(h.get("comment"))

        # 2. 测试财务视角 (陈敏)，必须能查到财务复核通过/驳回的报销单历史，绝不能混入仅李伟审批/驳回的单据
        res_finance = self.client.get(
            "/api/approvals/history",
            headers={"X-Employee-Id": "E10501"}
        )
        self.assertEqual(res_finance.status_code, 200)
        finance_history = res_finance.json()
        self.assertIsInstance(finance_history, list)
        self.assertGreaterEqual(len(finance_history), 1)
        # 验证财务历史全部为终态，且全部为陈敏/财务复核经办或陈敏本人单据
        for fh in finance_history:
            self.assertIn(fh.get("status"), ("approved", "rejected", "已批准", "已驳回"))
            self.assertNotIn(fh.get("id"), ("APR-569", "EXP-499", "EXP-750", "EXP-118", "EXP-433"))
            is_chenmin_related = (
                fh.get("employee_id") == "E10501"
                or "陈敏" in str(fh.get("approver", ""))
                or "财务" in str(fh.get("approver", ""))
                or "陈敏" in str(fh.get("comment", ""))
                or "财务" in str(fh.get("comment", ""))
            )
            self.assertTrue(is_chenmin_related, f"陈敏审批历史中混入了未经财务复核的单据: {fh}")

        # 3. 测试 HRBP 视角 (王芳)，只展示经王芳办理或王芳本人单据，不得混入李伟或陈敏独立审批的单据
        res_hr = self.client.get(
            "/api/approvals/history",
            headers={"X-Employee-Id": "E10456"}
        )
        self.assertEqual(res_hr.status_code, 200)
        hr_history = res_hr.json()
        self.assertIsInstance(hr_history, list)
        self.assertGreaterEqual(len(hr_history), 1)
        for hh in hr_history:
            self.assertIn(hh.get("status"), ("approved", "rejected", "已批准", "已驳回"))
            # 必须为王芳本人提交，或经由王芳/HRBP办理
            is_wangfang_related = (
                hh.get("employee_id") == "E10456"
                or "王芳" in str(hh.get("approver", ""))
                or "HRBP" in str(hh.get("approver", ""))
                or "王芳" in str(hh.get("comment", ""))
                or "HRBP" in str(hh.get("comment", ""))
            )
            self.assertTrue(is_wangfang_related, f"王芳审批历史中混入了无关单据: {hh}")
            # 明确排除陈敏复核的纯财务报销单及李伟单独审批的休假单
            self.assertNotIn(hh.get("id"), ("EXP-279", "EXP-159", "APR-002", "APR-101"))

    def test_agent_tool_query_approval_status_without_id(self):
        """测试 Agent 工具层 handle_query_approval_status 在无单号输入时的智能推断检索"""
        import asyncio
        from agent.tools import handle_query_approval_status

        # 模拟李伟主管无单号查询“本月”审批
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(
                handle_query_approval_status({"time_range": "this_month", "status": "all"})
            )
            self.assertTrue(res["success"])
            self.assertIn("approvals", res["data"])
            self.assertIn("total", res["data"])
        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main()
