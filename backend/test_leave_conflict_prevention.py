"""
休假重叠冲突检测与审批排他锁自动化测试
验证：
1. check_duplicate_leave 日期重合算法与单据冲突识别
2. 提交休假申请（submit_leave_request）的前置排他阻断（已生效单据冲突 & 在途pending冲突）
3. 主管审批休假（review_approval_request / process_approval）的排他互斥锁与幂等性保护
"""
import unittest
import asyncio
from db.database import (
    MOCK_EMPLOYEES,
    get_employee,
    check_duplicate_leave,
    create_approval,
    update_approval_status,
    set_current_employee_id,
    get_db_connection
)
from services.hr_adapter import get_hr_adapter
from agent.tools import registry

class TestLeaveConflictPrevention(unittest.TestCase):
    def setUp(self):
        set_current_employee_id("E10293")
        # 恢复张明的基础假期余额
        MOCK_EMPLOYEES["E10293"].leave_balance.annual = 3.0
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE leave_balances SET annual = 3.0 WHERE employee_id = 'E10293';")
                    cur.execute("DELETE FROM approvals WHERE id LIKE 'TEST-LEAVE-%';")
                    conn.commit()
        except Exception:
            pass

    def tearDown(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM approvals WHERE id LIKE 'TEST-LEAVE-%';")
                    conn.commit()
        except Exception:
            pass

    def test_01_check_duplicate_leave_detection(self):
        """测试日期重叠区间判定算法"""
        conflict = check_duplicate_leave("E10293", "2026-11-02", "2026-11-03")
        self.assertIsNotNone(conflict)
        self.assertTrue(conflict["is_duplicate"])
        self.assertEqual(conflict["type"], "already_approved")
        self.assertIn("APR-464", conflict["message"])

        # 部分重叠与边界
        self.assertIsNotNone(check_duplicate_leave("E10293", "2026-11-01", "2026-11-02"))
        self.assertIsNotNone(check_duplicate_leave("E10293", "2026-11-03", "2026-11-05"))
        self.assertIsNotNone(check_duplicate_leave("E10293", "2026-11-01", "2026-11-04"))

        # 无重叠与非法区间
        self.assertIsNone(check_duplicate_leave("E10293", "2026-11-10", "2026-11-12"))
        inv = check_duplicate_leave("E10293", "2026-11-15", "2026-11-10")
        self.assertIsNotNone(inv)
        self.assertEqual(inv["type"], "invalid_date_range")
        print("\n✅ 1. check_duplicate_leave 日期重合区间与合法性校验测试通过")

    def test_02_submit_leave_blocked_by_existing_approved(self):
        """测试提报与已批准单据时间冲突时被拒绝"""
        adapter = get_hr_adapter()
        with self.assertRaises(ValueError) as ctx:
            adapter.submit_leave_request(
                employee_id="E10293",
                applicant="张明",
                leave_type="annual",
                start_date="2026-11-02",
                end_date="2026-11-03",
                reason="尝试重复提报年假",
                approver="李伟"
            )
    def test_03_submit_leave_blocked_by_inflight_pending(self):
        """测试提报与在途 pending 单据冲突时被拒绝"""
        adapter = get_hr_adapter()
        t_id = "TEST-LEAVE-PENDING"
        create_approval(
            approval_id=t_id,
            employee_id="E10293",
            applicant="张明",
            approval_type="annual",
            status="pending",
            request_date="2026-11-05",
            start_date="2026-12-10",
            end_date="2026-12-12",
            reason="测试待办单据",
            approver="李伟"
        )
        with self.assertRaises(ValueError) as ctx:
            adapter.submit_leave_request(
                employee_id="E10293",
                applicant="张明",
                leave_type="annual",
                start_date="2026-12-11",
                end_date="2026-12-15",
                reason="重叠提报",
                approver="李伟"
            )
        self.assertIn("正在审批中的休假申请", str(ctx.exception))
        print("✅ 3. 提交休假单据前置拦截在途 pending 冲突测试通过")

    def test_04_approval_mutual_exclusion_safeguard(self):
        """测试主管审批决策二次互斥锁：已存在生效休假时，禁止重复审批通过并扣假"""
        t_id = "TEST-LEAVE-DUPLICATE"
        create_approval(
            approval_id=t_id,
            employee_id="E10293",
            applicant="张明",
            approval_type="annual",
            status="pending",
            request_date="2026-11-01",
            start_date="2026-11-02",
            end_date="2026-11-03",
            reason="历史遗留冲突申请",
            approver="李伟"
        )
        bal_before = get_employee("E10293").leave_balance.annual
        res = update_approval_status(
            approval_id=t_id,
            approver_name_or_id="李伟",
            decision="approved",
            comment="测试批准冲突单"
        )
        self.assertFalse(res["success"])
        self.assertIn("审批防重拦截", res["message"])
        self.assertIn("已有已批准生效的休假", res["message"])
        bal_after = get_employee("E10293").leave_balance.annual
        self.assertEqual(bal_after, bal_before)
        print("✅ 4. 主管审批二次互斥锁成功拦截冲突并保护余额不被扣减测试通过")

    def test_05_approval_idempotency_protection(self):
        """测试对同一单据重复点击批准时的幂等性防护（不重复扣除余额）"""
        t_id = "TEST-LEAVE-IDEMPOTENT"
        create_approval(
            approval_id=t_id,
            employee_id="E10293",
            applicant="张明",
            approval_type="annual",
            status="pending",
            request_date="2026-11-05",
            start_date="2026-12-24",
            end_date="2026-12-24",
            reason="圣诞假期平安夜",
            approver="李伟"
        )
        bal_start = get_employee("E10293").leave_balance.annual
        res1 = update_approval_status(
            approval_id=t_id,
            approver_name_or_id="李伟",
            decision="approved",
            comment="同意平安夜休假"
        )
        self.assertTrue(res1["success"])
        bal_after_first = get_employee("E10293").leave_balance.annual
        self.assertEqual(bal_after_first, bal_start - 1.0)

        # 重复审批同一单据
        res2 = update_approval_status(
            approval_id=t_id,
            approver_name_or_id="李伟",
            decision="approved",
            comment="重复同意"
        )
        self.assertTrue(res2["success"])
        self.assertIn("已处于【已通过】状态，无需重复审批与扣减假期", res2["message"])
        bal_after_second = get_employee("E10293").leave_balance.annual
        self.assertEqual(bal_after_second, bal_after_first)
        print("✅ 5. 审批状态幂等性保护测试通过，无重复扣假副作用")


class TestLeaveToolsAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        set_current_employee_id("E10293")

    async def test_tool_submit_leave_conflict(self):
        """测试 Agent 工具 handle_submit_leave_request 拦截"""
        res = await registry.execute(
            "submit_leave_request",
            {
                "leave_type": "annual",
                "start_date": "2026-11-02",
                "end_date": "2026-11-03",
                "reason": "请假旅游"
            }
        )
        self.assertFalse(res.success)
        self.assertIn("系统禁止在同一时段重复申请休假", res.error)
        print("✅ 6. Agent 工具层 submit_leave_request 前置冲突阻断测试通过")

    def test_query_approvals_bilingual_type_normalization(self):
        """测试多维审批查询中中英文单据类型的智能归一化与别名检索兼容性"""
        from db.database import query_approvals
        # 1. 泛称“请假”检索，应同时匹配存为中文'年假申请'和英文'annual'的记录
        res_leave = query_approvals(employee_id="E10293", approval_type="请假")
        types_leave = {r.get("approval_type") for r in res_leave}
        self.assertIn("年假申请", types_leave)
        self.assertIn("annual", types_leave)

        # 2. “年假”与“annual”等效双向匹配
        res_cn = query_approvals(employee_id="E10293", approval_type="年假")
        res_en = query_approvals(employee_id="E10293", approval_type="annual")
        self.assertEqual(len(res_cn), len(res_en))
        print(f"✅ 7. 中英文请假单据类型多维归一化测试通过 (命中 {len(res_cn)} 条记录)")



if __name__ == "__main__":
    unittest.main()

