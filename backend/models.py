"""
数据模型定义
"""
from pydantic import BaseModel, Field, model_validator
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


# ============ HITL (Human-in-the-Loop) 相关 ============

class HitlActionRequest(BaseModel):
    """人机协同 (Human-in-the-Loop) 待确认动作请求"""
    action_id: str
    tool_name: str
    tool_call_id: Optional[str] = None
    title: str
    category: Literal["leave", "document", "ticket", "travel", "transfer", "general"] = "general"
    summary: Dict[str, Any] = Field(default_factory=dict)
    raw_arguments: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "approved", "rejected"] = "pending"
    risk_level: Literal["low", "medium", "high"] = "medium"
    created_at: int



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

    def __getitem__(self, item: str):
        return getattr(self, item)


class ApprovalActionRequest(BaseModel):
    """主管处理审批单请求"""
    decision: Literal["approved", "rejected"]
    comment: Optional[str] = "已阅，同意"

    @model_validator(mode="before")
    @classmethod
    def normalize_decision(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw = data.get("decision") or data.get("action")
            if raw in ("approve", "approved", "agree", "pass"):
                data["decision"] = "approved"
            elif raw in ("reject", "rejected", "refuse", "deny"):
                data["decision"] = "rejected"
        return data


class ApprovalActionResponse(BaseModel):
    """主管处理审批单响应"""
    success: bool
    message: str
    approval: Dict[str, Any]
    leave_balance_deducted: Optional[Dict[str, Any]] = None




class HRTicket(BaseModel):
    """HR 服务工单"""
    id: str
    employee_id: str
    applicant: str
    category: str
    title: str
    description: str
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None
    external_system_id: Optional[str] = None


class DocumentRecord(BaseModel):
    """人事证明申请记录"""
    id: str
    employee_id: str
    applicant: str
    doc_type: str
    purpose: str
    language: str = "中文"
    status: str = "processing"
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessageRecord(BaseModel):
    """会话历史持久化记录"""
    id: str
    session_id: str
    employee_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
