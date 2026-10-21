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
    base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    base_url: str = "https://api.servicesessentials.ibm.com/v1"
    api_key: str = ""
    model: str = "gemini-3.7-flash"
    temperature: float = 0.7
    max_tokens: int = 2048


# 全局配置（运行时由前端传入）
current_config = LLMConfig()

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
    """更新全局配置"""
    global current_config
    current_config = config


def get_config() -> LLMConfig:
    """获取当前配置"""
    return current_config
