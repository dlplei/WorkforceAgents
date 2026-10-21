"""
Workforce Operations Agent - FastAPI Backend
"""
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import LLMConfig, update_config, get_config
from agent.engine import AgentEngine
from agent.tools import registry
from mock_data import get_current_employee

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

app = FastAPI(
    title="Workforce Operations Agent",
    description="智能员工服务与人力运营 Agent API",
    version="0.1.0",
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("🚀 Workforce Operations Agent 启动中...")
    logger.info("=" * 60)
    logger.info(f"📦 已注册工具数量: {len(registry.get_all())}")
    for tool in registry.get_all():
        logger.info(f"   - {tool['name']}: {tool['description'][:50]}...")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 Workforce Operations Agent 已关闭")


# ============ Request/Response Models ============

class ChatRequest(BaseModel):
    message: str
    config: Optional[LLMConfig] = None


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

    # 创建 Agent 引擎
    engine = AgentEngine()

    async def event_stream():
        try:
            async for event in engine.run(req.message):
                # 格式化为 SSE
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
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
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


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
