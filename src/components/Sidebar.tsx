import { useState } from 'react';
import { Plus, MessageSquare, Trash2, Calendar, FileText, Plane, HelpCircle, ChevronUp, ChevronDown } from 'lucide-react';
import { currentEmployee } from '../config';

export interface ChatSession {
  id: string;
  title: string;
  timestamp: number;
}

interface Props {
  onNewChat: () => void;
  onSelectPrompt: (prompt: string) => void;
  sessions: ChatSession[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
}

export default function Sidebar({
  onNewChat,
  onSelectPrompt,
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession,
}: Props) {
  const [showProfileDetail, setShowProfileDetail] = useState(false);

  const quickSkills = [
    { label: '查询假期余额', icon: Calendar, prompt: '帮我查一下我目前的假期余额' },
    { label: '申请年假/请假', icon: FileText, prompt: '我想申请下周一休年假 1 天，请帮我提交申请' },
    { label: '差旅报销标准', icon: Plane, prompt: '公司出差差旅标准是什么？住宿和补贴上限是多少？' },
    { label: '开具在职证明', icon: HelpCircle, prompt: '我需要开具一份用于办理签证的在职证明' },
  ];

  return (
    <aside className="h-full flex flex-col bg-slate-900 border-r border-slate-800 select-none">
      {/* 顶部新建对话按钮 */}
      <div className="p-3 border-b border-slate-800">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>新建对话</span>
        </button>
      </div>

      {/* 快捷业务技能 */}
      <div className="p-3 border-b border-slate-800">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">快捷服务</div>
        <div className="grid grid-cols-1 gap-1">
          {quickSkills.map((skill) => (
            <button
              key={skill.label}
              onClick={() => onSelectPrompt(skill.prompt)}
              className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 text-left transition-colors"
            >
              <skill.icon className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
              <span className="truncate">{skill.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 历史对话列表 */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>历史会话</span>
          <span className="text-[10px] text-slate-500">{sessions.length}</span>
        </div>
        {sessions.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500">暂无历史对话</div>
        ) : (
          <div className="space-y-1">
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                  s.id === currentSessionId ? 'bg-slate-800 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2 truncate min-w-0 mr-1">
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{s.title || '新对话'}</span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 rounded"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部员工名片与假期抽屉 */}
      <div className="border-t border-slate-800 bg-slate-900/90 p-3">
        {showProfileDetail && (
          <div className="mb-3 p-3 rounded-lg bg-slate-800/90 border border-slate-700/60 space-y-2 text-xs">
            <div className="flex items-center justify-between text-slate-300 font-medium border-b border-slate-700/50 pb-1.5">
              <span>员工档案</span>
              <span className="text-[10px] text-slate-400">{currentEmployee.id}</span>
            </div>
            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">常驻地:</span>
                <span>{currentEmployee.location}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">汇报人:</span>
                <span>{currentEmployee.manager}</span>
              </div>
            </div>

            <div className="pt-1.5 border-t border-slate-700/50 space-y-1.5">
              <div className="text-[11px] font-medium text-slate-400">假期余额</div>
              {[
                { label: '年假', val: currentEmployee.leaveBalance.annual, max: 15, color: 'bg-blue-500' },
                { label: '病假', val: currentEmployee.leaveBalance.sick, max: 10, color: 'bg-emerald-500' },
                { label: '事假', val: currentEmployee.leaveBalance.personal, max: 5, color: 'bg-amber-500' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">{item.label}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${item.color}`}
                        style={{ width: `${Math.min(100, (item.val / item.max) * 100)}%` }}
                      />
                    </div>
                    <span className="w-6 text-right font-mono text-slate-300">{item.val}天</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 紧凑员工栏 */}
        <div
          onClick={() => setShowProfileDetail(!showProfileDetail)}
          className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <div className="flex items-center space-x-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
              {currentEmployee.name[0]}
            </div>
            <div className="min-w-0">
              <div className="text-xs font-medium text-slate-200 truncate leading-tight">
                {currentEmployee.name}
              </div>
              <div className="text-[10px] text-slate-400 truncate leading-tight">
                {currentEmployee.department} · {currentEmployee.level}
              </div>
            </div>
          </div>
          <button className="text-slate-400 hover:text-slate-200 p-1">
            {showProfileDetail ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </aside>
  );
}
