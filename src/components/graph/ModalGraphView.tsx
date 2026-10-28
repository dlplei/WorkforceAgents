import React from 'react';
import { Workflow, Sparkles, Code2, Copy, Check, X } from 'lucide-react';
import InteractiveGraphSvg from './InteractiveGraphSvg';

interface Props {
  activeNode: string;
  isRunning: boolean;
  selectedNode: string;
  onSelectNode: (node: string) => void;
  nodeVisitCounts: Record<string, number>;
  copiedMermaid: boolean;
  onCopyMermaid: () => void;
  onClose: () => void;
}

export default function ModalGraphView({
  activeNode,
  isRunning,
  selectedNode,
  onSelectNode,
  nodeVisitCounts,
  copiedMermaid,
  onCopyMermaid,
  onClose,
}: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/60 bg-slate-800/80">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <Workflow className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">LangGraph 状态图全景架构</h3>
              <p className="text-xs text-slate-400">Workforce Operations Agent 状态机与反馈回路设计</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={onCopyMermaid}
              className="flex items-center space-x-1 px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-colors"
            >
              {copiedMermaid ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedMermaid ? '已复制' : '复制 Mermaid'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="bg-slate-950/60 rounded-xl border border-slate-800/80 p-6 flex flex-col items-center justify-center">
            <InteractiveGraphSvg
              activeNode={activeNode}
              isRunning={isRunning}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
              nodeVisitCounts={nodeVisitCounts}
              large
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 space-y-2">
              <div className="text-xs font-semibold text-cyan-400 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                <span>状态循环机理 (Conditional Edges)</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                在 <code className="text-purple-300 font-mono">reasoning</code> 节点后，通过条件路由函数{' '}
                <code className="text-cyan-300 font-mono">should_continue</code> 检查大模型输出是否含有{' '}
                <code className="text-amber-300 font-mono">tool_calls</code>：
              </p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                <li>
                  若包含工具调用 ➔ 跃迁至 <span className="text-amber-300">tool_execution</span> 执行，并将执行结果作为 ToolMessage 回流回 reasoning。
                </li>
                <li>
                  若无需工具调用 ➔ 直接流向 <span className="text-emerald-400">END</span> 节点，生成最终答复。
                </li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 space-y-2">
              <div className="text-xs font-semibold text-purple-400 flex items-center space-x-1.5">
                <Code2 className="w-3.5 h-3.5" />
                <span>LangGraph 官方标准事件映射</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                底层采用 <code className="text-cyan-300 font-mono">graph.astream_events(version="v2")</code> 全双工监听：
              </p>
              <div className="text-xs font-mono text-slate-400 bg-slate-900/80 p-2.5 rounded border border-slate-800 space-y-1">
                <div>on_chain_start ➔ node_enter</div>
                <div>on_chain_end ➔ node_exit</div>
                <div>on_custom_event(tool_call) ➔ 工具动态卡片</div>
                <div>on_chat_model_stream ➔ Token 实时打字机</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
