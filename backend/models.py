"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ============ LLM 相关 ============

class Message(BaseModel):
    """聊天消息"""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ToolCall(BaseModel):
    """工具调用"""
    id: str
    type: str = "function"
    function: Dict[str, Any]


# ============ Agent 相关 ============

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    config: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应（非流式）"""
    message: str
    tool_calls: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []


# ============ Tool 相关 ============

class ToolParameter(BaseModel):
    """工具参数定义"""
    type: str
    description: str
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: Literal["query", "action", "notification"]
    permission_level: Literal["autonomous", "confirmation", "restricted"]


class ToolResult(BaseModel):
    """工具执行结果"""
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0


# ============ Employee 相关 ============

class LeaveBalance(BaseModel):
    """假期余额"""
    annual: int
    sick: int
    personal: int


class EmployeeProfile(BaseModel):
    """员工档案"""
    id: str
    name: str
    department: str
    position: str
    level: str
    location: str
    manager: str
    hire_date: str
    contract_type: str
    leave_balance: LeaveBalance
    benefits: List[str]


# ============ Knowledge 相关 ============

class PolicyDocument(BaseModel):
    """政策文档"""
    id: str
    title: str
    category: str
    content: str
    effective_date: str
    applicable_to: List[str]


class KnowledgeChunk(BaseModel):
    """知识片段"""
    doc_id: str
    title: str
    content: str
    score: float
    category: str


# ============ SSE Event ============

class AgentEvent(BaseModel):
    """Agent 事件"""
    type: Literal[
        "thinking",
        "tool_call",
        "tool_result",
        "token",
        "message_complete",
        "error",
        "status",
        "node_enter",
        "node_exit",
    ]
    content: Optional[str] = None
    data: Optional[Any] = None
