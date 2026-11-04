"""
业务防重与人事证明、会话消息持久化端到端单元测试
涵盖：
1. chat_messages 会话表持久化与历史查询 (/api/chat/history)
2. documents 证明表持久化与查询 (/api/documents)
3. 在途单据防重拦截 (In-flight Duplicate Prevention)
4. POL-005 政策 30 天冷静期校验 (30-day Cooldown Enforcement)
"""
import asyncio
import os
import sys
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from db.database import (
    create_document,
    query_documents,
    check_duplicate_document,
    save_chat_message,
    get_recent_chat_messages,
    set_current_employee_id,
    get_db_connection,
)
from agent.tools import registry


class TestDuplicateAndChatHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_emp_id = "E10293"
        set_current_employee_id(cls.test_emp_id)

    def setUp(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM documents WHERE id LIKE 'TEST-DOC-%';")
                    cur.execute("DELETE FROM chat_messages WHERE id LIKE 'TEST-MSG-%';")
                    conn.commit()
        except Exception:
            pass

    def tearDown(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM documents WHERE id LIKE 'TEST-DOC-%';")
                    cur.execute("DELETE FROM chat_messages WHERE id LIKE 'TEST-MSG-%';")
                    conn.commit()
        except Exception:
            pass

    def test_01_chat_messages_persistence_and_query(self):
        """测试 1: 会话消息持久化入库与 API 查询"""
        sess_id = f"test-sess-{int(datetime.now().timestamp())}"
        save_chat_message("TEST-MSG-001", sess_id, self.test_emp_id, "user", "开具签证在职证明")
        save_chat_message("TEST-MSG-002", sess_id, self.test_emp_id, "assistant", "草稿已生成")

        history = get_recent_chat_messages(employee_id=self.test_emp_id, session_id=sess_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "开具签证在职证明")

        resp = self.client.get(f"/api/chat/history?session_id={sess_id}", headers={"X-Employee-Id": self.test_emp_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)
        print("✅ 1. chat_messages 会话持久化与 API 测试通过")

    def test_02_document_persistence_and_query(self):
        """测试 2: 人事证明记录持久化与 API 查询"""
        doc = create_document("TEST-DOC-001", self.test_emp_id, "张明", "在职证明", "法国签证")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["status"], "processing")

        resp = self.client.get("/api/documents", headers={"X-Employee-Id": self.test_emp_id})
        self.assertEqual(resp.status_code, 200)
        doc_ids = [d["id"] for d in resp.json()["documents"]]
        self.assertIn("TEST-DOC-001", doc_ids)
        print("✅ 2. documents 证明落库与 API 查询测试通过")

    def test_03_in_flight_duplicate_prevention(self):
        """测试 3: 连续重复申请在职证明触发【在途单据防重拦截】"""
        create_document("TEST-DOC-INFLIGHT", self.test_emp_id, "张明", "在职证明", "办理申根签证", status="processing")

        dup_check = check_duplicate_document(self.test_emp_id, "在职证明", "办理签证")
        self.assertIsNotNone(dup_check)
        self.assertTrue(dup_check["is_duplicate"])
        self.assertEqual(dup_check["type"], "in_flight")
        self.assertIn("TEST-DOC-INFLIGHT", dup_check["message"])

        res = asyncio.run(registry.execute("generate_document", {"doc_type": "在职证明", "purpose": "申根签证"}))
        self.assertFalse(res.success)
        self.assertIn("仍在处理中", res.error)
        print("✅ 3. 在途单据防重拦截测试通过")

    def test_04_cooldown_policy_enforcement(self):
        """测试 4: 违反 POL-005 30天冷静期限制触发拦截"""
        ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        create_document("TEST-DOC-CD", self.test_emp_id, "张明", "在职证明", "买房房贷公证", status="completed", created_at=ten_days_ago)

        dup_check = check_duplicate_document(self.test_emp_id, "在职证明", "申请房贷")
        self.assertIsNotNone(dup_check)
        self.assertEqual(dup_check["type"], "cooldown_violation")
        self.assertIn("POL-005", dup_check["message"])

        dup_diff = check_duplicate_document(self.test_emp_id, "在职证明", "国际学校入学")
        self.assertIsNone(dup_diff)
        print("✅ 4. POL-005 政策 30 天冷静期防重校验测试通过")


if __name__ == "__main__":
    unittest.main()
