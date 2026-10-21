import { useState } from 'react';
import type { AppConfig } from '../types';
import { saveConfig } from '../config';

interface Props {
  config: AppConfig;
  onSave: (config: AppConfig) => void;
  onClose: () => void;
}

export default function SettingsModal({ config, onSave, onClose }: Props) {
  const [form, setForm] = useState<AppConfig>({ ...config });
  const [showKey, setShowKey] = useState(false);

  const handleSave = () => {
    onSave(form);
    saveConfig(form);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <i className="fas fa-cog text-slate-400 mr-2"></i>
            配置
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <i className="fas fa-times"></i>
          </button>
        </div>

        {/* Form */}
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">后端地址 (Backend URL)</label>
            <input
              type="text"
              value={form.backendUrl}
              onChange={(e) => setForm({ ...form, backendUrl: e.target.value })}
              placeholder="http://localhost:8000"
              className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
            />
            <p className="text-xs text-slate-500 mt-1">本地 FastAPI 后端服务地址（默认 http://localhost:8000）</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">LLM API 地址 (LLM Base URL)</label>
            <input
              type="text"
              value={form.llmBaseUrl}
              onChange={(e) => setForm({ ...form, llmBaseUrl: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
            />
            <p className="text-xs text-slate-500 mt-1">OpenAI 兼容的 LLM API 服务地址（会传递给后端）</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">LLM API Key</label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={form.apiKey}
                onChange={(e) => setForm({ ...form, apiKey: e.target.value })}
                placeholder="sk-..."
                className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <i className={`fas ${showKey ? 'fa-eye-slash' : 'fa-eye'} text-sm`}></i>
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">OpenAI 兼容 API 的 Key，会传递给后端</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">模型</label>
              <input
                type="text"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder="gpt-4o-mini"
                className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) || 0.7 })}
                className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Max Tokens</label>
            <input
              type="number"
              step="256"
              min="256"
              max="32768"
              value={form.maxTokens}
              onChange={(e) => setForm({ ...form, maxTokens: parseInt(e.target.value) || 2048 })}
              className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={!form.apiKey}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors"
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  );
}
