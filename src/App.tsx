import { useState, useEffect } from 'react';
import { Menu, Bot, Settings, Layers, Workflow } from 'lucide-react';
import type { AppConfig, ChatMessage } from './types';
import { loadConfig, defaultConfig } from './config';
import ChatInterface from './components/ChatInterface';
import Sidebar, { ChatSession } from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import AboutModal from './components/AboutModal';

interface FullSession extends ChatSession {
  messages: ChatMessage[];
}

const STORAGE_KEY = 'wf_agent_sessions_v1';

export default function App() {
  const [config, setConfig] = useState<AppConfig>(defaultConfig);
  const [showSettings, setShowSettings] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [showGraph, setShowGraph] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activePrompt, setActivePrompt] = useState<string>('');

  const [sessions, setSessions] = useState<FullSession[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Failed to parse saved sessions:', e);
    }
    return [{ id: `session-${Date.now()}`, title: '新对话', timestamp: Date.now(), messages: [] }];
  });

  const [currentSessionId, setCurrentSessionId] = useState<string>(() => sessions[0]?.id || `session-${Date.now()}`);

  useEffect(() => {
    const saved = loadConfig();
    setConfig(saved);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to persist sessions:', e);
    }
  }, [sessions]);

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
      id: `session-${Date.now()}`,
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
          id: `session-${Date.now()}`,
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
      <header className="flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm">
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
            />
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatInterface
            key={currentSessionId}
            config={config}
            onOpenSettings={() => setShowSettings(true)}
            messages={messages}
            setMessages={setMessages}
            initialPrompt={activePrompt}
            onClearInitialPrompt={() => setActivePrompt('')}
            onFirstMessageSent={handleFirstMessageSent}
            showGraph={showGraph}
            setShowGraph={setShowGraph}
          />
        </div>
      </div>

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
    </div>
  );
}
