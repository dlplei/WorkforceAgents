import React, { useState, useEffect, useMemo } from 'react';
import {
  Workflow,
  Clock,
  Activity,
  Maximize2,
  Database,
  X,
} from 'lucide-react';
import type { AppConfig, ExecutionStep, ToolCallInfo, ToolResultInfo, GraphTopology } from '../types';
import { NODE_DEFINITIONS } from './graph/nodeMeta';
import TopologyView from './graph/TopologyView';
import TraceView from './graph/TraceView';
import StateView from './graph/StateView';
import ModalGraphView from './graph/ModalGraphView';

export interface GraphInspectorProps {
  activeNode: string;
  isRunning: boolean;
  traceSteps?: ExecutionStep[];
  currentToolCalls?: ToolCallInfo[];
  currentToolResults?: ToolResultInfo[];
  onClose?: () => void;
  config?: AppConfig;
}

export default function GraphInspector({
  activeNode,
  isRunning,
  traceSteps = [],
  currentToolCalls = [],
  currentToolResults = [],
  onClose,
  config,
}: GraphInspectorProps) {
  const [activeTab, setActiveTab] = useState<'topology' | 'trace' | 'state'>('topology');
  const [selectedNode, setSelectedNode] = useState<string>('reasoning');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [copiedMermaid, setCopiedMermaid] = useState(false);
  const [topology, setTopology] = useState<GraphTopology | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const base = (config?.backendUrl || '').replace(/\/+$/, '');
        const res = await fetch(`${base}/api/graph`);
        if (res.ok) {
          const data: GraphTopology = await res.json();
          if (data && data.nodes && data.nodes.length > 0) {
            setTopology(data);
          }
        }
      } catch (e) {
        console.warn('Using default topology layout', e);
      }
    };
    fetchTopology();
  }, [config?.backendUrl]);

  useEffect(() => {
    if (activeNode && NODE_DEFINITIONS[activeNode]) {
      setSelectedNode(activeNode);
    }
  }, [activeNode]);

  const nodeVisitCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const step of traceSteps) {
      counts[step.node] = (counts[step.node] || 0) + 1;
    }
    return counts;
  }, [traceSteps]);

  const totalExecutionTime = useMemo(() => {
    if (!traceSteps.length) return 0;
    const start = traceSteps[0].timestamp;
    const last = traceSteps[traceSteps.length - 1];
    return Math.max(0, (last.timestamp + (last.duration || 0)) - start);
  }, [traceSteps]);

  const handleCopyMermaid = () => {
    const mermaidCode =
      topology?.mermaid ||
      `graph TD;
  __start__([START]):::first --> knowledge_retrieval;
  knowledge_retrieval --> reasoning;
  reasoning -.-> __end__;
  reasoning -.-> tool_execution;
  tool_execution --> reasoning;`;
    navigator.clipboard.writeText(mermaidCode);
    setCopiedMermaid(true);
    setTimeout(() => setCopiedMermaid(false), 2000);
  };

  const toggleStepExpand = (stepId: string) => {
    setExpandedSteps(prev => ({ ...prev, [stepId]: !prev[stepId] }));
  };

  const selectedNodeInfo = NODE_DEFINITIONS[selectedNode] || NODE_DEFINITIONS.reasoning;

  return (
    <>
      <aside className="w-80 sm:w-96 flex-shrink-0 flex flex-col border-l border-slate-700/60 bg-slate-900/95 backdrop-blur-md h-full transition-all duration-200 select-none">
        {/* Header */}
        <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-slate-700/60 bg-slate-800/60">
          <div className="flex items-center space-x-2 min-w-0">
            <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center flex-shrink-0">
              <Workflow className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-semibold text-white tracking-wide truncate">LangGraph 状态机</span>
                {isRunning ? (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 animate-pulse">
                    运行中
                  </span>
                ) : traceSteps.length > 0 ? (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    已就绪
                  </span>
                ) : (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-700/50 text-slate-400">
                    等待提问
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-1 flex-shrink-0">
            <button
              onClick={() => setIsModalOpen(true)}
              className="p-1 text-slate-400 hover:text-white hover:bg-slate-700/60 rounded transition-colors"
              title="全屏放大查看流程图"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 text-slate-400 hover:text-white hover:bg-slate-700/60 rounded transition-colors"
                title="折叠面板"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center border-b border-slate-700/50 bg-slate-800/30 px-3 pt-1">
          <button
            onClick={() => setActiveTab('topology')}
            className={`pb-2 px-2 text-xs font-medium border-b-2 transition-colors flex items-center space-x-1.5 ${
              activeTab === 'topology'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3 h-3" />
            <span>拓扑流转</span>
          </button>
          <button
            onClick={() => setActiveTab('trace')}
            className={`pb-2 px-2 text-xs font-medium border-b-2 transition-colors flex items-center space-x-1.5 ${
              activeTab === 'trace'
                ? 'border-purple-400 text-purple-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Clock className="w-3 h-3" />
            <span>执行追踪 ({traceSteps.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('state')}
            className={`pb-2 px-2 text-xs font-medium border-b-2 transition-colors flex items-center space-x-1.5 ${
              activeTab === 'state'
                ? 'border-blue-400 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3 h-3" />
            <span>状态结构</span>
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
          {activeTab === 'topology' && (
            <TopologyView
              activeNode={activeNode}
              isRunning={isRunning}
              selectedNode={selectedNode}
              onSelectNode={setSelectedNode}
              nodeVisitCounts={nodeVisitCounts}
              selectedNodeInfo={selectedNodeInfo}
              currentToolCalls={currentToolCalls}
              currentToolResults={currentToolResults}
              traceSteps={traceSteps}
            />
          )}

          {activeTab === 'trace' && (
            <TraceView
              traceSteps={traceSteps}
              expandedSteps={expandedSteps}
              onToggleExpand={toggleStepExpand}
              totalExecutionTime={totalExecutionTime}
              isRunning={isRunning}
              activeNode={activeNode}
            />
          )}

          {activeTab === 'state' && (
            <StateView
              topology={topology}
              copiedMermaid={copiedMermaid}
              onCopyMermaid={handleCopyMermaid}
              config={config}
            />
          )}
        </div>

        {/* Bottom Status bar */}
        <div className="px-3 py-2 border-t border-slate-700/50 bg-slate-900/80 text-[11px] text-slate-400 flex items-center justify-between">
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span>StateGraph(AgentState)</span>
          </span>
          <span>{traceSteps.length > 0 ? `累计步数: ${traceSteps.length}` : '就绪'}</span>
        </div>
      </aside>

      {isModalOpen && (
        <ModalGraphView
          activeNode={activeNode}
          isRunning={isRunning}
          selectedNode={selectedNode}
          onSelectNode={setSelectedNode}
          nodeVisitCounts={nodeVisitCounts}
          copiedMermaid={copiedMermaid}
          onCopyMermaid={handleCopyMermaid}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
}
