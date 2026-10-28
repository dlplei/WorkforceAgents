import React from 'react';
import { Clock, Activity, ChevronDown, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';
import type { ExecutionStep } from '../../types';
import { NODE_DEFINITIONS } from './nodeMeta';

interface Props {
  traceSteps: ExecutionStep[];
  expandedSteps: Record<string, boolean>;
  onToggleExpand: (stepId: string) => void;
  totalExecutionTime: number;
  isRunning: boolean;
  activeNode: string;
}

export default function TraceView({
  traceSteps,
  expandedSteps,
  onToggleExpand,
  totalExecutionTime,
  isRunning,
  activeNode,
}: Props) {
  if (traceSteps.length === 0) {
    return (
      <div className="py-12 px-4 text-center">
        <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
        <p className="text-xs text-slate-400">暂无执行追踪记录</p>
        <p className="text-[11px] text-slate-500 mt-1">在左侧发送问题后，此处将按时间轴记录每一步跃迁</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 概览统计 */}
      <div className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg border border-slate-700/50 text-xs">
        <span className="text-slate-400">总计耗时</span>
        <span className="font-mono text-cyan-400 font-medium">
          {totalExecutionTime > 0 ? `${(totalExecutionTime / 1000).toFixed(2)}s` : '进行中...'}
        </span>
      </div>

      {/* 时序列表 */}
      <div className="relative pl-4 border-l border-slate-700/60 space-y-3 ml-2">
        {traceSteps.map((step, idx) => {
          const isExpanded = expandedSteps[step.id];
          const nodeDef = NODE_DEFINITIONS[step.node] || {
            label: step.node,
            color: 'text-slate-300',
            icon: Activity,
          };
          const Icon = nodeDef.icon;
          const isCurrentActive = isRunning && activeNode === step.node && idx === traceSteps.length - 1;

          return (
            <div key={step.id} className="relative group">
              {/* 时间轴圆点 */}
              <div
                className={`absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full border ${
                  isCurrentActive
                    ? 'bg-cyan-400 border-cyan-200 animate-ping'
                    : step.status === 'failed'
                    ? 'bg-red-500 border-red-300'
                    : 'bg-slate-700 border-slate-500'
                }`}
              />

              <div className="bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 rounded-lg p-2.5 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 min-w-0">
                    <Icon className={`w-3.5 h-3.5 ${nodeDef.color} flex-shrink-0`} />
                    <span className="text-xs font-medium text-slate-200 truncate">
                      Step {idx + 1}: {nodeDef.label}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {step.duration !== undefined && (
                      <span className="text-[10px] font-mono text-slate-400">
                        {step.duration < 1000 ? `${step.duration}ms` : `${(step.duration / 1000).toFixed(2)}s`}
                      </span>
                    )}
                    {(step.toolCall || step.details) && (
                      <button
                        onClick={() => onToggleExpand(step.id)}
                        className="text-slate-400 hover:text-white p-0.5"
                      >
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {step.summary && (
                  <p className="text-[11px] text-slate-400 mt-1">{step.summary}</p>
                )}

                {/* 工具调用详情展开 */}
                {step.toolCall && (
                  <div className="mt-1.5 text-[11px] font-mono text-amber-300 bg-slate-900/60 p-1.5 rounded border border-slate-800">
                    → {step.toolCall.name}({JSON.stringify(step.toolCall.arguments)})
                  </div>
                )}

                {/* 工具执行结果 */}
                {step.toolResult && (
                  <div
                    className={`mt-1 text-[11px] font-mono p-1.5 rounded border ${
                      step.toolResult.success
                        ? 'text-emerald-300 bg-emerald-950/20 border-emerald-900/40'
                        : 'text-red-300 bg-red-950/20 border-red-900/40'
                    }`}
                  >
                    ← {step.toolResult.tool_name}: {step.toolResult.success ? '✓ 成功' : '✗ 失败'} (
                    {(step.toolResult.execution_time * 1000).toFixed(0)}ms)
                  </div>
                )}

                {/* 详细展开卡片 */}
                {isExpanded && step.details && (
                  <pre className="mt-2 text-[10px] font-mono text-slate-400 bg-slate-950 p-2 rounded overflow-x-auto border border-slate-800">
                    {JSON.stringify(step.details, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
