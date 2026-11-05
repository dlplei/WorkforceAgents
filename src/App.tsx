import { useState, useEffect, useCallback, useRef } from 'react';
import { Menu, Bot, Settings, Layers, Workflow, ChevronDown, CheckSquare, UserCheck, Activity } from 'lucide-react';
import type { AppConfig, ChatMessage, EmployeeProfile } from './types';
import { loadConfig, defaultConfig, currentEmployee as fallbackEmployee } from './config';
import ChatInterface from './components/ChatInterface';
import Sidebar, { ChatSession } from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import AboutModal from './components/AboutModal';
import PendingApprovalsModal from './components/PendingApprovalsModal';
import ObservabilityModal from './components/ObservabilityModal';

interface FullSession extends ChatSession {
  messages: ChatMessage[];
}

const PERSONA_STORAGE_KEY = 'wf_agent_persona_emp_id';
const getPersonaSessionStorageKey = (empId: string) => `wf_agent_sessions_${empId}_v2`;

const loadSessionsForPersona = (empId: string): FullSession[] => {
  try {
    const saved = localStorage.getItem(getPersonaSessionStorageKey(empId));
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.warn(`Failed to parse saved sessions for ${empId}:`, e);
  }
  // 针对默认员工 E10293，兼容旧版未隔离的 storage
  if (empId === 'E10293') {
    try {
      const legacySaved = localStorage.getItem('wf_agent_sessions_v1');
      if (legacySaved) {
        const parsed = JSON.parse(legacySaved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
  }
  return [{ id: `session-${empId}-${Date.now()}`, title: '新对话', timestamp: Date.now(), messages: [] }];
};

const DEFAULT_PERSONAS: EmployeeProfile[] = [
  {
    id: 'E10293',
    name: '张明',
    department: '技术研发部',
    position: '高级前端工程师',
    level: 'P6',
    location: '北京',
    manager: '李伟',
    leave_balance: { annual: 7, sick: 5, personal: 2 },
  },
  {
    id: 'E10001',
    name: '李伟',
    department: '技术研发部',
    position: '技术总监 / 研发主管',
    level: 'M1',
    location: '北京',
    manager: '赵静',
    leave_balance: { annual: 15, sick: 10, personal: 5 },
  },
  {
    id: 'E10456',
    name: '王芳',
    department: '人力资源部',
    position: 'HRBP',
    level: 'P7',
    location: '上海',
    manager: '赵静',
    leave_balance: { annual: 12, sick: 8, personal: 3 },
  },
];

export default function App() {
  const [config, setConfig] = useState<AppConfig>(defaultConfig);
  const [showSettings, setShowSettings] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [showObservability, setShowObservability] = useState(false);
  const [showGraph, setShowGraph] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activePrompt, setActivePrompt] = useState<string>('');
  const [employees, setEmployees] = useState<EmployeeProfile[]>(DEFAULT_PERSONAS);
  const [currentEmpId, setCurrentEmpId] = useState<string>(() => {
    return localStorage.getItem(PERSONA_STORAGE_KEY) || 'E10293';
  });
  const [currentEmployee, setCurrentEmployee] = useState<EmployeeProfile>(() => {
    const savedId = localStorage.getItem(PERSONA_STORAGE_KEY) || 'E10293';
    return DEFAULT_PERSONAS.find((e) => e.id === savedId) || DEFAULT_PERSONAS[0];
  });
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);
  const [showApprovalsModal, setShowApprovalsModal] = useState(false);
  const [personaMenuOpen, setPersonaMenuOpen] = useState(false);
  const personaMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!personaMenuOpen) return;

    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (personaMenuRef.current && !personaMenuRef.current.contains(event.target as Node)) {
        setPersonaMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setPersonaMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [personaMenuOpen]);

  const backendBase = (config.backendUrl || '').replace(/\/+$/, '') || '';

  const refreshEmployeeData = useCallback(async () => {
    try {
      const res = await fetch(`${backendBase}/api/employee`, {
        headers: { 'X-Employee-Id': currentEmpId },
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentEmployee(data);
      }
    } catch (e) {
      console.warn('Failed to refresh employee data:', e);
    }
  }, [backendBase, currentEmpId]);

  const refreshPendingCount = useCallback(async () => {
    try {
      const res = await fetch(`${backendBase}/api/approvals/pending`, {
        headers: { 'X-Employee-Id': currentEmpId },
      });
      if (res.ok) {
        const list = await res.json();
        setPendingApprovalsCount(Array.isArray(list) ? list.length : 0);
      }
    } catch (e) {
      console.warn('Failed to refresh pending count:', e);
    }
  }, [backendBase, currentEmpId]);

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const res = await fetch(`${backendBase}/api/employees`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setEmployees(data);
            const found = data.find((e: EmployeeProfile) => e.id === currentEmpId);
            if (found) setCurrentEmployee(found);
          }
        }
      } catch (e) {
        console.warn('Failed to fetch employees:', e);
      }
    };
    fetchEmployees();
  }, [backendBase, currentEmpId]);

  useEffect(() => {
    refreshEmployeeData();
    refreshPendingCount();
  }, [currentEmpId, refreshEmployeeData, refreshPendingCount]);

  // 全局事件总线联动：实时监听待办审批状态变更与请假变动
  useEffect(() => {
    const handleApprovalsUpdated = () => {
      refreshEmployeeData();
      refreshPendingCount();
    };
    window.addEventListener('workforce:approvals_updated', handleApprovalsUpdated);
    return () => {
      window.removeEventListener('workforce:approvals_updated', handleApprovalsUpdated);
    };
  }, [refreshEmployeeData, refreshPendingCount]);

  const [sessions, setSessions] = useState<FullSession[]>(() => {
    const initialEmpId = localStorage.getItem(PERSONA_STORAGE_KEY) || 'E10293';
    return loadSessionsForPersona(initialEmpId);
  });

  const [currentSessionId, setCurrentSessionId] = useState<string>(() => sessions[0]?.id || `session-${currentEmpId}-${Date.now()}`);

  useEffect(() => {
    const saved = loadConfig();
    setConfig(saved);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(getPersonaSessionStorageKey(currentEmpId), JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to persist sessions:', e);
    }
  }, [sessions, currentEmpId]);

  const handleSwitchPersona = (emp: EmployeeProfile) => {
    if (emp.id === currentEmpId) {
      setPersonaMenuOpen(false);
      return;
    }

    // 1. 持久化保存当前角色的会话
    try {
      localStorage.setItem(getPersonaSessionStorageKey(currentEmpId), JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to persist sessions on switch:', e);
    }

    // 2. 加载目标角色的专属会话
    const nextSessions = loadSessionsForPersona(emp.id);
    setSessions(nextSessions);
    setCurrentSessionId(nextSessions[0].id);

    // 3. 切换角色状态与工号
    setCurrentEmpId(emp.id);
    setCurrentEmployee(emp);
    localStorage.setItem(PERSONA_STORAGE_KEY, emp.id);
    setPersonaMenuOpen(false);
  };

  const currentSession = sessions.find((s) => s.id === currentSessionId) || sessions[0];
  const messages = currentSession ? currentSession.messages : [];

  const setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>> = (action) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === currentSessionId) {
          const next = typeof action === 'function' ? action(s.messages) : action;
          return { ...s, messages: next };
        }
        return s;
      })
    );
  };

  const handleNewChat = () => {
    const newSession: FullSession = {
      id: `session-${currentEmpId}-${Date.now()}`,
      title: '新对话',
      timestamp: Date.now(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id);
      if (filtered.length === 0) {
        const fallback: FullSession = {
          id: `session-${currentEmpId}-${Date.now()}`,
          title: '新对话',
          timestamp: Date.now(),
          messages: [],
        };
        setCurrentSessionId(fallback.id);
        return [fallback];
      }
      if (currentSessionId === id) {
        setCurrentSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleFirstMessageSent = (content: string) => {
    const title = content.length > 15 ? `${content.slice(0, 15)}...` : content;
    setSessions((prev) =>
      prev.map((s) => (s.id === currentSessionId ? { ...s, title } : s))
    );
  };

  const handleSelectPrompt = (prompt: string) => {
    setActivePrompt(prompt);
  };

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white overflow-hidden">
      {/* Top Bar */}
      <header className="relative z-30 flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <Menu className="w-4 h-4" />
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent leading-tight">
                Workforce Operations Agent
              </h1>
              <p className="text-[10px] text-slate-500">企业级智能员工服务 Copilot</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Persona Switcher Dropdown */}
          <div className="relative" ref={personaMenuRef}>
            <button
              onClick={() => setPersonaMenuOpen((prev) => !prev)}
              className="flex items-center space-x-2 px-2.5 py-1.5 text-xs rounded-lg bg-slate-700/60 hover:bg-slate-700 border border-slate-600/60 transition-colors"
              title="切换当前体验身份"
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  currentEmployee.level.startsWith('M')
                    ? 'bg-amber-400'
                    : currentEmployee.department.includes('人力')
                    ? 'bg-purple-400'
                    : 'bg-blue-400'
                }`}
              />
              <span className="font-medium text-slate-200">
                {currentEmployee.name} ({currentEmployee.id})
              </span>
              <span className="text-[10px] text-slate-400 hidden lg:inline">
                · {currentEmployee.position}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {personaMenuOpen && (
              <div className="absolute right-0 mt-1 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 py-1 overflow-hidden">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 border-b border-slate-700/60 uppercase tracking-wider flex items-center justify-between">
                  <span>切换模拟身份 (RBAC)</span>
                  <UserCheck className="w-3 h-3 text-cyan-400" />
                </div>
                {employees.map((emp) => {
                  const isSelected = emp.id === currentEmployee.id;
                  const isManager = emp.level.startsWith('M');
                  const isHR = emp.department.includes('人力');
                  return (
                    <button
                      key={emp.id}
                      onClick={() => handleSwitchPersona(emp)}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition-colors ${
                        isSelected
                          ? 'bg-blue-600/20 text-blue-300 font-medium'
                          : 'hover:bg-slate-700/60 text-slate-300'
                      }`}
                    >
                      <div>
                        <div className="flex items-center space-x-1.5">
                          <span>{emp.name}</span>
                          <span className="text-[10px] text-slate-400">({emp.id})</span>
                          {isManager && (
                            <span className="text-[9px] px-1 py-0.2 bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded">
                              主管
                            </span>
                          )}
                          {isHR && (
                            <span className="text-[9px] px-1 py-0.2 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded">
                              HRBP
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {emp.department} · {emp.position}
                        </div>
                      </div>
                      {isSelected && <span className="text-blue-400 text-xs">✓</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pending Approvals Entry Button */}
          {(currentEmployee.level.startsWith('M') ||
            currentEmployee.department.includes('人力') ||
            pendingApprovalsCount > 0) && (
            <button
              onClick={() => setShowApprovalsModal(true)}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 text-xs rounded-lg transition-colors border ${
                pendingApprovalsCount > 0
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30 animate-pulse'
                  : 'bg-slate-700/40 text-slate-300 border-slate-700/60 hover:bg-slate-700/60'
              }`}
              title="查看与审批待办事项"
            >
              <CheckSquare className="w-3.5 h-3.5 text-amber-400" />
              <span>待办审批</span>
              {pendingApprovalsCount > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-amber-500 text-slate-900 leading-tight">
                  {pendingApprovalsCount}
                </span>
              )}
            </button>
          )}

          {/* Status indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs bg-green-500/10 text-green-400">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
            <span>已就绪 (.env)</span>
          </div>

          {/* Model badge */}
          <span className="text-xs bg-slate-700/50 text-slate-400 px-2 py-1 rounded hidden sm:inline">
            {config.model}
          </span>

          {/* 系统架构与工具库入口 */}
          <button
            onClick={() => setShowAbout(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-slate-700/70 border border-slate-700/60 rounded-lg transition-colors"
            title="查看底层系统架构与 Agent 可用工具"
          >
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span className="hidden md:inline">架构与工具</span>
          </button>

          {/* 可观测性监控仪表盘入口 */}
          <button
            onClick={() => setShowObservability(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs rounded-lg transition-all border bg-blue-600/20 text-blue-300 border-blue-500/40 hover:bg-blue-600/30 hover:text-white shadow-sm"
            title="在主窗口内直接查看 Prometheus & Grafana 实时时序与聚合监控大屏"
          >
            <Activity className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
            <span className="font-medium">监控仪表盘</span>
          </button>

          {/* LangGraph 状态机拓扑监控入口 */}
          <button
            onClick={() => setShowGraph((prev) => !prev)}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 text-xs rounded-lg transition-colors border ${
              showGraph
                ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/60 border-slate-700/50'
            }`}
            title="展开/收起 LangGraph 状态机拓扑监控"
          >
            <Workflow className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">LangGraph 拓扑</span>
          </button>

          {/* Settings button */}
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            title="API 配置"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <div className="w-64 flex-shrink-0 hidden md:block">
            <Sidebar
              onNewChat={handleNewChat}
              onSelectPrompt={handleSelectPrompt}
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelectSession={setCurrentSessionId}
              onDeleteSession={handleDeleteSession}
              employee={currentEmployee}
              onOpenObservability={() => setShowObservability(true)}
            />
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatInterface
            key={`${currentSessionId}-${currentEmployee.id}`}
            config={config}
            onOpenSettings={() => setShowSettings(true)}
            messages={messages}
            setMessages={setMessages}
            initialPrompt={activePrompt}
            onClearInitialPrompt={() => setActivePrompt('')}
            onFirstMessageSent={handleFirstMessageSent}
            showGraph={showGraph}
            setShowGraph={setShowGraph}
            employee={currentEmployee}
            onActionCompleted={() => {
              refreshEmployeeData();
              refreshPendingCount();
            }}
          />
        </div>
      </div>

      {/* Pending Approvals Modal */}
      {showApprovalsModal && (
        <PendingApprovalsModal
          isOpen={showApprovalsModal}
          onClose={() => setShowApprovalsModal(false)}
          currentEmployee={currentEmployee}
          backendUrl={config.backendUrl}
          onApprovalDone={() => {
            setPendingApprovalsCount((prev) => Math.max(0, prev - 1));
            refreshEmployeeData();
            refreshPendingCount();
          }}
        />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          config={config}
          onSave={setConfig}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* About & Tools Modal */}
      {showAbout && (
        <AboutModal
          config={config}
          onClose={() => setShowAbout(false)}
        />
      )}

      {/* Prometheus & Grafana 实时监控仪表盘模态窗口 */}
      <ObservabilityModal
        isOpen={showObservability}
        onClose={() => setShowObservability(false)}
      />
    </div>
  );
}
