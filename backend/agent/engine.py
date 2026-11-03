"""
Agent 核心引擎 - LangGraph 工作流驱动 + SSE 流式输出
"""
import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from config import LLMConfig, get_config
from agent.graph import build_workforce_graph, build_system_prompt
from agent.guardrails import evaluate_guardrails
from services.metrics_service import record_llm_usage, record_hitl_action, record_node_duration

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# ============ Agent Engine ============

class AgentEngine:
    """基于 LangGraph 状态图的 Agent 引擎"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_config()
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 15

    def update_config(self, config: LLMConfig):
        self.config = config

    def clear_history(self):
        self.conversation_history = []

    async def run(
        self,
        user_message: str,
        hitl_confirmed: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """运行 Agent 状态图，产生对齐前端协议的 SSE 事件流，支持原生 HITL 门禁挂起与授权执行"""
        logger.info(f"🚀 开始执行 Agent 请求: {user_message[:60]}...")

        # 初始思考状态
        yield {"type": "status", "content": "thinking"}

        # 0. 前置输入安全、越权探针、偏离业务与情绪护栏审查 (Guardrails Fast-Fail & Moderation)
        yield {"type": "node_enter", "content": "guardrail_check"}
        guardrail_res = evaluate_guardrails(user_message, self.conversation_history)

        # 场景 A: 拦截恶意提示词注入/越狱、数据越权刺探、或无业务意图的辱骂挑衅
        if guardrail_res.is_blocked:
            logger.warning(f"🚨 [Guardrails 拦截] 类别: {guardrail_res.category} | 原因: {guardrail_res.reason}")
            reply = guardrail_res.refusal_message
            yield {"type": "status", "content": "responding"}
            for i in range(0, len(reply), 6):
                yield {"type": "token", "content": reply[i:i+6]}
                await asyncio.sleep(0.015)
            yield {"type": "node_exit", "content": "guardrail_check"}
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": reply})
            yield {"type": "message_complete", "content": reply}
            yield {"type": "status", "content": "idle"}
            return

        # 场景 B: 偏离业务话题（如代码编写、写诗、解题、外部闲聊）或纯问候快速引导
        if guardrail_res.is_off_topic:
            logger.info(f"🧭 [Guardrails 引导] 类别: {guardrail_res.category} | 原因: {guardrail_res.reason}")
            reply = guardrail_res.refusal_message
            yield {"type": "status", "content": "responding"}
            for i in range(0, len(reply), 6):
                yield {"type": "token", "content": reply[i:i+6]}
                await asyncio.sleep(0.015)
            yield {"type": "node_exit", "content": "guardrail_check"}
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": reply})
            yield {"type": "message_complete", "content": reply}
            yield {"type": "status", "content": "idle"}
            return

        # 前置安全护栏审查通过，正常流转至状态图业务处理
        yield {"type": "node_exit", "content": "guardrail_check"}

        # 场景 C: 合规业务请求（如伴随负面情绪，将情绪安抚与工单升级指引注入状态机）
        # 构建历史消息列表
        messages: List[BaseMessage] = []
        for msg in self.conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # 加入当前用户消息
        messages.append(HumanMessage(content=user_message))

        # 构建并编译 LangGraph 状态图
        graph = build_workforce_graph(self.config)

        full_content = ""
        in_response_generation = False
        current_has_tool_call = False

        initial_state = {
            "messages": messages,
            "retrieved_docs": [],
            "emotion_instruction": guardrail_res.emotion_instruction if guardrail_res.has_negative_emotion else None,
            "hitl_confirmed": hitl_confirmed,
        }

        node_start_times: Dict[str, float] = {}

        try:
            async for ev in graph.astream_events(
                initial_state,
                version="v2",
                config={"recursion_limit": self.max_iterations * 2}
            ):
                event_kind = ev.get("event")
                name = ev.get("name")

                # 1. 状态图节点进入
                if event_kind == "on_chain_start":
                    if name in ("knowledge_retrieval", "reasoning", "tool_execution"):
                        node_start_times[name] = asyncio.get_event_loop().time()

                    if name == "knowledge_retrieval":
                        yield {"type": "node_enter", "content": "knowledge_retrieval"}
                    elif name == "reasoning":
                        current_has_tool_call = False
                        yield {"type": "node_enter", "content": "reasoning"}
                    elif name == "tool_execution":
                        yield {"type": "status", "content": "tool_calling"}
                        yield {"type": "node_enter", "content": "tool_execution"}

                # 2. 状态图节点退出
                elif event_kind == "on_chain_end":
                    if name in node_start_times:
                        duration = asyncio.get_event_loop().time() - node_start_times.pop(name, 0.0)
                        record_node_duration(name, duration)

                    if name == "knowledge_retrieval":
                        yield {"type": "node_exit", "content": "knowledge_retrieval"}
                    elif name == "reasoning":
                        if in_response_generation:
                            yield {"type": "node_exit", "content": "response_generation"}
                            in_response_generation = False
                        yield {"type": "node_exit", "content": "reasoning"}
                    elif name == "tool_execution":
                        yield {"type": "node_exit", "content": "tool_execution"}

                # 3. 自定义事件（工具调用、工具返回与原生 HITL 门禁挂起请求）
                elif event_kind == "on_custom_event":
                    ev_name = ev.get("name")
                    ev_data = ev.get("data")
                    if ev_name == "tool_call":
                        yield {"type": "tool_call", "data": ev_data}
                    elif ev_name == "tool_result":
                        yield {"type": "tool_result", "data": ev_data}
                    elif ev_name == "hitl_request":
                        tool_name = (ev_data or {}).get("tool_name", "unknown")
                        record_hitl_action("triggered", tool_name)
                        yield {"type": "hitl_request", "data": ev_data}

                # 4. 模型流式输出
                elif event_kind == "on_chat_model_stream":
                    chunk = ev.get("data", {}).get("chunk")
                    if not chunk:
                        continue

                    # 若存在工具调用 chunk，标记当前轮次为工具调用，不推送文本 token
                    if getattr(chunk, "tool_call_chunks", None):
                        current_has_tool_call = True

                    # 正常生成文本 token 且本轮无工具调用
                    if chunk.content and not current_has_tool_call:
                        if not in_response_generation:
                            in_response_generation = True
                            yield {"type": "status", "content": "responding"}
                            yield {"type": "node_enter", "content": "response_generation"}

                        yield {"type": "token", "content": chunk.content}
                        full_content += chunk.content

                # 5. 模型输出结束（统计 Token 与耗时兜底）
                elif event_kind == "on_chat_model_end":
                    output = ev.get("data", {}).get("output")
                    if output:
                        # 尝试提取 usage_metadata
                        usage = getattr(output, "usage_metadata", None) or {}
                        p_tokens = usage.get("input_tokens", 0)
                        c_tokens = usage.get("output_tokens", 0)
                        if not p_tokens and not c_tokens:
                            c_tokens = len(getattr(output, "content", "") or "")
                            p_tokens = max(10, len(user_message))
                        record_llm_usage(
                            prompt_tokens=p_tokens,
                            completion_tokens=c_tokens,
                            model=getattr(self.config, "model_name", "qwen2.5"),
                            purpose="reasoning",
                        )

                    if output and not getattr(output, "tool_calls", None):
                        output_text = getattr(output, "content", "")
                        if not full_content and output_text:
                            yield {"type": "status", "content": "responding"}
                            yield {"type": "node_enter", "content": "response_generation"}
                            for char in output_text:
                                yield {"type": "token", "content": char}
                                await asyncio.sleep(0)
                            full_content = output_text

            # 6. 保存至历史并通知前端完成
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": full_content})

            yield {"type": "message_complete", "content": full_content}
            yield {"type": "status", "content": "idle"}
            logger.info(f"🎉 聊天响应处理完毕，已推送给前端 (共 {len(full_content)} 字符)")

        except Exception as e:
            logger.error(f"Agent engine execution failed: {e}", exc_info=True)
            yield {"type": "error", "content": str(e)}
            yield {"type": "status", "content": "error"}




