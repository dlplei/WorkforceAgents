"""
Redis 缓存服务
支持 AI 回复内容缓存，实现高频重复提问毫秒级秒回 (Prompt / Response Cache)
支持复用宿主机/容器中的 Redis 实例，采用 DB 隔离与 key 前缀隔离机制。
"""
import hashlib
import json
import logging
import re
import time
from typing import Optional, Dict, Any, List

import redis
from config import get_redis_config

logger = logging.getLogger(__name__)

# 全局 Redis 客户端连接池单例
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None
_is_connected: bool = False


def get_redis_client() -> Optional[redis.Redis]:
    """获取 Redis 客户端单例（线程安全连接池）"""
    global _redis_pool, _redis_client, _is_connected
    cfg = get_redis_config()
    if not cfg.enabled:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        _redis_pool = redis.ConnectionPool(
            host=cfg.host,
            port=cfg.port,
            db=cfg.db,
            password=cfg.password,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        client = redis.Redis(connection_pool=_redis_pool)
        client.ping()
        _redis_client = client
        _is_connected = True
        logger.info(f"✅ 成功连接 Redis (Host: {cfg.host}:{cfg.port}, DB: {cfg.db})")
        return _redis_client
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接不可用 ({cfg.host}:{cfg.port}/db{cfg.db}): {e}，将绕过缓存直接请求模型")
        _redis_client = None
        _is_connected = False
        return None


def init_cache() -> bool:
    """在服务启动时验证并初始化缓存连接"""
    client = get_redis_client()
    return client is not None


def normalize_question(question: str) -> str:
    """
    标准化用户提问文本：
    - 去除首尾空白
    - 统一小写
    - 去除首尾标点符号（如中英文问号、句号、感叹号等），增强模糊命中率
    """
    q = question.strip().lower()
    # 去除末尾常见标点符号
    q = re.sub(r'[\s\?\!\,\.\;\:\'\"，。？！；：“”‘’]+$', '', q)
    return q


def generate_cache_key(question: str, model: str = "") -> str:
    """生成统一规范的 Redis Cache Key"""
    norm_q = normalize_question(question)
    raw = f"{norm_q}::{model}"
    q_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
    return f"workforce:cache:qa:{q_hash}"


def get_cached_response(question: str, model: str = "") -> Optional[Dict[str, Any]]:
    """
    查询问题缓存
    如果命中返回包含 content、cached_at 等信息的字典，未命中返回 None
    """
    client = get_redis_client()
    if client is None:
        return None

    key = generate_cache_key(question, model)
    try:
        data_str = client.get(key)
        if not data_str:
            return None

        data = json.loads(data_str)
        # 增加命中计数
        client.hincrby("workforce:cache:metrics", "hit_count", 1)
        logger.info(f"⚡ Redis 缓存命中! [Key: {key}] 问题: '{question[:40]}...'")
        return data
    except Exception as e:
        logger.warning(f"读取 Redis 缓存异常: {e}")
        return None


def set_cached_response(
    question: str,
    content: str,
    model: str = "",
    tools_used: Optional[List[str]] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    ttl: Optional[int] = None,
) -> bool:
    """
    将 AI 回复内容存入 Redis 缓存
    :param question: 原始用户提问
    :param content: AI 生成的完整文本内容
    :param model: 所用模型标识
    :param tools_used: 过程中调用的工具名列表
    :param tool_calls: 过程中捕获的工具调用详情
    :param tool_results: 过程中捕获的工具执行结果详情
    :param ttl: 过期时间（秒），默认取配置项
    """
    if not content or not content.strip():
        return False

    client = get_redis_client()
    if client is None:
        return False

    cfg = get_redis_config()
    expire_seconds = ttl if ttl is not None else cfg.ttl
    key = generate_cache_key(question, model)

    payload = {
        "question": question,
        "content": content,
        "model": model,
        "tools_used": tools_used or [],
        "tool_calls": tool_calls or [],
        "tool_results": tool_results or [],
        "cached_at": int(time.time()),
        "expires_in": expire_seconds,
    }

    try:
        client.set(key, json.dumps(payload, ensure_ascii=False), ex=expire_seconds)
        client.hincrby("workforce:cache:metrics", "set_count", 1)
        logger.info(f"💾 AI 回复已成功写入 Redis 缓存 [Key: {key}, TTL: {expire_seconds}s]")
        return True
    except Exception as e:
        logger.warning(f"写入 Redis 缓存异常: {e}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存状态与统计信息"""
    cfg = get_redis_config()
    client = get_redis_client()
    if client is None:
        return {
            "enabled": cfg.enabled,
            "connected": False,
            "host": cfg.host,
            "port": cfg.port,
            "db": cfg.db,
            "keys_count": 0,
            "metrics": {},
        }

    try:
        keys = client.keys("workforce:cache:qa:*")
        metrics = client.hgetall("workforce:cache:metrics")
        info = client.info("memory")
        return {
            "enabled": cfg.enabled,
            "connected": True,
            "host": cfg.host,
            "port": cfg.port,
            "db": cfg.db,
            "keys_count": len(keys),
            "keys": keys[:10],  # 最多预览前10个
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"获取 Redis 统计异常: {e}")
        return {"connected": False, "error": str(e)}


def clear_cache(pattern: str = "workforce:cache:*") -> int:
    """清空当前项目的缓存键"""
    client = get_redis_client()
    if client is None:
        return 0

    try:
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"🧹 已清空 {deleted} 个 Redis 缓存键 (匹配: {pattern})")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"清空 Redis 缓存异常: {e}")
        return 0
