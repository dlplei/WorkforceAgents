import React from 'react';
import { Play, BookOpen, Brain, Wrench, CheckCircle2 } from 'lucide-react';

export interface NodeMeta {
  name: string;
  label: string;
  subLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  borderColor: string;
  glowColor: string;
  description: string;
  handler: string;
  category: 'control' | 'task';
}

export const NODE_DEFINITIONS: Record<string, NodeMeta> = {
  __start__: {
    name: '__start__',
    label: 'START 起点',
    subLabel: '输入与上下文注入',
    icon: Play,
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/40',
    glowColor: 'shadow-emerald-500/20',
    description: '接收用户提问与历史多轮对话，注入系统 Prompt 与员工身份上下文 (张明 E10293)。',
    handler: 'LangGraph START Node',
    category: 'control',
  },
  knowledge_retrieval: {
    name: 'knowledge_retrieval',
    label: '知识检索 (RAG)',
    subLabel: '向量/关键词混合检索',
    icon: BookOpen,
    color: 'text-cyan-400',
    borderColor: 'border-cyan-500/50',
    glowColor: 'shadow-cyan-500/30',
    description: '调用 Chroma 密集向量库 (Ollama BGE-M3) 与本地政策切片进行混合语义检索，切片注入 AgentState.retrieved_docs。',
    handler: 'knowledge_retrieval_node(state)',
    category: 'task',
  },
  reasoning: {
    name: 'reasoning',
    label: '决策推理 (LLM)',
    subLabel: 'ReAct 规划与工具决策',
    icon: Brain,
    color: 'text-purple-400',
    borderColor: 'border-purple-500/50',
    glowColor: 'shadow-purple-500/30',
    description: 'LLM 结合政策切片与历史进行逻辑推理，通过 Tool Calling 机制自主决策是调用 HR 业务工具还是直接生成答复。',
    handler: 'create_reasoning_node(config)(state)',
    category: 'task',
  },
  tool_execution: {
    name: 'tool_execution',
    label: '工具执行 (Tools)',
    subLabel: '适配层与业务工具分发',
    icon: Wrench,
    color: 'text-amber-400',
    borderColor: 'border-amber-500/50',
    glowColor: 'shadow-amber-500/30',
    description: '执行 9 个自主/确认型业务工具（年假查询、差旅预算、工单创建、证明开具等），将 ToolMessage 结果回传状态机。',
    handler: 'tool_execution_node(state)',
    category: 'task',
  },
  __end__: {
    name: '__end__',
    label: 'END 终点',
    subLabel: '流式结束与历史归档',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/40',
    glowColor: 'shadow-emerald-500/20',
    description: '状态机流转终点，完成本轮流式 token 推送，并更新 Conversation History 供下一轮调用。',
    handler: 'LangGraph END Node',
    category: 'control',
  },
};
