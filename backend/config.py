"""
配置管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ 已加载 .env 文件: {env_path}")
else:
    logger.warning(f"⚠️  未找到 .env 文件: {env_path}")
    logger.info("💡 请复制 .env.example 为 .env 并配置参数")


class LLMConfig(BaseModel):
    """LLM 配置"""
    base_url: str = os.getenv("LLM_BASE_URL", "https://api.servicesessentials.ibm.com/v1")
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "gemini-3.7-flash")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))


class RedisConfig(BaseModel):
    """Redis 缓存配置"""
    enabled: bool = os.getenv("REDIS_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "1"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD", None) or None
    ttl: int = int(os.getenv("REDIS_CACHE_TTL", "86400"))  # 默认 24 小时


# 全局配置（运行时由前端传入）
current_config = LLMConfig()
redis_config = RedisConfig()

# 启动时打印配置信息
logger.info("=" * 60)
logger.info("📋 LLM 配置信息:")
logger.info(f"   - Base URL: {current_config.base_url}")
logger.info(f"   - Model: {current_config.model}")
logger.info(f"   - Temperature: {current_config.temperature}")
logger.info(f"   - Max Tokens: {current_config.max_tokens}")
logger.info(f"   - API Key: {'已配置' if current_config.api_key else '❌ 未配置'}")
logger.info("=" * 60)


def update_config(config: LLMConfig):
    """更新全局配置（空字段保留 .env 默认值）"""
    global current_config
    if config.base_url and config.base_url.strip():
        current_config.base_url = config.base_url.strip()
    if config.api_key and config.api_key.strip():
        current_config.api_key = config.api_key.strip()
    if config.model and config.model.strip():
        current_config.model = config.model.strip()
    if config.temperature is not None:
        current_config.temperature = config.temperature
    if config.max_tokens is not None and config.max_tokens > 0:
        current_config.max_tokens = config.max_tokens


def get_config() -> LLMConfig:
    """获取当前配置"""
    return current_config


def get_redis_config() -> RedisConfig:
    """获取当前 Redis 配置"""
    return redis_config

