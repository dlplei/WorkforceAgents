#!/usr/bin/env python3
"""
测试配置加载
"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import current_config, get_config

print("=" * 60)
print("🔍 配置加载测试")
print("=" * 60)

config = get_config()

print(f"\n✅ 配置加载成功:")
print(f"   - Base URL: {config.base_url}")
print(f"   - Model: {config.model}")
print(f"   - Temperature: {config.temperature}")
print(f"   - Max Tokens: {config.max_tokens}")
print(f"   - API Key: {'已配置 (' + config.api_key[:8] + '...)' if config.api_key else '❌ 未配置'}")

print("\n" + "=" * 60)

if not config.api_key:
    print("⚠️  警告: API Key 未配置!")
    print("💡 请复制 .env.example 为 .env 并填入你的 API Key")
    print("=" * 60)
    sys.exit(1)
else:
    print("✅ 配置正常，可以启动服务")
    print("=" * 60)
    sys.exit(0)
