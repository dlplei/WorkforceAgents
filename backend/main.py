"""
Workforce Operations Agent - FastAPI Backend
"""
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import LLMConfig, update_config, get_config
from agent.engine import AgentEngine
from agent.tools import registry
from mock_data import get_current_employee


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
    # 更新配置（如果请求中提供了）
    if req.config:
        update_config(req.config)

    # 创建 Agent 引擎
    engine = AgentEngine()

    async def event_stream():
        try:
            async for event in engine.run(req.message):
                # 格式化为 SSE
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
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
    )
