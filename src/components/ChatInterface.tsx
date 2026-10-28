import { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, Trash2, Cog, Loader2, Send, User, Wrench, ChevronUp, ChevronDown } from 'lucide-react';
import type { ChatMessage, AgentEvent, ToolCallInfo, ToolResultInfo, AppConfig } from '../types';

interface Props {
  config: AppConfig;
  onOpenSettings: () => void;
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  initialPrompt?: string;
  onClearInitialPrompt?: () => void;
  onFirstMessageSent?: (content: string) => void;
}

export default function ChatInterface({
  config,
  onOpenSettings,
  messages,
  setMessages,
  initialPrompt,
  onClearInitialPrompt,
  onFirstMessageSent,
}: Props) {
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCallInfo[]>([]);
  const [currentToolResults, setCurrentToolResults] = useState<ToolResultInfo[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [activeNode, setActiveNode] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const toolCallsRef = useRef<ToolCallInfo[]>([]);
  const toolResultsRef = useRef<ToolResultInfo[]>([]);

  // 监听外部注入快捷提示
  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
      inputRef.current?.focus();
      onClearInitialPrompt?.();
    }
  }, [initialPrompt, onClearInitialPrompt]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isRunning) return;

    const userMessage = input.trim();
    if (messages.length === 0) {
      onFirstMessageSent?.(userMessage);
    }
    setInput('');
    setIsRunning(true);
    setStreamingContent('');
    toolCallsRef.current = [];
    toolResultsRef.current = [];
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

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      // Call backend API
      // 留空时走同源相对路径（由 Vite dev proxy 转发到后端），避免跨域 / 浏览器代理挂起
      const backendBase = (config.backendUrl || '').replace(/\/+$/, '') || '';
      const response = await fetch(`${backendBase}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          history: messages
            .filter(m => m.content && m.content.trim().length > 0)
            .map(m => ({ role: m.role, content: m.content })),
          config: {
            ...(config.apiKey ? { api_key: config.apiKey } : {}),
            model: config.model,
            temperature: config.temperature,
            max_tokens: config.maxTokens,
          },
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Parse SSE stream
      const reader = response.body?.getReader();
      if (!reader) throw new Error('无法读取响应流');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (!data) continue;

          try {
            const event: AgentEvent = JSON.parse(data);
            handleEvent(event);
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was aborted
        return;
      }
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
      setCurrentToolCalls([]);
      setCurrentToolResults([]);
      toolCallsRef.current = [];
      toolResultsRef.current = [];
      abortControllerRef.current = null;
    }
  }, [input, isRunning, config, messages, setMessages, onFirstMessageSent]);

  const handleEvent = (event: AgentEvent) => {
    switch (event.type) {
      case 'status':
        break;
      case 'node_enter':
        setActiveNode(event.content);
        break;
      case 'node_exit':
        setActiveNode('');
        break;
      case 'tool_call':
        toolCallsRef.current.push(event.data);
        setCurrentToolCalls([...toolCallsRef.current]);
        break;
      case 'tool_result':
        toolResultsRef.current.push(event.data);
        setCurrentToolResults([...toolResultsRef.current]);
        break;
      case 'token':
        setStreamingContent(prev => prev + event.content);
        break;
      case 'message_complete':
        setMessages(prev => [...prev, {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: event.content,
          timestamp: Date.now(),
          toolCalls: toolCallsRef.current.length > 0 ? [...toolCallsRef.current] : undefined,
          toolResults: toolResultsRef.current.length > 0 ? [...toolResultsRef.current] : undefined,
        }]);
        setStreamingContent('');
        setCurrentToolCalls([]);
        setCurrentToolResults([]);
        toolCallsRef.current = [];
        toolResultsRef.current = [];
        break;
      case 'error':
        setMessages(prev => [...prev, {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `❌ ${event.content}`,
          timestamp: Date.now(),
          toolCalls: toolCallsRef.current.length > 0 ? [...toolCallsRef.current] : undefined,
          toolResults: toolResultsRef.current.length > 0 ? [...toolResultsRef.current] : undefined,
        }]);
        setStreamingContent('');
        setCurrentToolCalls([]);
        setCurrentToolResults([]);
        toolCallsRef.current = [];
        toolResultsRef.current = [];
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
    toolCallsRef.current = [];
    toolResultsRef.current = [];
    // Note: Backend conversation history is not cleared in this demo
  };

  const quickActions = [
    { label: '📅 查询假期余额', prompt: '帮我查一下我还有多少年假' },
    { label: '📖 年假政策', prompt: '公司年假政策是怎样的？请3天以上需要怎么审批？' },
    { label: '✈️ 差旅预算', prompt: '我下周要去上海出差3天，帮我算一下差旅预算' },
    { label: '📋 开具证明', prompt: '我需要开一份在职证明，用于办理签证' },
    { label: '🎫 提交服务工单', prompt: '我想咨询跨城市社保转移流程，请帮我创建一份 HR 服务工单' },
    { label: '🔍 审批进度', prompt: '帮我查询一下我当前的审批单和流程进度' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
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
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !streamingContent && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-blue-400" />
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
        {isRunning && currentToolCalls.length > 0 && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <Cog className={`w-3.5 h-3.5 text-purple-400 ${
                currentToolCalls.length > currentToolResults.length ? 'animate-spin' : ''
              }`} />
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl rounded-tl-none px-4 py-3 max-w-lg">
              <p className="text-xs text-slate-400 mb-2">
                {currentToolCalls.length > currentToolResults.length ? '🔧 正在调用工具...' : '✓ 工具调用完成，正在生成回复...'}
              </p>
              {currentToolCalls.map((tc, i) => (
                <div key={i} className="text-xs text-cyan-300 font-mono mb-1">
                  → {tc.name}({JSON.stringify(tc.arguments)})
                </div>
              ))}
              {currentToolResults.map((tr, i) => (
                <div key={`r-${i}`} className={`text-xs mt-1 ${tr.success ? 'text-green-400' : 'text-red-400'}`}>
                  ← {tr.tool_name}: {tr.success ? '✓ 成功' : `✗ ${tr.error}`} ({(tr.execution_time * 1000).toFixed(0)}ms)
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Streaming content */}
        {streamingContent && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <Bot className="w-3.5 h-3.5 text-purple-400" />
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
              placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
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
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
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
  const [showTools, setShowTools] = useState(false);

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-blue-500/20' : 'bg-purple-500/20'
      }`}>
        {isUser ? (
          <User className="w-3.5 h-3.5 text-blue-400" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-purple-400" />
        )}
      </div>
      <div className={`rounded-xl px-4 py-3 max-w-2xl ${
        isUser
          ? 'bg-blue-600/20 border border-blue-500/30 rounded-tr-none'
          : 'bg-slate-800/50 border border-slate-700/50 rounded-tl-none'
      }`}>
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-2 pb-2 border-b border-slate-700/50">
            <button
              onClick={() => setShowTools(!showTools)}
              className="text-xs text-purple-300 hover:text-purple-200 flex items-center space-x-1 cursor-pointer"
            >
              <Wrench className="w-3 h-3" />
              <span>已调用 {message.toolCalls.length} 个工具</span>
              {showTools ? <ChevronUp className="w-3 h-3 ml-1" /> : <ChevronDown className="w-3 h-3 ml-1" />}
            </button>
            {showTools && (
              <div className="mt-2 p-2 bg-slate-900/60 rounded border border-slate-700/40 text-xs font-mono space-y-1">
                {message.toolCalls.map((tc, i) => (
                  <div key={i} className="text-cyan-300">
                    → {tc.name}({JSON.stringify(tc.arguments)})
                  </div>
                ))}
                {message.toolResults?.map((tr, i) => (
                  <div key={`res-${i}`} className={tr.success ? 'text-green-400' : 'text-red-400'}>
                    ← {tr.tool_name}: {tr.success ? '✓ 成功' : `✗ ${tr.error}`} ({(tr.execution_time * 1000).toFixed(0)}ms)
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {isUser ? (
          <div className="text-sm text-slate-200 whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div className="text-sm text-slate-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatted }} />
        )}
      </div>
    </div>
  );
}

// Render markdown tables into responsive Tailwind styled HTML
function renderMarkdownTable(
  lines: string[],
  startIndex: number,
  formatInline: (t: string) => string
): { html: string; endIndex: number } {
  const getCells = (line: string): string[] =>
    line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());

  const headerCells = getCells(lines[startIndex]);
  const dividerCells = getCells(lines[startIndex + 1]);

  const alignments = dividerCells.map(c => {
    const left = c.startsWith(':');
    const right = c.endsWith(':');
    if (left && right) return 'text-center';
    if (right) return 'text-right';
    return 'text-left';
  });

  let html = '<div class="overflow-x-auto my-3 rounded-lg border border-slate-700/60 shadow-sm">';
  html += '<table class="min-w-full text-xs divide-y divide-slate-700/80 border-collapse">';
  html += '<thead class="bg-slate-800/90 text-slate-200"><tr>';

  headerCells.forEach((h, idx) => {
    const align = alignments[idx] || 'text-left';
    html += `<th class="px-3 py-2 font-semibold ${align}">${formatInline(h)}</th>`;
  });
  html += '</tr></thead>';

  html += '<tbody class="divide-y divide-slate-800/60 bg-slate-900/40">';
  let i = startIndex + 2;

  while (i < lines.length && lines[i].trim().includes('|')) {
    const trimmed = lines[i].trim();
    const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
    if (cells.length > 0 && cells.every(c => /^:?-+:?$/.test(c))) {
      break; // Stop if another divider row appears
    }
    const rowCells = getCells(lines[i]);
    html += '<tr class="hover:bg-slate-800/30 transition-colors">';
    rowCells.forEach((c, idx) => {
      const align = alignments[idx] || 'text-left';
      html += `<td class="px-3 py-2 text-slate-300 ${align}">${formatInline(c)}</td>`;
    });
    html += '</tr>';
    i++;
  }
  html += '</tbody></table></div>';

  return { html, endIndex: i - 1 };
}


// Markdown-like formatting with proper container wrapping for ordered and unordered lists
function formatMessage(content: string): string {
  const formatInline = (text: string): string => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-slate-700/50 px-1 py-0.5 rounded text-cyan-300 text-xs">$1</code>');
  };

  // Normalise lines (handle cases where divider is glued with previous content)
  const normalized = content.replace(/([^\n])\s*(---|---|\*\*\*)\s*$/gm, '$1\n$2');
  const lines = normalized.split('\n');
  const result: string[] = [];
  let inOl = false;
  let inUl = false;
  let inNestedUl = false;

  const closeNestedUl = () => {
    if (inNestedUl) {
      result.push('</ul>');
      inNestedUl = false;
    }
  };

  const isTableDivider = (line: string): boolean => {
    const trimmed = line.trim();
    if (!trimmed.includes('|')) return false;
    const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
    return cells.length > 0 && cells.every(c => /^:?-+:?$/.test(c));
  };

  const closeLists = () => {
    closeNestedUl();
    if (inUl) {
      result.push('</ul>');
      inUl = false;
    }
    if (inOl) {
      result.push('</ol>');
      inOl = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Check table: current line has '|' and next line is table divider
    if (trimmed.includes('|') && i + 1 < lines.length && isTableDivider(lines[i + 1])) {
      closeLists();
      const { html, endIndex } = renderMarkdownTable(lines, i, formatInline);
      result.push(html);
      i = endIndex;
      continue;
    }

    // Check divider: --- or ***
    if (/^(---|---|\*\*\*)$/.test(trimmed) || /^---+$/.test(trimmed)) {
      closeLists();
      result.push('<hr class="my-3 border-slate-700/60" />');
      continue;
    }

    // Check headings
    const h3Match = rawLine.match(/^###\s+(.*)$/);
    if (h3Match) {
      closeLists();
      result.push(`<h3 class="text-base font-semibold text-white mt-3 mb-1.5">${formatInline(h3Match[1])}</h3>`);
      continue;
    }

    const h2Match = rawLine.match(/^##\s+(.*)$/);
    if (h2Match) {
      closeLists();
      result.push(`<h2 class="text-lg font-semibold text-white mt-4 mb-2">${formatInline(h2Match[1])}</h2>`);
      continue;
    }

    const h1Match = rawLine.match(/^#\s+(.*)$/);
    if (h1Match) {
      closeLists();
      result.push(`<h1 class="text-xl font-bold text-white mt-4 mb-2">${formatInline(h1Match[1])}</h1>`);
      continue;
    }

    // Check ordered list: 1. xxx or 1) xxx
    const olMatch = rawLine.match(/^\s*(\d+)[\.\)]\s+(.*)$/);
    if (olMatch) {
      closeNestedUl();
      if (inUl) {
        result.push('</ul>');
        inUl = false;
      }
      if (!inOl) {
        result.push('<ol class="list-decimal ml-6 my-1.5 space-y-1">');
        inOl = true;
      }
      result.push(`<li value="${olMatch[1]}">${formatInline(olMatch[2])}</li>`);
      continue;
    }

    // Check unordered list: - xxx or * xxx
    const ulMatch = rawLine.match(/^\s*[-*]\s+(.*)$/);
    if (ulMatch) {
      if (inOl) {
        if (!inNestedUl) {
          result.push('<ul class="list-disc ml-6 my-1 space-y-0.5 text-slate-300">');
          inNestedUl = true;
        }
        result.push(`<li>${formatInline(ulMatch[1])}</li>`);
        continue;
      }
      if (!inUl) {
        result.push('<ul class="list-disc ml-6 my-1.5 space-y-1">');
        inUl = true;
      }
      result.push(`<li>${formatInline(ulMatch[1])}</li>`);
      continue;
    }

    // Empty line
    if (!trimmed) {
      // Check if subsequent non-empty line continues list
      let nextLineIsList = false;
      for (let j = i + 1; j < lines.length; j++) {
        const nextTrimmed = lines[j].trim();
        if (!nextTrimmed) continue;
        if (/^\s*(\d+)[\.\)]\s+/.test(nextTrimmed) || /^\s*[-*]\s+/.test(nextTrimmed)) {
          nextLineIsList = true;
        }
        break;
      }
      if (nextLineIsList) {
        continue;
      }

      closeLists();
      result.push('<div class="h-2"></div>');
      continue;
    }

    // Regular text line
    closeLists();
    result.push(`<div class="my-0.5">${formatInline(rawLine)}</div>`);
  }

  closeLists();
  return result.join('\n');
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
