"""
配置管理
"""
from pydantic import BaseModel
from typing import Optional


class LLMConfig(BaseModel):
    """LLM 配置"""
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048


# 全局配置（运行时由前端传入）
current_config = LLMConfig()


def update_config(config: LLMConfig):
    """更新全局配置"""
    global current_config
    current_config = config


def get_config() -> LLMConfig:
    """获取当前配置"""
    return current_config
