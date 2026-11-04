import { useState, useEffect, useRef } from 'react';
import { X, Activity, Maximize2, Minimize2, ExternalLink, RefreshCw, AlertCircle, Cpu, Radio } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  grafanaUrl?: string;
}

export default function ObservabilityModal({
  isOpen,
  onClose,
  grafanaUrl = 'http://localhost:3002/d/workforce-ops-agent/workforce-operations-agent-observability-dashboard?kiosk=tv&theme=dark&refresh=5s',
}: Props) {
  const [isMaximized, setIsMaximized] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      setHasError(false);
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleRefresh = () => {
    setIsLoading(true);
    setHasError(false);
    setIframeKey((prev) => prev + 1);
  };

  const cleanOpenUrl = grafanaUrl.replace('&kiosk=tv', '').replace('?kiosk=tv', '');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/75 backdrop-blur-md animate-fade-in select-none">
      <div
        className={`bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-200 ${
          isMaximized ? 'w-full h-full rounded-none' : 'w-[96vw] max-w-7xl h-[88vh]'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800/90 border-b border-slate-700/70">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white">时序与聚合监控仪表盘</h2>
                <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <Radio className="w-2.5 h-2.5 animate-pulse" />
                  <span>实时流 5s</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Prometheus 实时采集 · Grafana 生产级可观测性大屏 (Workforce Ops)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1.5">
            <button
              onClick={handleRefresh}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="刷新仪表盘视图"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title={isMaximized ? '还原窗口' : '全屏沉浸大屏'}
            >
              {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <a
              href={cleanOpenUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="在独立新标签页中打开"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded-lg transition-colors ml-1"
              title="关闭 (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        {/* 主体 iframe 区域 */}
        <div className="relative flex-1 bg-slate-950 overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm text-slate-300">
              <Activity className="w-8 h-8 text-blue-400 animate-spin mb-3" />
              <div className="text-sm font-medium">正在载入 Grafana 实时监控大屏...</div>
              <div className="text-xs text-slate-500 mt-1">连接 Prometheus :9091 与 Grafana :3002</div>
            </div>
          )}

          {hasError ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center">
              <AlertCircle className="w-8 h-8 text-amber-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">无法连接到 Grafana 容器 (:3002)</h3>
              <p className="text-xs text-slate-400 max-w-md mb-4 leading-relaxed">
                请确认容器已启动：<code>podman compose up -d prometheus grafana</code>
              </p>
              <button
                onClick={handleRefresh}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg"
              >
                重试连接
              </button>
            </div>
          ) : (
            <iframe
              key={iframeKey}
              ref={iframeRef}
              src={grafanaUrl}
              title="Workforce Operations Agent Observability"
              className="w-full h-full border-0 select-auto"
              onLoad={() => setIsLoading(false)}
              onError={() => {
                setIsLoading(false);
                setHasError(true);
              }}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-t border-slate-800 text-[11px] text-slate-400">
          <span className="flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span>链路: FastAPI (:8000/metrics) ➔ Prometheus (:9091) ➔ Grafana (:3002)</span>
          </span>
          <span className="text-slate-500 hidden md:inline">
            指标覆盖: LLM Tokens · 缓存命中率 · 护栏短路拦截 · HITL 决策 · P90 延迟
          </span>
        </div>
      </div>
    </div>
  );
}