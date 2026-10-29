"""
Redis 缓存与秒回机制单元测试
验证复用 chatbi-automotive_redis_1 容器、DB 1 隔离与毫秒级秒回特性
"""
import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.cache_service import (
    init_cache,
    get_redis_client,
    get_cached_response,
    set_cached_response,
    get_cache_stats,
    clear_cache,
    normalize_question,
    generate_cache_key,
    calculate_ttl,
    invalidate_cache_on_write,
    TTL_POLICY_DOCS,
    TTL_DOCUMENT_GEN,
    TTL_DYNAMIC_QUERY,
)
from config import get_redis_config


class TestRedisCache(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def tearDown(self):
        clear_cache()

    def test_01_redis_connection_and_db_isolation(self):
        """测试 Redis 连接及 DB 隔离"""
        cfg = get_redis_config()
        self.assertEqual(cfg.db, 1, "应使用 db 1 与 chatbi-automotive (db 0) 隔离")

        client = get_redis_client()
        self.assertIsNotNone(client, "应成功连接 Redis 容器")
        self.assertTrue(client.ping(), "Redis ping 应返回 True")

    def test_02_normalize_question(self):
        """测试用户问题归一化（去除末尾中英文问号、空白）"""
        q1 = "年假政策是怎样的？"
        q2 = "  年假政策是怎样的?  "
        q3 = "年假政策是怎样的"
        norm1 = normalize_question(q1)
        norm2 = normalize_question(q2)
        norm3 = normalize_question(q3)
        self.assertEqual(norm1, norm2)
        self.assertEqual(norm1, norm3)
        self.assertEqual(norm1, "年假政策是怎样的")

    def test_03_cache_set_and_hit(self):
        """测试设置缓存与精确秒回读取"""
        model = "gemini-3.7-flash"
        question = "病假需要提供什么材料？"
        answer = "病假需在OA系统提交二级以上公立医院开具的就诊记录或病假证明。"

        # 首次查询应未命中
        miss = get_cached_response(question, model)
        self.assertIsNone(miss)

        # 写入缓存
        ok = set_cached_response(
            question=question,
            content=answer,
            model=model,
            tools_used=["search_policy"],
            ttl=3600,
        )
        self.assertTrue(ok)

        # 再次查询（带问号与不带问号）均应命中
        hit1 = get_cached_response(question, model)
        self.assertIsNotNone(hit1)
        self.assertEqual(hit1["content"], answer)
        self.assertEqual(hit1["tools_used"], ["search_policy"])

        hit2 = get_cached_response("病假需要提供什么材料", model)
        self.assertIsNotNone(hit2)
        self.assertEqual(hit2["content"], answer)

    def test_04_cache_stats_and_metrics(self):
        """测试缓存统计信息"""
        stats = get_cache_stats()
        self.assertTrue(stats.get("connected"))
        self.assertEqual(stats.get("db"), 1)
        self.assertIn("keys_count", stats)
        self.assertIn("ttl_tiers", stats)

    def test_05_dynamic_ttl_tiered_policy(self):
        """测试基于工具调用的动态 TTL 分级计算"""
        # 个人动态数据（如假期余额查询）-> 600s
        ttl_dynamic = calculate_ttl(["query_leave_balance"])
        self.assertEqual(ttl_dynamic, TTL_DYNAMIC_QUERY)
        self.assertEqual(ttl_dynamic, 600)

        # 证明开具类工具 -> 3600s
        ttl_doc = calculate_ttl(["generate_document"])
        self.assertEqual(ttl_doc, TTL_DOCUMENT_GEN)
        self.assertEqual(ttl_doc, 3600)

        # 普通政策/问答 -> 86400s
        ttl_policy = calculate_ttl(["search_policy"])
        self.assertEqual(ttl_policy, TTL_POLICY_DOCS)
        self.assertEqual(ttl_policy, 86400)

        # 无工具调用 -> 86400s
        ttl_none = calculate_ttl([])
        self.assertEqual(ttl_none, TTL_POLICY_DOCS)

    def test_06_evict_on_write_invalidation(self):
        """测试写操作（如提交请假）触发关联查询缓存主动失效 (Evict-on-Write)"""
        model = "gemini-3.7-flash"
        q_leave = "张明的年假还有几天？"
        q_policy = "差旅报销标准是怎样的？"

        # 存入一条个人动态假期查询缓存
        set_cached_response(
            question=q_leave,
            content="您还有5天年假。",
            model=model,
            tools_used=["query_leave_balance"],
        )
        # 存入一条静态政策缓存
        set_cached_response(
            question=q_policy,
            content="一线城市住宿上限500元/晚。",
            model=model,
            tools_used=["search_policy"],
        )

        # 验证此时两条缓存都在
        self.assertIsNotNone(get_cached_response(q_leave, model))
        self.assertIsNotNone(get_cached_response(q_policy, model))

        # 触发写操作：提交请假申请 (submit_leave_request)
        deleted = invalidate_cache_on_write("submit_leave_request")
        self.assertGreaterEqual(deleted, 1)

        # 假期相关的个人动态缓存应已被主动淘汰！
        self.assertIsNone(get_cached_response(q_leave, model), "请假申请提交后，年假查询缓存必须已被淘汰")

        # 无关的静态政策缓存依然健康保留！
        self.assertIsNotNone(get_cached_response(q_policy, model), "无关政策缓存不应受影响")


if __name__ == "__main__":
    unittest.main()
