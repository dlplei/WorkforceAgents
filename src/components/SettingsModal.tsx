import { useState } from 'react';
import { Settings, X, CheckCircle2, Eye, EyeOff } from 'lucide-react';
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
            <Settings className="w-5 h-5 text-slate-400 mr-2" />
            模型运行参数设置
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="px-6 py-5 space-y-4">
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-300 flex items-start space-x-2.5">
            <CheckCircle2 className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="leading-relaxed">
              <span className="font-semibold text-white">系统环境配置生效中：</span>
              后端服务地址及 LLM API 地址已统一直接由后端的 <code className="bg-slate-900/80 px-1 py-0.5 rounded text-blue-200">.env</code> 文件接管管理，无需在前端手动输入。
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              LLM API Key <span className="text-xs text-slate-500 font-normal">（可选，留空则默认使用 .env 中的配置）</span>
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={form.apiKey}
                onChange={(e) => setForm({ ...form, apiKey: e.target.value })}
                placeholder="使用 .env 中配置的 API Key"
                className="w-full bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">若需临时切换特定调试 Key 可在此输入</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">模型 (Model)</label>
              <input
                type="text"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder="gemini-3.7-flash"
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
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium shadow-md shadow-blue-500/20"
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  );
}
