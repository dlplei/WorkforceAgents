import React from 'react';
import type { ToolCallInfo, ToolResultInfo, ExecutionStep } from '../../types';
import { NODE_DEFINITIONS, type NodeMeta } from './nodeMeta';
import InteractiveGraphSvg from './InteractiveGraphSvg';

interface Props {
  activeNode: string;
  isRunning: boolean;
  selectedNode: string;
  onSelectNode: (node: string) => void;
  nodeVisitCounts: Record<string, number>;
  selectedNodeInfo: NodeMeta;
  currentToolCalls: ToolCallInfo[];
  currentToolResults: ToolResultInfo[];
  traceSteps: ExecutionStep[];
}

export default function TopologyView({
  activeNode,
  isRunning,
  selectedNode,
  onSelectNode,
  nodeVisitCounts,
  selectedNodeInfo,
  currentToolCalls,
  traceSteps,
}: Props) {
  return (
    <div className="space-y-3">
      {/* 实时状态提示条 */}
      <div
        className={`p-2.5 rounded-lg border text-xs transition-all ${
          isRunning
            ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-200'
            : traceSteps.length > 0
            ? 'bg-slate-800/60 border-slate-700/50 text-slate-300'
            : 'bg-slate-800/30 border-slate-700/30 text-slate-400'
        }`}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium flex items-center space-x-1.5">
            <span
              className={`w-2 h-2 rounded-full ${isRunning ? 'bg-cyan-400 animate-ping' : 'bg-slate-500'}`}
            />
            <span>
              {isRunning
                ? `当前运行: ${NODE_DEFINITIONS[activeNode]?.label || activeNode || '思考中'}`
                : traceSteps.length > 0
                ? '✓ 本轮工作流执行完毕'
                : '就绪，等待提问以启动状态图'}
            </span>
          </span>
          {isRunning && <span className="text-[10px] text-cyan-400 font-mono animate-pulse">流转中</span>}
        </div>
        {isRunning && currentToolCalls.length > 0 && (
          <div className="text-[11px] text-amber-300 font-mono mt-1 truncate">
            🔧 调用工具: {currentToolCalls[currentToolCalls.length - 1].name}
          </div>
        )}
      </div>

      {/* 交互式 SVG 拓扑图 */}
      <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-3 flex flex-col items-center justify-center relative overflow-hidden shadow-inner">
        <InteractiveGraphSvg
          activeNode={activeNode}
          isRunning={isRunning}
          selectedNode={selectedNode}
          onSelectNode={onSelectNode}
          nodeVisitCounts={nodeVisitCounts}
        />
        <div className="text-[10px] text-slate-500 mt-2 text-center">
          点击节点可查看详情与 LangGraph 运行时职责
        </div>
      </div>

      {/* 选中节点详情卡片 */}
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div
              className={`w-6 h-6 rounded-md bg-slate-800 border ${selectedNodeInfo.borderColor} flex items-center justify-center`}
            >
              <selectedNodeInfo.icon className={`w-3.5 h-3.5 ${selectedNodeInfo.color}`} />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">{selectedNodeInfo.label}</div>
              <div className="text-[10px] text-slate-400">{selectedNodeInfo.subLabel}</div>
            </div>
          </div>
          {nodeVisitCounts[selectedNodeInfo.name] ? (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-700/60 text-slate-300 font-mono">
              本轮被执行 {nodeVisitCounts[selectedNodeInfo.name]} 次
            </span>
          ) : (
            <span className="text-[10px] text-slate-500">未触发</span>
          )}
        </div>

        <p className="text-[11px] text-slate-300 leading-relaxed bg-slate-900/60 p-2 rounded border border-slate-800">
          {selectedNodeInfo.description}
        </p>

        <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between pt-1">
          <span>Handler:</span>
          <span className="text-cyan-400 truncate max-w-[200px]">{selectedNodeInfo.handler}</span>
        </div>
      </div>
    </div>
  );
}
