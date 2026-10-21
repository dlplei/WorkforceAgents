"""
Agent 核心引擎 - ReAct 循环 + 流式输出
"""
import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx

from config import LLMConfig, get_config
from mock_data import get_current_employee
from agent.knowledge import retrieve_knowledge
from agent.tools import registry

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============ System Prompt ============

def build_system_prompt() -> str:
    emp = get_current_employee()
    return f"""你是一个智能员工服务与人力运营 Agent（Workforce Operations Agent）。

## 你的身份
- 你服务于「星辰科技有限公司」的员工
- 当前登录员工：{emp.name}（{emp.id}），{emp.department}，{emp.position}
- 你的职责是帮助员工完成 HR 相关事务

## 你的能力
1. 政策咨询：查询和解释公司各项 HR 政策
2. 休假管理：查询假期余额、协助请假申请
3. 差旅管理：计算差旅预算、协助差旅申请
4. 证明开具：协助开具各类证明
5. 信息查询：查询员工信息、审批状态等

## 工作原则
1. **Policy Grounding**：回答政策问题时，必须基于检索到的政策原文，不可编造
2. **引用来源**：回答时标注政策依据（如"根据《员工年假管理办法》第X条"）
3. **确认操作**：涉及提交申请等写操作时，必须先展示摘要请用户确认
4. **个性化**：结合当前员工的身份、部门、级别给出个性化建议
5. **诚实边界**：不确定的内容明确告知，不猜测

## 输出格式
- 使用清晰的 Markdown 格式
- 重要信息用 **加粗** 标注
- 列表项用 - 或数字编号
- 涉及金额、天数等关键数据要突出显示"""


# ============ Agent Engine ============

class AgentEngine:
    """Agent 引擎"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_config()
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 6

    def update_config(self, config: LLMConfig):
        self.config = config

    def clear_history(self):
        self.conversation_history = []

    async def run(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """运行 Agent，产生事件流"""

        # 添加用户消息到历史
        self.conversation_history.append({"role": "user", "content": user_message})

        # 检索知识
        yield {"type": "status", "content": "thinking"}
        yield {"type": "node_enter", "content": "knowledge_retrieval"}

        knowledge = retrieve_knowledge(user_message, top_k=3)
        context_prompt = ""
        if knowledge:
            context_prompt = "\n\n## 相关政策知识（检索结果）\n"
            for i, k in enumerate(knowledge, 1):
                context_prompt += f"\n### [{i}] {k.title}（{k.doc_id}）\n{k.content}\n"

        yield {"type": "node_exit", "content": "knowledge_retrieval"}

        # 构建消息列表
        messages = [
            {"role": "system", "content": build_system_prompt() + context_prompt},
        ]
        for msg in self.conversation_history:
            messages.append(msg)

        # ReAct 循环
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            yield {"type": "node_enter", "content": "reasoning"}

            try:
                response = await self._call_llm(messages)
                yield {"type": "node_exit", "content": "reasoning"}

                # 检查是否有工具调用
                tool_calls = response.get("tool_calls")
                if tool_calls:
                    # 添加 assistant 消息（含 tool_calls）
                    messages.append({
                        "role": "assistant",
                        "content": response.get("content") or "",
                        "tool_calls": tool_calls,
                    })

                    # 执行每个工具
                    for tc in tool_calls:
                        yield {
                            "type": "tool_call",
                            "data": {
                                "id": tc["id"],
                                "name": tc["function"]["name"],
                                "arguments": json.loads(tc["function"]["arguments"]),
                            },
                        }
                        yield {"type": "status", "content": "tool_calling"}
                        yield {"type": "node_enter", "content": "tool_execution"}

                        result = await registry.execute(
                            tc["function"]["name"],
                            json.loads(tc["function"]["arguments"]),
                        )

                        yield {"type": "tool_result", "data": result.model_dump()}

                        # 添加工具结果到消息
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result.data or result.error or "", ensure_ascii=False),
                        })

                        yield {"type": "node_exit", "content": "tool_execution"}

                    # 继续循环获取最终回复
                    continue

                # 没有工具调用 - 这是最终回复
                yield {"type": "status", "content": "responding"}
                yield {"type": "node_enter", "content": "response_generation"}

                full_content = response.get("content", "")

                # 流式输出（如果是流式响应）
                if response.get("stream"):
                    async for chunk in response["stream"]:
                        yield {"type": "token", "content": chunk}
                else:
                    # 非流式，一次性输出
                    for char in full_content:
                        yield {"type": "token", "content": char}
                        await asyncio.sleep(0)  # 让出控制权

                yield {"type": "node_exit", "content": "response_generation"}

                # 添加到历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_content,
                })

                yield {"type": "message_complete", "content": full_content}
                yield {"type": "status", "content": "idle"}
                return

            except Exception as e:
                yield {"type": "error", "content": str(e)}
                yield {"type": "status", "content": "error"}
                return

        # 达到最大迭代
        yield {"type": "error", "content": "Agent 达到最大迭代次数，请简化您的问题"}
        yield {"type": "status", "content": "idle"}

    async def _call_llm(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用 LLM API"""
        cfg = self.config

        if not cfg.api_key:
            raise ValueError("请先配置 API Key")

        url = f"{cfg.base_url.rstrip('/')}/chat/completions"
        
        # 记录请求信息
        logger.info(f"🚀 调用 LLM API: {url}")
        logger.info(f"📋 模型: {cfg.model}")
        logger.info(f"📊 消息数量: {len(messages)}")
        logger.info(f"🔧 工具数量: {len(registry.get_for_llm())}")
        logger.debug(f"🌡️  Temperature: {cfg.temperature}, Max Tokens: {cfg.max_tokens}")
        
        # 隐藏 API Key 的日志
        api_key_masked = cfg.api_key[:8] + "..." + cfg.api_key[-4:] if len(cfg.api_key) > 12 else "***"
        logger.info(f"🔑 API Key: {api_key_masked}")

        payload = {
            "model": cfg.model,
            "messages": messages,
            "tools": registry.get_for_llm(),
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info("📡 发送请求中...")
                
                async with client.stream(
                    "POST",
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cfg.api_key}",
                    },
                    json=payload,
                ) as response:
                    logger.info(f"📨 响应状态码: {response.status_code}")
                    logger.info(f"📝 响应头: {dict(response.headers)}")
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        error_msg = error_text.decode()
                        logger.error(f"❌ LLM API 错误: {response.status_code}")
                        logger.error(f"❌ 错误详情: {error_msg}")
                        raise ValueError(
                            f"LLM API 错误 ({response.status_code}): {error_msg}\n"
                            f"URL: {url}\n"
                            f"模型: {cfg.model}"
                        )

                    logger.info("✅ 开始解析响应流")
                    return await self._parse_stream(response)
                    
        except httpx.ConnectError as e:
            logger.error(f"🔌 连接错误: {e}")
            logger.error(f"🔌 目标 URL: {url}")
            logger.error(f"🔌 可能的原因:")
            logger.error(f"   1. 后端无法访问 LLM API 服务器")
            logger.error(f"   2. 网络连接问题或防火墙限制")
            logger.error(f"   3. API Base URL 配置错误")
            logger.error(f"   4. 需要代理但未配置")
            raise ValueError(
                f"无法连接到 LLM API: {url}\n"
                f"错误: {e}\n"
                f"请检查:\n"
                f"1. Base URL 是否正确: {cfg.base_url}\n"
                f"2. 网络是否可以访问该地址\n"
                f"3. 是否需要配置代理"
            ) from e
            
        except httpx.TimeoutException as e:
            logger.error(f"⏱️  请求超时: {e}")
            raise ValueError(f"LLM API 请求超时，请检查网络连接或稍后重试") from e
            
        except Exception as e:
            logger.error(f"💥 未预期的错误: {type(e).__name__}: {e}")
            logger.exception("完整异常堆栈:")
            raise ValueError(f"调用 LLM API 时发生错误: {e}") from e

    async def _parse_stream(self, response) -> Dict[str, Any]:
        """解析 SSE 流"""
        full_content = ""
        tool_calls_map: Dict[int, Dict[str, Any]] = {}
        chunks: List[str] = []

        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data = line[6:].strip()
            if data == "[DONE]":
                break

            try:
                parsed = json.loads(data)
                delta = parsed.get("choices", [{}])[0].get("delta", {})

                # 处理工具调用
                if "tool_calls" in delta:
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        existing = tool_calls_map[idx]
                        if tc.get("id"):
                            existing["id"] = tc["id"]
                        if tc.get("function", {}).get("name"):
                            existing["function"]["name"] = tc["function"]["name"]
                        if tc.get("function", {}).get("arguments"):
                            existing["function"]["arguments"] += tc["function"]["arguments"]

                # 处理内容
                if delta.get("content"):
                    chunks.append(delta["content"])
                    full_content += delta["content"]

            except json.JSONDecodeError:
                continue

        # 如果有工具调用，返回工具调用
        if tool_calls_map:
            tool_calls = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                try:
                    tc["function"]["arguments"] = json.loads(tc["function"]["arguments"])
                    # 重新序列化为字符串（LLM API 期望字符串）
                    tc["function"]["arguments"] = json.dumps(tc["function"]["arguments"], ensure_ascii=False)
                except json.JSONDecodeError:
                    tc["function"]["arguments"] = "{}"
                tool_calls.append(tc)
            return {"content": full_content, "tool_calls": tool_calls}

        # 否则返回流式内容
        async def gen_chunks():
            for chunk in chunks:
                yield chunk

        return {"content": full_content, "stream": gen_chunks()}
