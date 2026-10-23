"""
Workforce Operations Agent - LangGraph 架构回归测试
验证场景：
1. 政策咨询与 RAG 检索（知识库检索 + 推理）
2. 工具调用（假期余额查询 + 状态机流转）
3. SSE 事件流契约验证（node_enter, node_exit, tool_call, tool_result, token, message_complete）
4. 多轮对话上下文延续性
"""
import asyncio
import os
import sys

# 确保 backend 路径加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.engine import AgentEngine
from agent.graph import build_workforce_graph


async def test_scenario_policy_rag():
    print("\n" + "=" * 60)
    print("🧪 测试场景 1: 政策咨询与 RAG 知识检索")
    print("=" * 60)
    
    engine = AgentEngine()
    query = "公司的年假政策是怎么规定的？请问休假前需要提前几天申请？"
    print(f"用户提问: {query}")

    received_events = []
    tokens = []

    async for event in engine.run(query):
        received_events.append(event["type"])
        if event["type"] == "token":
            tokens.append(event["content"])
        elif event["type"] in ["node_enter", "node_exit"]:
            print(f"  [{event['type']}] -> {event['content']}")
        elif event["type"] == "tool_call":
            print(f"  [tool_call] -> {event['data']['name']}({event['data']['arguments']})")

    full_reply = "".join(tokens)
    print(f"\nAgent 最终回复 ({len(full_reply)} 字):\n{full_reply[:200]}...")

    assert "node_enter" in received_events, "未触发 node_enter 事件"
    assert "node_exit" in received_events, "未触发 node_exit 事件"
    assert "token" in received_events, "未产生流式 token"
    assert "message_complete" in received_events, "未产生 message_complete 事件"
    assert len(engine.conversation_history) == 2, "历史记录未正确保存"
    print("✅ 测试场景 1 通过！")


async def test_scenario_tool_calling():
    print("\n" + "=" * 60)
    print("🧪 测试场景 2: 工具调用（年假余额查询）")
    print("=" * 60)

    engine = AgentEngine()
    query = "帮我查一下我目前的年假余额还剩几天？"
    print(f"用户提问: {query}")

    tool_called = False
    tool_result_received = False
    tokens = []

    async for event in engine.run(query):
        if event["type"] == "tool_call":
            tool_called = True
            print(f"  [tool_call] -> 触发工具: {event['data']['name']}, 参数: {event['data']['arguments']}")
        elif event["type"] == "tool_result":
            tool_result_received = True
            print(f"  [tool_result] -> 结果成功: {event['data']['success']}")
        elif event["type"] == "token":
            tokens.append(event["content"])
        elif event["type"] in ["node_enter", "node_exit"]:
            print(f"  [{event['type']}] -> {event['content']}")

    full_reply = "".join(tokens)
    print(f"\nAgent 最终回复 ({len(full_reply)} 字):\n{full_reply[:200]}...")

    assert tool_called, "未触发工具调用"
    assert tool_result_received, "未收到工具返回结果"
    assert len(tokens) > 0, "未产生最终回复流式 token"
    print("✅ 测试场景 2 通过！")


async def test_scenario_multi_turn():
    print("\n" + "=" * 60)
    print("🧪 测试场景 3: 多轮对话上下文延续")
    print("=" * 60)

    engine = AgentEngine()
    # 第一轮
    print("第 1 轮: 问名字")
    tokens1 = []
    async for event in engine.run("请告诉我你的名字和主要职责"):
        if event["type"] == "token":
            tokens1.append(event["content"])
    print(f"第 1 轮回复: {''.join(tokens1)[:80]}...")

    # 第二轮
    print("\n第 2 轮: 上下文追问")
    tokens2 = []
    async for event in engine.run("我刚刚问了你什么？"):
        if event["type"] == "token":
            tokens2.append(event["content"])
    reply2 = "".join(tokens2)
    print(f"第 2 轮回复: {reply2[:100]}...")

    assert len(engine.conversation_history) == 4, f"历史记录条数不对: {len(engine.conversation_history)}"
    print("✅ 测试场景 3 通过！")


async def main():
    try:
        await test_scenario_policy_rag()
        await test_scenario_tool_calling()
        await test_scenario_multi_turn()
        print("\n" + "🎉" * 20)
        print("所有 LangGraph 回归测试全部通过！")
        print("🎉" * 20)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
