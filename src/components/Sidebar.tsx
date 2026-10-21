import { useState, useEffect } from 'react';
import type { AppConfig, ToolInfo } from '../types';
import { currentEmployee } from '../config';

interface Props {
  config: AppConfig;
}

export default function Sidebar({ config }: Props) {
  const [tools, setTools] = useState<ToolInfo[]>([]);

  // Fetch tools from backend
  useEffect(() => {
    const fetchTools = async () => {
      try {
        console.log('Fetching tools from:', `${config.backendUrl}/api/tools`);
        const response = await fetch(`${config.backendUrl}/api/tools`);
        if (response.ok) {
          const data = await response.json();
          console.log('Tools loaded:', data.length);
          setTools(data);
        } else {
          console.error('Failed to fetch tools, status:', response.status);
        }
      } catch (err) {
        console.error('Failed to fetch tools:', err);
      }
    };
    fetchTools();
  }, [config.backendUrl]);

  return (
    <div className="h-full overflow-y-auto bg-slate-800/30 border-r border-slate-700/50">
      {/* Employee Info */}
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">当前员工</h3>
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold text-white">{currentEmployee.name[0]}</span>
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{currentEmployee.name}</div>
            <div className="text-xs text-slate-400">{currentEmployee.id}</div>
          </div>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between"><span className="text-slate-400">部门</span><span className="text-slate-200">{currentEmployee.department}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">职位</span><span className="text-slate-200">{currentEmployee.position}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">级别</span><span className="text-slate-200">{currentEmployee.level}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">地点</span><span className="text-slate-200">{currentEmployee.location}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">汇报</span><span className="text-slate-200">{currentEmployee.manager}</span></div>
        </div>
      </div>

      {/* Leave Balance */}
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">假期余额</h3>
        <div className="space-y-2">
          {[
            { label: '年假', value: currentEmployee.leaveBalance.annual, color: 'blue' },
            { label: '病假', value: currentEmployee.leaveBalance.sick, color: 'green' },
            { label: '事假', value: currentEmployee.leaveBalance.personal, color: 'amber' },
          ].map((leave) => (
            <div key={leave.label} className="flex items-center justify-between">
              <span className="text-xs text-slate-400">{leave.label}</span>
              <div className="flex items-center space-x-2">
                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full bg-${leave.color}-500`}
                    style={{ width: `${(leave.value / 15) * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs font-mono text-slate-200 w-6 text-right">{leave.value}天</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Available Tools */}
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">可用工具 ({tools.length})</h3>
        <div className="space-y-1.5">
          {tools.map((tool: ToolInfo) => (
            <div key={tool.name} className="flex items-start space-x-2 group">
              <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                tool.permission_level === 'autonomous' ? 'bg-green-400' :
                tool.permission_level === 'confirmation' ? 'bg-amber-400' : 'bg-red-400'
              }`}></div>
              <div>
                <div className="text-xs font-mono text-slate-300">{tool.name}</div>
                <div className="text-[10px] text-slate-500 leading-tight">{tool.description.slice(0, 50)}...</div>
              </div>
            </div>
          ))}
          {tools.length === 0 && (
            <p className="text-xs text-slate-500">无法连接后端...</p>
          )}
        </div>
      </div>

      {/* Architecture Info */}
      <div className="p-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">系统架构</h3>
        <div className="space-y-2">
          {[
            { label: '前端', value: 'React + Vite', icon: 'fa-react' },
            { label: '后端', value: 'FastAPI + Python', icon: 'fa-python' },
            { label: '引擎', value: 'ReAct + Tool Calling', icon: 'fa-brain' },
            { label: '知识库', value: 'Mock RAG (7篇政策)', icon: 'fa-book' },
            { label: '通信', value: 'SSE Streaming', icon: 'fa-bolt' },
          ].map((item) => (
            <div key={item.label} className="flex items-center space-x-2 text-xs">
              <i className={`fas ${item.icon} text-slate-500 w-4`}></i>
              <span className="text-slate-400">{item.label}:</span>
              <span className="text-slate-300">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
