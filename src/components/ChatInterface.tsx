import { useState, useRef, useEffect, useCallback } from 'react';
import type { ChatMessage, AgentEvent, ToolCallInfo, ToolResult, LLMConfig } from '../types';
import { AgentEngine } from '../agent/engine';

interface Props {
  config: LLMConfig;
  onOpenSettings: () => void;
}

export default function ChatInterface({ config, onOpenSettings }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCallInfo[]>([]);
  const [currentToolResults, setCurrentToolResults] = useState<ToolResult[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [activeNode, setActiveNode] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<AgentEngine | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize engine
  useEffect(() => {
    engineRef.current = new AgentEngine(config);
  }, []);

  // Update config
  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.updateConfig(config);
    }
  }, [config]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isRunning) return;
    if (!config.apiKey) {
      onOpenSettings();
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setIsRunning(true);
    setStreamingContent('');
    setCurrentToolCalls([]);
    setCurrentToolResults([]);

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);

    if (!engineRef.current) return;

    try {
      const events = engineRef.current.run(userMessage);

      for await (const event of events) {
        handleEvent(event);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `❌ 错误：${errorMsg}`,
        timestamp: Date.now(),
      }]);
    } finally {
      setIsRunning(false);
      setActiveNode('');
    }
  }, [input, isRunning, config, onOpenSettings]);

  const handleEvent = (event: AgentEvent) => {
    switch (event.type) {
      case 'status':
        break;
      case 'node_enter':
        setActiveNode(event.node);
        break;
      case 'node_exit':
        setActiveNode('');
        break;
      case 'tool_call':
        setCurrentToolCalls(prev => [...prev, event.toolCall]);
        break;
      case 'tool_result':
        setCurrentToolResults(prev => [...prev, event.result]);
        break;
      case 'token':
        setStreamingContent(prev => prev + event.content);
        break;
      case 'message_complete':
        setMessages(prev => [...prev, event.message]);
        setStreamingContent('');
        break;
      case 'error':
        setMessages(prev => [...prev, {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `❌ ${event.error}`,
          timestamp: Date.now(),
        }]);
        setStreamingContent('');
        break;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setMessages([]);
    setStreamingContent('');
    setCurrentToolCalls([]);
    setCurrentToolResults([]);
    engineRef.current?.clearHistory();
  };

  const quickActions = [
    { label: '📅 查询假期余额', prompt: '帮我查一下我还有多少年假' },
    { label: '📖 年假政策', prompt: '公司年假政策是怎样的？请3天以上需要怎么审批？' },
    { label: '✈️ 差旅预算', prompt: '我下周要去上海出差3天，帮我算一下差旅预算' },
    { label: '📋 开具证明', prompt: '我需要开一份在职证明，用于办理签证' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <i className="fas fa-robot text-white text-sm"></i>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Workforce Agent</h2>
            <p className="text-xs text-slate-400">智能员工服务助手</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isRunning && (
            <span className="text-xs text-cyan-400 flex items-center space-x-1">
              <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></span>
              <span>{getNodeLabel(activeNode)}</span>
            </span>
          )}
          <button onClick={handleClear} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors" title="清空对话">
            <i className="fas fa-trash-alt text-sm"></i>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !streamingContent && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-4">
              <i className="fas fa-robot text-3xl text-blue-400"></i>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">你好，我是 Workforce Agent</h3>
            <p className="text-sm text-slate-400 mb-6 max-w-md">
              我可以帮助你查询假期余额、了解公司政策、申请休假、计算差旅预算等。试试下面的快捷操作：
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg">
              {quickActions.map((action, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(action.prompt); inputRef.current?.focus(); }}
                  className="text-left text-sm px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:border-blue-500/30 hover:bg-slate-800 transition-all text-slate-300"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Tool calls in progress */}
        {currentToolCalls.length > 0 && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <i className="fas fa-cogs text-xs text-purple-400 animate-spin"></i>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl rounded-tl-none px-4 py-3 max-w-lg">
              <p className="text-xs text-slate-400 mb-2">🔧 正在调用工具...</p>
              {currentToolCalls.map((tc, i) => (
                <div key={i} className="text-xs text-cyan-300 font-mono mb-1">
                  → {tc.name}({JSON.stringify(tc.arguments)})
                </div>
              ))}
              {currentToolResults.map((tr, i) => (
                <div key={`r-${i}`} className={`text-xs mt-1 ${tr.success ? 'text-green-400' : 'text-red-400'}`}>
                  ← {tr.toolName}: {tr.success ? '✓ 成功' : `✗ ${tr.error}`} ({tr.executionTime.toFixed(0)}ms)
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Streaming content */}
        {streamingContent && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <i className="fas fa-robot text-xs text-purple-400"></i>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl rounded-tl-none px-4 py-3 max-w-2xl">
              <div className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                {streamingContent}
                <span className="inline-block w-1.5 h-4 bg-blue-400 animate-pulse ml-0.5 align-middle"></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-800/50">
        <div className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={config.apiKey ? '输入你的问题... (Enter 发送, Shift+Enter 换行)' : '请先配置 API Key...'}
              className="w-full bg-slate-900/50 border border-slate-600/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 resize-none"
              rows={1}
              disabled={isRunning}
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isRunning}
            className="p-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl transition-colors"
          >
            <i className={`fas ${isRunning ? 'fa-spinner animate-spin' : 'fa-paper-plane'} text-sm`}></i>
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Message Bubble ---
function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const formatted = isUser ? message.content : formatMessage(message.content);

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-blue-500/20' : 'bg-purple-500/20'
      }`}>
        <i className={`fas ${isUser ? 'fa-user text-blue-400' : 'fa-robot text-purple-400'} text-xs`}></i>
      </div>
      <div className={`rounded-xl px-4 py-3 max-w-2xl ${
        isUser
          ? 'bg-blue-600/20 border border-blue-500/30 rounded-tr-none'
          : 'bg-slate-800/50 border border-slate-700/50 rounded-tl-none'
      }`}>
        {isUser ? (
          <div className="text-sm text-slate-200 whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div className="text-sm text-slate-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatted }} />
        )}
      </div>
    </div>
  );
}

// Simple markdown-like formatting
function formatMessage(content: string): string {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/`(.*?)`/g, '<code class="bg-slate-700/50 px-1 py-0.5 rounded text-cyan-300 text-xs">$1</code>')
    .replace(/^### (.*$)/gm, '<h3 class="text-base font-semibold text-white mt-2 mb-1">$1</h3>')
    .replace(/^## (.*$)/gm, '<h2 class="text-lg font-semibold text-white mt-3 mb-1">$1</h2>')
    .replace(/^- (.*$)/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/^(\d+)\. (.*$)/gm, '<li class="ml-4 list-decimal">$2</li>');
}
function getNodeLabel(node: string): string {
  const labels: Record<string, string> = {
    'knowledge_retrieval': '📚 检索知识...',
    'reasoning': '🧠 思考中...',
    'tool_execution': '🔧 执行工具...',
    'response_generation': '💬 生成回复...',
    'context_loading': '📋 加载上下文...',
  };
  return labels[node] || '处理中...';
}
