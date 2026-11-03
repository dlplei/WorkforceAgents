"""
FastAPI 聊天接口与 Redis 缓存联调集成测试
"""
import sys
import unittest
import json
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from main import app
from services.cache_service import clear_cache, set_cached_response, get_cached_response


class TestFastAPICacheIntegration(unittest.TestCase):
    def setUp(self):
        clear_cache()
        self.client = TestClient(app)

    def tearDown(self):
        clear_cache()

    def test_cache_stats_endpoint(self):
        """测试 GET /api/cache/stats"""
        res = self.client.get("/api/cache/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("connected"))
        self.assertEqual(data.get("db"), 1)

    def test_chat_stream_cache_hit(self):
        """测试预置缓存后调用 POST /api/chat 触发秒回"""
        test_question = "公司的年假天数是如何规定的？"
        cached_content = "根据员工司龄：1-10年工龄享5天年假，10-20年享10天年假，20年以上享15天年假。"

        # 写入缓存
        set_cached_response(
            question=test_question,
            content=cached_content,
            model="gemini-3.7-flash",
            tools_used=["get_policy"],
        )

        # 命中查询
        payload = {
            "message": "公司的年假天数是如何规定的",  # 省略标点，测试归一化匹配
            "history": [],
        }

        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-cache"), "HIT")

        # 解析 SSE 事件
        lines = response.text.split("\n")
        events = []
        for line in lines:
            if line.startswith("data: "):
                event_json = line[6:].strip()
                if event_json:
                    events.append(json.loads(event_json))

        # 验证包含 token 事件与 message_complete
        token_contents = [e["content"] for e in events if e.get("type") == "token"]
        reconstructed = "".join(token_contents)
        self.assertEqual(reconstructed, cached_content)

        complete_events = [e for e in events if e.get("type") == "message_complete"]
        self.assertEqual(len(complete_events), 1)
        self.assertTrue(complete_events[0].get("cached"))
        self.assertEqual(complete_events[0].get("content"), cached_content)

    def test_chat_stream_cache_hit_with_conversation_history(self):
        """测试用户在连续多轮会话中重复提问时（带 history），依然准确命中秒回与工具回放"""
        question = "我需要开具一份用于办理签证的在职证明"
        content = "张明您好，已为您提交用于办理签证的在职证明开具申请。"
        tool_call_sample = {
            "id": "call_123",
            "name": "generate_document",
            "arguments": {"doc_type": "在职证明", "purpose": "签证"},
        }
        tool_result_sample = {
            "tool_name": "generate_document",
            "success": True,
            "data": {"document_id": "DOC-99999", "status": "processing"},
        }

        # 写入缓存（包含工具调用信息）
        set_cached_response(
            question=question,
            content=content,
            model="gemini-3.7-flash",
            tools_used=["generate_document"],
            tool_calls=[tool_call_sample],
            tool_results=[tool_result_sample],
        )

        # 连续第二次提问（模拟前端传入的包含前轮对话的 history）
        payload = {
            "message": question,
            "history": [
                {"role": "user", "content": question},
                {"role": "assistant", "content": content},
            ],
        }

        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-cache"), "HIT")

        # 解析事件
        lines = response.text.split("\n")
        events = [json.loads(l[6:]) for l in lines if l.startswith("data: ") and l[6:].strip()]

        # 验证工具调用回放
        tool_calls = [e for e in events if e.get("type") == "tool_call"]
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["data"]["name"], "generate_document")

        # 验证 message_complete 包含 cached 标记
        complete_events = [e for e in events if e.get("type") == "message_complete"]
        self.assertEqual(len(complete_events), 1)
        self.assertTrue(complete_events[0].get("cached"))

    def test_chat_stream_force_refresh_bypasses_cache(self):
        """测试客户端传入 force_refresh: True 时跳过缓存秒回，直通模型执行"""
        question = "请假审批一般需要多长时间？"
        cached_content = "旧的缓存：通常需要1个工作日。"
        set_cached_response(
            question=question,
            content=cached_content,
            model="gemini-3.7-flash",
        )

        # 默认不传 force_refresh -> 应该 HIT
        res_cached = self.client.post("/api/chat", json={"message": question})
        self.assertEqual(res_cached.status_code, 200)
        self.assertEqual(res_cached.headers.get("x-cache"), "HIT")

        # 传入 force_refresh: True -> 应该跳过缓存，直通执行（不带 X-Cache: HIT 头）
        res_forced = self.client.post(
            "/api/chat",
            json={"message": question, "force_refresh": True},
        )
        self.assertEqual(res_forced.status_code, 200)
        self.assertNotEqual(res_forced.headers.get("x-cache"), "HIT")

    def test_cache_clear_endpoint(self):
        """测试 POST /api/cache/clear"""
        set_cached_response("测试问题", "测试回复")
        res_clear = self.client.post("/api/cache/clear")
        self.assertEqual(res_clear.status_code, 200)
        self.assertGreaterEqual(res_clear.json().get("deleted_keys", 0), 1)

        # 验证清空后不再命中
        self.assertIsNone(get_cached_response("测试问题"))

    def test_chat_cross_employee_header_isolation(self):
        """测试通过 X-Employee-Id 请求头在 POST /api/chat 时的多租户隔离"""
        question = "帮我查一下我目前的假期余额"
        content_zhang = "张明您好，您目前剩余年假 7 天。"

        # 为张明 (E10293) 预置专属私有缓存
        set_cached_response(
            question=question,
            content=content_zhang,
            model="gemini-3.7-flash",
            employee_id="E10293",
            tools_used=["query_leave_balance"],
        )

        # 1. 张明请求：必须 HIT
        res_zhang = self.client.post(
            "/api/chat",
            headers={"X-Employee-Id": "E10293"},
            json={"message": question},
        )
        self.assertEqual(res_zhang.status_code, 200)
        self.assertEqual(res_zhang.headers.get("x-cache"), "HIT")
        self.assertIn("张明您好", res_zhang.text)

        # 2. 主管李伟 (E10001) 请求相同问题：绝不能 HIT 张明的缓存！
        # 此时李伟尚未缓存自己的数据，系统安全门禁拦截公共/跨用户命中，直通后端模型 (非 HIT)
        # 为避免实际调用外部 LLM 耗时，我们可以验证缓存服务层查询返回 None
        hit_manager = get_cached_response(question, model="gemini-3.7-flash", employee_id="E10001")
        self.assertIsNone(hit_manager, "主管李伟查询个人假期时，绝不能命中普通员工张明的私有缓存！")


if __name__ == "__main__":
    unittest.main()
