"""
Workforce Operations Agent - FastAPI Backend
"""
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import LLMConfig, update_config, get_config
from agent.engine import AgentEngine
from agent.tools import registry
from db.database import get_current_employee, init_db
from services.hr_adapter import get_hr_adapter
from services.cache_service import (
    init_cache,
    get_cached_response,
    set_cached_response,
    get_cache_stats,
    clear_cache,
    invalidate_cache_on_write,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
    ]
)
logger = logging.getLogger(__name__)


# ============ FastAPI App ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（替代废弃的 on_event）"""
    logger.info("=" * 60)
    logger.info("🚀 Workforce Operations Agent 启动中...")
    pg_ok = init_db()
    logger.info(f"PostgreSQL connection status: {'SUCCESS' if pg_ok else 'FAILED'}")

    redis_ok = init_cache()
    logger.info(f"Redis Cache connection status: {'SUCCESS' if redis_ok else 'FAILED'}")

    logger.info("=" * 60)
    logger.info(f"📦 已注册工具数量: {len(registry.get_all())}")
    for tool in registry.get_all():
        logger.info(f"   - {tool['name']}: {tool['description'][:50]}...")
    logger.info("=" * 60)

    yield

    logger.info("👋 Workforce Operations Agent 已关闭")


app = FastAPI(
    title="Workforce Operations Agent",
    description="智能员工服务与人力运营 Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Request/Response Models ============

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None
    config: Optional[LLMConfig] = None
    force_refresh: Optional[bool] = False  # 强制跳过缓存重新生成，并在完成时覆写缓存
    hitl_confirmed: Optional[Dict[str, Any]] = None  # 原生 HITL 授权执行载荷


class HitlDecisionRequest(BaseModel):
    action_id: str
    tool_name: str
    decision: str  # "approve" | "reject"
    arguments: Dict[str, Any]
    comment: Optional[str] = None


class ConfigUpdate(BaseModel):
    config: LLMConfig


# ============ API Endpoints ============

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Workforce Operations Agent",
        "version": "0.1.0",
    }


@app.get("/api/employee")
async def get_employee():
    """获取当前登录员工信息"""
    return get_current_employee()


@app.get("/api/tools")
async def get_tools():
    """获取所有可用工具"""
    tools = registry.get_all()
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "category": t["category"],
            "permission_level": t["permission_level"],
        }
        for t in tools
    ]


@app.get("/api/tickets")
async def get_tickets(ticket_id: Optional[str] = None):
    """获取当前员工的 HR 工单列表"""
    emp = get_current_employee()
    adapter = get_hr_adapter()
    return adapter.get_tickets(emp.id, ticket_id)


@app.get("/api/graph")
async def get_graph_topology():
    """获取 LangGraph 状态图拓扑结构定义与 Mermaid 流程图"""
    try:
        from agent.graph import build_workforce_graph
        from config import get_config
        cfg = get_config()
        graph = build_workforce_graph(cfg)
        compiled_graph = graph.get_graph()

        node_metadata = {
            "__start__": {
                "name": "START",
                "label": "用户输入 / 起点",
                "description": "接收用户提问与历史多轮对话，注入系统 Prompt 与员工身份上下文",
                "type": "control"
            },
            "guardrail_check": {
                "name": "guardrail_check",
                "label": "安全护栏 (Guardrails)",
                "description": "输入层意图安全审查、Prompt Injection 拦截、越权刺探与负面情绪感知",
                "type": "control"
            },
            "knowledge_retrieval": {
                "name": "knowledge_retrieval",
                "label": "知识检索 (RAG)",
                "description": "调用向量数据库与本地政策库进行混合语义检索，切片注入 AgentState.retrieved_docs",
                "type": "task"
            },
            "reasoning": {
                "name": "reasoning",
                "label": "决策推理 (LLM)",
                "description": "基于上下文与检索切片进行思考，判断是直接生成答复还是调用工具",
                "type": "task"
            },
            "tool_execution": {
                "name": "tool_execution",
                "label": "工具执行 (Tools)",
                "description": "分发执行具体企业工具（假期、差旅预算、工单申请等），生成 ToolMessage 回传",
                "type": "task"
            },
            "hitl_gate": {
                "name": "hitl_gate",
                "label": "人机协同门禁 (HITL)",
                "description": "高风险写操作拦截挂起，生成结构化交互卡片等待员工核对与人工授权 (Approve/Reject)",
                "type": "control"
            },
            "__end__": {
                "name": "END",
                "label": "回复完成 / 终点",
                "description": "结束状态机流转，流式输出完成并归档到会话历史",
                "type": "control"
            }
        }

        nodes = []
        for n in compiled_graph.nodes.values():
            meta = node_metadata.get(n.id, {})
            nodes.append({
                "id": n.id,
                "label": meta.get("label", n.id),
                "description": meta.get("description", ""),
                "type": meta.get("type", "task"),
            })
        # 补充前置安全护栏与人机协同门禁节点，确保架构拓扑完整反映控制链路
        if not any(node["id"] == "guardrail_check" for node in nodes):
            nodes.insert(1, {
                "id": "guardrail_check",
                "label": node_metadata["guardrail_check"]["label"],
                "description": node_metadata["guardrail_check"]["description"],
                "type": "control",
            })
        if not any(node["id"] == "hitl_gate" for node in nodes):
            nodes.insert(-1, {
                "id": "hitl_gate",
                "label": node_metadata["hitl_gate"]["label"],
                "description": node_metadata["hitl_gate"]["description"],
                "type": "control",
            })

        edges = []
        for e in compiled_graph.edges:
            edges.append({
                "source": e.source,
                "target": e.target,
                "conditional": getattr(e, "conditional", False)
            })
        # 补充 HITL 与 Guardrails 拓扑边
        edges.append({"source": "tool_execution", "target": "hitl_gate", "conditional": True, "label": "写操作门禁挂起"})
        edges.append({"source": "hitl_gate", "target": "tool_execution", "conditional": True, "label": "人工授权执行"})
        edges.append({"source": "hitl_gate", "target": "__end__", "conditional": True, "label": "撤销/放弃"})

        mermaid_str = (
            "graph TD;\n"
            "  __start__([START]):::first --> guardrail_check;\n"
            "  guardrail_check -->|合规放行| knowledge_retrieval;\n"
            "  guardrail_check -.->|快速短路| __end__;\n"
            "  knowledge_retrieval --> reasoning;\n"
            "  reasoning -.->|直接答复| __end__;\n"
            "  reasoning -.->|调用工具| tool_execution;\n"
            "  tool_execution -->|只读结果回流| reasoning;\n"
            "  tool_execution -.->|写操作门禁挂起| hitl_gate;\n"
            "  hitl_gate -.->|人工授权执行| tool_execution;\n"
            "  hitl_gate -.->|取消/放弃| __end__;\n"
            "  classDef first fill:#064e3b,stroke:#059669,stroke-width:2px,color:#a7f3d0;\n"
            "  classDef hitl fill:#451a03,stroke:#d97706,stroke-width:2px,color:#fde68a;\n"
            "  class hitl_gate hitl;"
        )

        return {
            "nodes": nodes,
            "edges": edges,
            "mermaid": mermaid_str,
            "state_schema": {
                "messages": "Annotated[Sequence[BaseMessage], add_messages]",
                "retrieved_docs": "List[Dict[str, Any]]",
                "emotion_instruction": "Optional[str]",
                "hitl_confirmed": "Optional[Dict[str, Any]]"
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate graph topology: {e}", exc_info=True)
        return {
            "error": str(e),
            "nodes": [],
            "edges": [],
            "mermaid": ""
        }



@app.post("/api/config")
async def update_llm_config(req: ConfigUpdate):
    """更新 LLM 配置"""
    update_config(req.config)
    return {"status": "ok", "message": "配置已更新"}


@app.get("/api/config")
async def get_llm_config():
    """获取当前 LLM 配置（隐藏 API Key）"""
    cfg = get_config()
    return {
        "base_url": cfg.base_url,
        "api_key": "***" if cfg.api_key else "",
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "has_api_key": bool(cfg.api_key),
    }


@app.get("/api/cache/stats")
async def get_cache_statistics():
    """获取 Redis 缓存统计与状态"""
    return get_cache_stats()


@app.post("/api/cache/clear")
async def clear_cache_endpoint():
    """清空项目相关的 Redis 缓存"""
    deleted = clear_cache()
    return {"status": "ok", "deleted_keys": deleted}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    聊天接口（流式 SSE）
    
    返回 Server-Sent Events 流，事件类型：
    - thinking: 思考中
    - tool_call: 工具调用
    - tool_result: 工具结果
    - token: 文本 token
    - message_complete: 消息完成
    - error: 错误
    - status: 状态变化
    - node_enter/exit: 节点进入/退出
    """
    logger.info(f"💬 收到聊天请求: {req.message[:100]}...")
    
    # 更新配置（如果请求中提供了）
    if req.config:
        logger.info("🔄 更新 LLM 配置")
        update_config(req.config)
        
        # 记录配置信息
        cfg = get_config()
        logger.info(f"📋 LLM 配置:")
        logger.info(f"   - Base URL: {cfg.base_url}")
        logger.info(f"   - Model: {cfg.model}")
        logger.info(f"   - Temperature: {cfg.temperature}")
        logger.info(f"   - Max Tokens: {cfg.max_tokens}")
        logger.info(f"   - API Key: {'已配置' if cfg.api_key else '未配置'}")

    cfg = get_config()
    current_model = (req.config.model if req.config and req.config.model else None) or cfg.model

    # 尝试命中 Redis 问答缓存（若启用 force_refresh 或包含 HITL 确认执行载荷则直接绕过）
    if req.force_refresh or req.hitl_confirmed:
        logger.info(f"🔄 [跳过缓存] force_refresh={req.force_refresh}, hitl_confirmed={bool(req.hitl_confirmed)}: '{req.message[:50]}'")
        cached_item = None
    else:
        cached_item = get_cached_response(req.message, model=current_model)

    if cached_item:
        cached_text = cached_item.get("content", "")
        cached_tools = cached_item.get("tool_calls", [])
        cached_results = cached_item.get("tool_results", [])
        logger.info(f"⚡ [Redis 秒回] 命中缓存: '{req.message[:50]}' (共 {len(cached_text)} 字)")

        async def cached_event_stream():
            # 状态流转符合前端 GraphInspector & ChatInterface 期望
            yield f"data: {json.dumps({'type': 'status', 'content': 'thinking'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'node_enter', 'content': 'knowledge_retrieval'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'node_exit', 'content': 'knowledge_retrieval'}, ensure_ascii=False)}\n\n"

            # 如果存在工具调用，触发工具调用与执行节点事件
            if cached_tools:
                yield f"data: {json.dumps({'type': 'status', 'content': 'tool_calling'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'node_enter', 'content': 'tool_execution'}, ensure_ascii=False)}\n\n"
                for tc in cached_tools:
                    yield f"data: {json.dumps({'type': 'tool_call', 'data': tc}, ensure_ascii=False)}\n\n"
                for tr in cached_results:
                    yield f"data: {json.dumps({'type': 'tool_result', 'data': tr}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'node_exit', 'content': 'tool_execution'}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'status', 'content': 'responding'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'node_enter', 'content': 'response_generation'}, ensure_ascii=False)}\n\n"

            # 快速切片流式推送（每块15字，间隔10ms，兼顾打字动效与极速秒回）
            chunk_size = 15
            for i in range(0, len(cached_text), chunk_size):
                chunk = cached_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

            yield f"data: {json.dumps({'type': 'node_exit', 'content': 'response_generation'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'message_complete', 'content': cached_text, 'cached': True}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'status', 'content': 'idle'}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            cached_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Cache": "HIT",
            },
        )

    # 创建 Agent 引擎
    engine = AgentEngine()
    if req.history:
        for item in req.history:
            if isinstance(item, dict) and item.get("role") and item.get("content"):
                engine.conversation_history.append({
                    "role": item["role"],
                    "content": item["content"],
                })

    async def event_stream():
        full_content = ""
        tools_called = []
        captured_tool_calls = []
        captured_tool_results = []
        has_hitl_request = False
        try:
            async for event in engine.run(req.message, hitl_confirmed=req.hitl_confirmed):
                ev_type = event.get("type")
                if ev_type == "tool_call":
                    tool_data = event.get("data", {})
                    captured_tool_calls.append(tool_data)
                    t_name = tool_data.get("name", "")
                    if t_name:
                        tools_called.append(t_name)
                elif ev_type == "tool_result":
                    tool_res_data = event.get("data", {})
                    captured_tool_results.append(tool_res_data)
                    t_name = tool_res_data.get("tool_name", "")
                    if t_name and tool_res_data.get("success", True):
                        # Evict-on-Write: 业务写操作成功时主动淘汰相关关联动态缓存
                        evicted = invalidate_cache_on_write(t_name)
                        if evicted > 0:
                            logger.info(f"🧹 [Evict-on-Write] 写操作 '{t_name}' 成功执行，已联动淘汰 {evicted} 条陈旧缓存")
                elif ev_type == "hitl_request":
                    has_hitl_request = True
                    logger.info(f"🛡️ [HITL Push] 捕获人机协同事件，向前端推送结构化交互确认卡片: {event.get('data', {}).get('title')}")
                elif ev_type == "message_complete":
                    full_content = event.get("content", "")

                # 格式化为 SSE
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 正常完成且非 HITL 门禁挂起卡片状态时，将结果缓存入 Redis
            if full_content and not has_hitl_request and not req.hitl_confirmed:
                set_cached_response(
                    question=req.message,
                    content=full_content,
                    model=current_model,
                    tools_used=tools_called,
                    tool_calls=captured_tool_calls,
                    tool_results=captured_tool_results,
                )
        except Exception as e:
            logger.error(f"💥 聊天处理错误: {type(e).__name__}: {e}")
            logger.exception("完整异常堆栈:")
            error_event = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Cache": "MISS",
        },
    )


@app.post("/api/hitl/action")
async def handle_hitl_action(req: HitlDecisionRequest):
    """
    处理原生 HITL (Human-in-the-Loop) 交互卡片操作决策（确认提交 / 取消放弃）
    """
    logger.info(f"🛡️ [HITL Action] 收到卡片决策: {req.decision} | 工具: {req.tool_name} | ID: {req.action_id}")

    if req.decision == "reject":
        return {
            "success": True,
            "status": "rejected",
            "message": "已成功取消该申请操作，未对系统数据产生变更。",
            "action_id": req.action_id,
        }

    # 执行确认写操作
    tool = registry.get(req.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"未找到对应业务工具: {req.tool_name}")

    start_t = asyncio.get_event_loop().time()
    result = await registry.execute(req.tool_name, req.arguments)
    duration = asyncio.get_event_loop().time() - start_t

    if result.success:
        evicted = invalidate_cache_on_write(req.tool_name)
        if evicted > 0:
            logger.info(f"🧹 [HITL Action] 写操作 '{req.tool_name}' 成功执行，已淘汰 {evicted} 条缓存")
        return {
            "success": True,
            "status": "approved",
            "action_id": req.action_id,
            "tool_name": req.tool_name,
            "data": result.data,
            "execution_time": round(duration, 3),
        }
    else:
        logger.error(f"❌ [HITL Action] 写操作 '{req.tool_name}' 执行失败: {result.error}")
        return {
            "success": False,
            "status": "failed",
            "action_id": req.action_id,
            "tool_name": req.tool_name,
            "error": result.error or "执行失败",
        }



# ============ Run Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
