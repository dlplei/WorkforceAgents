import { useState, useEffect } from 'react';
import type { AppConfig } from './types';
import { loadConfig, defaultConfig } from './config';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';

export default function App() {
  const [config, setConfig] = useState<AppConfig>(defaultConfig);
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Load config on mount
  useEffect(() => {
    const saved = loadConfig();
    setConfig(saved);
    if (!saved.apiKey) {
      setShowSettings(true);
    }
  }, []);

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white overflow-hidden">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <i className="fas fa-bars text-sm"></i>
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <i className="fas fa-robot text-white text-xs"></i>
            </div>
            <div>
              <h1 className="text-sm font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent leading-tight">
                Workforce Operations Agent
              </h1>
              <p className="text-[10px] text-slate-500">MVP Demo · FastAPI + React</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Status indicator */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs ${
            config.apiKey ? 'bg-green-500/10 text-green-400' : 'bg-amber-500/10 text-amber-400'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${config.apiKey ? 'bg-green-400' : 'bg-amber-400'}`}></span>
            <span>{config.apiKey ? '已连接' : '未配置'}</span>
          </div>

          {/* Model badge */}
          <span className="text-xs bg-slate-700/50 text-slate-400 px-2 py-1 rounded hidden sm:inline">
            {config.model}
          </span>

          {/* Settings button */}
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            title="API 配置"
          >
            <i className="fas fa-cog text-sm"></i>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <div className="w-72 flex-shrink-0 hidden md:block">
            <Sidebar config={config} />
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatInterface config={config} onOpenSettings={() => setShowSettings(true)} />
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
    </div>
  );
}
