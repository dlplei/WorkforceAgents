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

    def test_07_cross_employee_private_cache_isolation(self):
        """
        核心安全测试：跨角色/跨员工私有数据隔离防串扰
        - 普通员工张明 (E10293) 提问'帮我查一下我目前的假期余额'并缓存
        - 切换到主管李伟 (E10001)，提问相同内容，绝对不能取出张明的假期数据！
        - 主管李伟写入自己的数据后，两人的私有缓存互不影响、精准秒回各自的数据
        - 验证公共制度依然能跨角色无缝复用
        """
        model = "gemini-3.7-flash"
        q_private = "帮我查一下我目前的假期余额"
        ans_zhangming = "张明您好，您目前剩余年假为 7 天，带薪病假 5 天。"
        ans_liwei = "李伟主管您好，您目前剩余年假为 15 天，带薪病假 10 天。"

        # 1. 普通员工张明 (E10293) 提问并存入缓存
        ok1 = set_cached_response(
            question=q_private,
            content=ans_zhangming,
            model=model,
            employee_id="E10293",
            tools_used=["query_leave_balance"],
        )
        self.assertTrue(ok1)

        # 验证张明本人查询能够命中自己的私有缓存
        hit_zhang = get_cached_response(q_private, model=model, employee_id="E10293")
        self.assertIsNotNone(hit_zhang)
        self.assertEqual(hit_zhang["content"], ans_zhangming)

        # 2. 切换为主管李伟 (E10001)，输入完全相同的问题
        # 核心断言：李伟绝不能从 Redis 中取出张明的假期！必须未命中 (None)
        hit_liwei = get_cached_response(q_private, model=model, employee_id="E10001")
        self.assertIsNone(hit_liwei, "主管账号绝不能查出普通员工的私有假期缓存！")

        # 3. 主管李伟执行模型推理后，写入李伟自己的私有缓存
        ok2 = set_cached_response(
            question=q_private,
            content=ans_liwei,
            model=model,
            employee_id="E10001",
            tools_used=["query_leave_balance"],
        )
        self.assertTrue(ok2)

        # 4. 再次分别以张明和李伟的身份查询，各自命中各自的专属数据
        hit_zhang_again = get_cached_response(q_private, model=model, employee_id="E10293")
        self.assertIsNotNone(hit_zhang_again)
        self.assertEqual(hit_zhang_again["content"], ans_zhangming)

        hit_liwei_again = get_cached_response(q_private, model=model, employee_id="E10001")
        self.assertIsNotNone(hit_liwei_again)
        self.assertEqual(hit_liwei_again["content"], ans_liwei)

        # 5. 验证公共制度在跨员工场景下的正常共享
        q_public = "公司的年假政策是如何规定的？"
        ans_policy = "全员每年享受基本年假5-15天，按司龄累进。"
        set_cached_response(
            question=q_public,
            content=ans_policy,
            model=model,
            employee_id="E10293",
            tools_used=["search_policy"],
        )
        # 张明和李伟均能命中同一份公共制度缓存
        self.assertEqual(get_cached_response(q_public, model=model, employee_id="E10293")["content"], ans_policy)
        self.assertEqual(get_cached_response(q_public, model=model, employee_id="E10001")["content"], ans_policy)

        # 6. 定向写淘汰：张明提交请假单，只淘汰张明的假期私有缓存，李伟的假期私有缓存依然健康
        deleted = invalidate_cache_on_write("submit_leave_request", employee_id="E10293")
        self.assertGreaterEqual(deleted, 1)
        self.assertIsNone(get_cached_response(q_private, model=model, employee_id="E10293"))
        self.assertIsNotNone(get_cached_response(q_private, model=model, employee_id="E10001"), "李伟的缓存不应受张明请假影响")


if __name__ == "__main__":
    unittest.main()
