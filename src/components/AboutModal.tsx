import { useState, useEffect } from 'react';
import { X, Monitor, Server, Brain, BookOpen, Zap, Wrench, ShieldCheck, AlertCircle } from 'lucide-react';
import type { AppConfig, ToolInfo } from '../types';

interface Props {
  config: AppConfig;
  onClose: () => void;
}

export default function AboutModal({ config, onClose }: Props) {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTools = async () => {
      try {
        const base = (config.backendUrl || '').replace(/\/+$/, '');
        const response = await fetch(`${base}/api/tools`);
        if (response.ok) {
          const data = await response.json();
          setTools(data);
        }
      } catch (err) {
        console.error('Failed to fetch tools:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTools();
  }, [config.backendUrl]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/60 bg-slate-800/80">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <Brain className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">系统架构与 Agent 概览</h2>
              <p className="text-xs text-slate-400">Workforce Operations Agent 架构与能力库</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Architecture section */}
          <div>
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
              <Server className="w-3.5 h-3.5 text-blue-400" />
              <span>底层系统架构 (Tech Stack)</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { label: '前端界面', value: 'React 18 + Vite + Tailwind CSS', Icon: Monitor },
                { label: '服务后端', value: 'FastAPI + Python 3.10+ (Uvicorn)', Icon: Server },
                { label: '智能体引擎', value: 'LangGraph 状态机 (StateGraph 驱动)', Icon: Brain },
                { label: '知识检索', value: 'Mock RAG (7篇 HR/出差政策库)', Icon: BookOpen },
                { label: '实时通信', value: 'SSE (Server-Sent Events) 流式', Icon: Zap },
                { label: '权限安全', value: '敏感操作确认与权限分级拦截', Icon: ShieldCheck },
              ].map((item) => (
                <div key={item.label} className="flex items-center space-x-3 p-3 rounded-lg bg-slate-900/60 border border-slate-700/40">
                  <item.Icon className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[11px] text-slate-400">{item.label}</div>
                    <div className="text-xs font-medium text-slate-200 truncate">{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tools section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
                <Wrench className="w-3.5 h-3.5 text-amber-400" />
                <span>可用 Agent 工具库 ({tools.length})</span>
              </h3>
            </div>

            {loading ? (
              <div className="py-4 text-center text-xs text-slate-500">正在加载工具元数据...</div>
            ) : tools.length === 0 ? (
              <div className="p-4 rounded-lg bg-slate-900/40 text-center text-xs text-slate-500 flex items-center justify-center space-x-2">
                <AlertCircle className="w-4 h-4 text-amber-500" />
                <span>未连接到后端工具注册服务</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {tools.map((tool) => (
                  <div key={tool.name} className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-medium text-blue-300 truncate">{tool.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        tool.permission_level === 'autonomous' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        {tool.permission_level === 'autonomous' ? '自主' : '确认'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{tool.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-700/60 bg-slate-800/80 flex justify-end">
          <button onClick={onClose} className="px-4 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-700 hover:bg-slate-600 rounded-lg">
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
