// ============================================================
// Workforce Operations Agent - Type Definitions
// ============================================================

export interface AppConfig {
  backendUrl: string;    // 本地 FastAPI 后端地址
  llmBaseUrl: string;    // LLM API 服务地址
  apiKey: string;        // LLM API Key
  model: string;
  temperature: number;
  maxTokens: number;
}

// --- Chat Types ---
export interface ExecutionStep {
  id: string;
  node: string;
  timestamp: number;
  duration?: number;
  status: 'running' | 'completed' | 'failed';
  summary?: string;
  toolCall?: ToolCallInfo;
  toolResult?: ToolResultInfo;
  details?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  toolCalls?: ToolCallInfo[];
  toolResults?: ToolResultInfo[];
  executionTrace?: ExecutionStep[];
  cached?: boolean;
}

// --- Tool Types ---
export interface ToolInfo {
  name: string;
  description: string;
  category: string;
  permission_level: string;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

// --- Graph Topology Types ---
export interface GraphNode {
  id: string;
  label: string;
  description: string;
  type: 'control' | 'task';
}

export interface GraphEdge {
  source: string;
  target: string;
  conditional?: boolean;
}

export interface GraphTopology {
  nodes: GraphNode[];
  edges: GraphEdge[];
  mermaid?: string;
  state_schema?: Record<string, string>;
}

export interface ToolResultInfo {
  tool_name: string;
  success: boolean;
  data: unknown;
  error?: string;
  execution_time: number;
}

// --- SSE Event Types ---
export type AgentEvent =
  | { type: 'token'; content: string }
  | { type: 'tool_call'; data: ToolCallInfo }
  | { type: 'tool_result'; data: ToolResultInfo }
  | { type: 'message_complete'; content: string; cached?: boolean }
  | { type: 'error'; content: string }
  | { type: 'status'; content: string }
  | { type: 'node_enter'; content: string }
  | { type: 'node_exit'; content: string };

// --- Employee Types ---
export interface EmployeeProfile {
  id: string;
  name: string;
  department: string;
  position: string;
  level: string;
  location: string;
  manager: string;
  leave_balance: {
    annual: number;
    sick: number;
    personal: number;
  };
}
