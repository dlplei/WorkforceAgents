// ============================================================
// Workforce Operations Agent - Type Definitions
// ============================================================

// --- LLM Configuration ---
export interface LLMConfig {
  baseUrl: string;
  apiKey: string;
  model: string;
  embeddingModel: string;
  temperature: number;
  maxTokens: number;
}

// --- Agent Types ---
export type AgentNodeType =
  | 'intent_recognition'
  | 'context_loading'
  | 'knowledge_retrieval'
  | 'reasoning'
  | 'tool_execution'
  | 'response_generation'
  | 'memory_update';

export interface AgentState {
  messages: ChatMessage[];
  currentIntent: string | null;
  employeeContext: EmployeeProfile | null;
  retrievedKnowledge: KnowledgeChunk[];
  toolResults: ToolResult[];
  thinking: string;
  status: 'idle' | 'thinking' | 'tool_calling' | 'responding' | 'error';
  iteration: number;
  maxIterations: number;
}

// --- Chat Types ---
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  thinking?: string;
  toolCalls?: ToolCallInfo[];
  toolCallId?: string;
  name?: string;
  isStreaming?: boolean;
}

// --- Tool Types ---
export interface ToolHandlerResult {
  success: boolean;
  data: unknown;
  error?: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: JSONSchema;
  category: 'query' | 'action' | 'notification';
  permissionLevel: 'autonomous' | 'confirmation' | 'restricted';
  handler: (params: Record<string, unknown>) => Promise<ToolHandlerResult>;
}

export interface JSONSchema {
  type: string;
  properties?: Record<string, {
    type: string;
    description: string;
    enum?: string[];
    items?: unknown;
  }>;
  required?: string[];
}

export interface ToolCallInfo {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ToolResult {
  toolName: string;
  success: boolean;
  data: unknown;
  error?: string;
  executionTime: number;
}

// --- Employee Types ---
export interface EmployeeProfile {
  id: string;
  name: string;
  department: string;
  position: string;
  level: string;
  location: string;
  manager: string;
  hireDate: string;
  contractType: string;
  leaveBalance: {
    annual: number;
    sick: number;
    personal: number;
  };
  benefits: string[];
}

// --- Knowledge Types ---
export interface PolicyDocument {
  id: string;
  title: string;
  category: string;
  content: string;
  effectiveDate: string;
  applicableTo: string[];
  embedding?: number[];
}

export interface KnowledgeChunk {
  docId: string;
  title: string;
  content: string;
  score: number;
  category: string;
}

// --- Event Types (for streaming UI) ---
export type AgentEvent =
  | { type: 'thinking'; content: string }
  | { type: 'tool_call'; toolCall: ToolCallInfo }
  | { type: 'tool_result'; result: ToolResult }
  | { type: 'token'; content: string }
  | { type: 'message_complete'; message: ChatMessage }
  | { type: 'error'; error: string }
  | { type: 'status'; status: AgentState['status'] }
  | { type: 'node_enter'; node: AgentNodeType }
  | { type: 'node_exit'; node: AgentNodeType };
