import React from 'react';
import { Database, Code2, Workflow, Check, Copy } from 'lucide-react';
import type { AppConfig, GraphTopology } from '../../types';

interface Props {
  topology: GraphTopology | null;
  copiedMermaid: boolean;
  onCopyMermaid: () => void;
  config: AppConfig;
}

export default function StateView({
  topology,
  copiedMermaid,
  onCopyMermaid,
  config,
}: Props) {
  const defaultMermaid = `graph TD;
  __start__([START]):::first --> knowledge_retrieval;
  knowledge_retrieval --> reasoning;
  reasoning -.-> __end__;
  reasoning -.-> tool_execution;
  tool_execution --> reasoning;`;

  return (
    <div className="space-y-3">
      {/* 状态定义 TypedDict */}
      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-2">
        <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span>LangGraph 状态架构 (AgentState)</span>
        </div>
        <p className="text-[11px] text-slate-400">
          基于 Python <code className="text-cyan-300 font-mono">TypedDict</code> 强类型定义，负责贯穿整个状态机的全局记忆：
        </p>

        <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1.5">
          <div>
            <span className="text-purple-400">messages:</span>{' '}
            <span className="text-slate-400">Annotated[Sequence[BaseMessage], add_messages]</span>
            <div className="text-[10px] text-slate-500 pl-2">包含 HumanMessage, AIMessage, ToolMessage 累积队列</div>
          </div>
          <div>
            <span className="text-purple-400">retrieved_docs:</span>{' '}
            <span className="text-slate-400">List[Dict[str, Any]]</span>
            <div className="text-[10px] text-slate-500 pl-2">RAG 混合检索召回的政策分片（标题、来源、相似度）</div>
          </div>
        </div>
      </div>

      {/* 运行时参数 */}
      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-2">
        <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
          <Code2 className="w-3.5 h-3.5 text-purple-400" />
          <span>运行时环境配置</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">编排驱动引擎</span>
            <span className="text-slate-200 font-mono">LangGraph 0.2+</span>
          </div>
          <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">事件协议</span>
            <span className="text-slate-200 font-mono">astream_events v2</span>
          </div>
          <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">当前模型</span>
            <span className="text-slate-200 font-mono truncate block">{config.model}</span>
          </div>
          <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">温度系数</span>
            <span className="text-slate-200 font-mono">{config.temperature}</span>
          </div>
        </div>
      </div>

      {/* Mermaid 流程图源码 */}
      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-2">
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
            <Workflow className="w-3.5 h-3.5 text-cyan-400" />
            <span>Mermaid 拓扑定义</span>
          </div>
          <button
            onClick={onCopyMermaid}
            className="flex items-center space-x-1 px-2 py-1 text-[11px] bg-slate-700/60 hover:bg-slate-700 text-slate-300 rounded transition-colors"
          >
            {copiedMermaid ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
            <span>{copiedMermaid ? '已复制' : '复制'}</span>
          </button>
        </div>
        <pre className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[10px] text-cyan-300 overflow-x-auto whitespace-pre">
          {topology?.mermaid || defaultMermaid}
        </pre>
      </div>
    </div>
  );
}
