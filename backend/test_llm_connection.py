#!/usr/bin/env python3
"""
LLM API 连接测试脚本
用于诊断 LLM API 连接问题
"""
import asyncio
import httpx
import sys


async def test_connection(base_url: str, api_key: str, model: str = "gpt-4o-mini"):
    """测试 LLM API 连接"""
    
    print("=" * 60)
    print("🔍 LLM API 连接测试")
    print("=" * 60)
    print(f"📍 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else f"🔑 API Key: {api_key}")
    print(f"🤖 Model: {model}")
    print("=" * 60)
    
    # 测试 1: 检查 models 端点
    print("\n[1/3] 测试 models 端点...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"✅ 状态码: {response.status_code}")
            if response.status_code == 200:
                print("✅ models 端点可访问")
            else:
                print(f"❌ 错误响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 连接失败: {type(e).__name__}: {e}")
        return False
    
    # 测试 2: 简单的聊天请求（非流式）
    print("\n[2/3] 测试聊天 API（非流式）...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10,
                    "stream": False
                }
            )
            print(f"✅ 状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ 响应内容: {content[:50]}...")
            else:
                print(f"❌ 错误响应: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}: {e}")
        return False
    
    # 测试 3: 流式请求
    print("\n[3/3] 测试聊天 API（流式）...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_tokens": 20,
                    "stream": True
                }
            ) as response:
                print(f"✅ 状态码: {response.status_code}")
                if response.status_code == 200:
                    print("✅ 流式响应开始")
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith(" "):
                            chunk_count += 1
                    print(f"✅ 接收到 {chunk_count} 个数据块")
                else:
                    error_text = await response.aread()
                    print(f"❌ 错误响应: {error_text.decode()[:200]}")
                    return False
    except Exception as e:
        print(f"❌ 流式请求失败: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！LLM API 连接正常")
    print("=" * 60)
    return True


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python test_llm_connection.py <base_url> <api_key> [model]")
        print("示例: python test_llm_connection.py https://api.openai.com/v1 sk-xxx gpt-4o-mini")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gpt-4o-mini"
    
    success = asyncio.run(test_connection(base_url, api_key, model))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
