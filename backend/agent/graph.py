"""
LangGraph 状态图定义
包含 Workforce Operations Agent 的状态定义、节点与工作流编排
"""
import json
import logging
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from datetime import datetime

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from config import LLMConfig
from db.database import get_current_employee
from agent.knowledge import retrieve_knowledge
from agent.tools import registry

logger = logging.getLogger(__name__)


# ============ State Definition ============

class AgentState(TypedDict):
    """LangGraph 状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    retrieved_docs: List[Dict[str, Any]]


# ============ System Prompt Builder ============

def build_system_prompt() -> str:
    """构建动态系统提示词，注入当前员工信息和实时系统时间"""
    emp = get_current_employee()
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_date_str = f"{now.year}年{now.month}月{now.day}日 {weekdays[now.weekday()]}"
    current_iso_date = now.strftime("%Y-%m-%d")

    return f"""你是一个智能员工服务与人力运营 Agent（Workforce Operations Agent）。

## 你的身份
- 你服务于「星辰科技有限公司」的员工
- 当前登录员工：{emp.name}（{emp.id}），{emp.department}，{emp.position}
- 你的职责是帮助员工完成 HR 相关事务

## 当前环境与时间基准（重要）
- 当前系统日期：{current_date_str}（{current_iso_date}）
- 当前所在年份：{now.year}年
- **日期处理与推断原则**：
  1. 员工在日常对话中通常使用相对日期（如"明天"、"下周三"）或省略年份（如"10月8日到10日"）。
  2. 你**必须严格以当前系统日期（{now.year}年）为基准**推算目标年份和日期，绝对不要使用 2024 年或任何训练集中的历史过时年份。
  3. 未指明年份时，优先推断为当前年份（{now.year}年）；若该日期在当前年份已过去且语境表明是未来请假，则合理推断为下一自然年（{now.year + 1}年）。
  4. 生成确认摘要和调用工具参数时，请使用正确的推断日期（格式：YYYY-MM-DD）。

## 你的能力
1. 政策咨询：查询和解释公司各项 HR 政策
2. 休假管理：查询假期余额、协助请假申请
3. 差旅管理：计算差旅预算、协助差旅申请
4. 证明开具：协助开具各类证明
5. 信息查询：查询员工信息、审批状态等

## 工作原则
1. **Policy Grounding**：回答政策问题时，必须基于检索到的政策原文，不可编造。**政策依据（Policy Reference）严格仅限于检索到的政策文档原文。若结合国家政务常识或通用经验进行补充，必须明确区分为【国家/公开渠道参考指引】，严禁将外部常识冒充为公司政策条款。**
2. **引用来源**：回答时标注政策依据（如"根据《员工年假管理办法》第X条"），政策中未记载的内容不可断言为政策条款。
3. **确认操作**：涉及提交申请等写操作时，必须先展示摘要请用户确认
4. **个性化**：结合当前员工的身份、部门、级别给出个性化建议
5. **诚实边界**：不确定的内容明确告知，不猜测

## 输出格式
- 使用清晰的 Markdown 格式
- 重要信息用 **加粗** 标注
- 列表项用 - 或数字编号
- 涉及金额、天数等关键数据要突出显示"""


def format_full_system_message(retrieved_docs: Optional[List[Dict[str, Any]]] = None) -> SystemMessage:
    """组合基础 System Prompt 与 RAG 检索知识"""
    content = build_system_prompt()
    if retrieved_docs:
        content += "\n\n## 相关政策知识（检索结果）\n"
        for i, doc in enumerate(retrieved_docs, 1):
            title = doc.get("title", "")
            doc_id = doc.get("doc_id", "")
            doc_content = doc.get("content", "")
            content += f"\n### [{i}] {title}（{doc_id}）\n{doc_content}\n"
    return SystemMessage(content=content)


# ============ Nodes ============

async def knowledge_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """知识检索节点：根据最新用户问题检索 HR 政策库"""
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            user_query = msg.content
            break

    retrieved = []
    if user_query:
        try:
            chunks = retrieve_knowledge(user_query, top_k=3)
            for chunk in chunks:
                retrieved.append({
                    "id": getattr(chunk, "id", ""),
                    "doc_id": getattr(chunk, "doc_id", getattr(chunk, "id", "")),
                    "title": getattr(chunk, "title", ""),
                    "category": getattr(chunk, "category", ""),
                    "content": getattr(chunk, "content", ""),
                })
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")

    return {"retrieved_docs": retrieved}


def create_reasoning_node(config: LLMConfig):
    """创建推理节点：调用带工具绑定的 ChatOpenAI 模型"""
    llm = ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        streaming=True,
        timeout=120.0,
    )
    tools = registry.get_for_llm()
    bound_llm = llm.bind_tools(tools)

    async def reasoning_node(state: AgentState) -> Dict[str, Any]:
        retrieved_docs = state.get("retrieved_docs", [])
        system_msg = format_full_system_message(retrieved_docs)
        messages = [system_msg] + list(state.get("messages", []))
        response = await bound_llm.ainvoke(messages)
        return {"messages": [response]}

    return reasoning_node


async def tool_execution_node(state: AgentState) -> Dict[str, Any]:
    """工具执行节点：执行 AIMessage 中的 tool_calls 并返回 ToolMessages"""
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
        return {"messages": []}

    tool_messages = []
    for tc in last_msg.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        tool_call_id = tc["id"]

        # 发出自定义事件供 SSE 流捕获
        await adispatch_custom_event(
            "tool_call",
            {"id": tool_call_id, "name": tool_name, "arguments": tool_args}
        )

        result = await registry.execute(tool_name, tool_args)

        await adispatch_custom_event(
            "tool_result",
            result.model_dump()
        )

        content_str = json.dumps(
            result.data if result.success else {"error": result.error},
            ensure_ascii=False
        )

        tool_messages.append(
            ToolMessage(
                content=content_str,
                tool_call_id=tool_call_id,
                name=tool_name,
            )
        )

    return {"messages": tool_messages}


# ============ Conditional Routing ============

def should_continue(state: AgentState) -> str:
    """条件路由：检查模型是否产生工具调用"""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tool_execution"
    return END


# ============ Graph Construction ============

def build_workforce_graph(config: LLMConfig, checkpointer=None):
    """构建 Workforce Operations 状态图"""
    workflow = StateGraph(AgentState)

    workflow.add_node("knowledge_retrieval", knowledge_retrieval_node)
    workflow.add_node("reasoning", create_reasoning_node(config))
    workflow.add_node("tool_execution", tool_execution_node)

    workflow.add_edge(START, "knowledge_retrieval")
    workflow.add_edge("knowledge_retrieval", "reasoning")

    workflow.add_conditional_edges(
        "reasoning",
        should_continue,
        {
            "tool_execution": "tool_execution",
            END: END,
        }
    )

    workflow.add_edge("tool_execution", "reasoning")

    return workflow.compile(checkpointer=checkpointer)

