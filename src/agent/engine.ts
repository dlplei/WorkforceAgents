// ============================================================
// Agent Core Engine - ReAct Loop + Streaming
// ============================================================
import type { ChatMessage, AgentEvent, LLMConfig, ToolCallInfo } from '../types';
import { currentEmployee } from '../config';
import { retrieveKnowledge } from './knowledge';
import { getToolsForLLM, executeTool } from './tools';

// --- System Prompt ---
const SYSTEM_PROMPT = `你是一个智能员工服务与人力运营 Agent（Workforce Operations Agent）。

## 你的身份
- 你服务于「星辰科技有限公司」的员工
- 当前登录员工：${currentEmployee.name}（${currentEmployee.id}），${currentEmployee.department}，${currentEmployee.position}
- 你的职责是帮助员工完成 HR 相关事务

## 你的能力
1. 政策咨询：查询和解释公司各项 HR 政策
2. 休假管理：查询假期余额、协助请假申请
3. 差旅管理：计算差旅预算、协助差旅申请
4. 证明开具：协助开具各类证明
5. 信息查询：查询员工信息、审批状态等

## 工作原则
1. **Policy Grounding**：回答政策问题时，必须基于检索到的政策原文，不可编造
2. **引用来源**：回答时标注政策依据（如"根据《员工年假管理办法》第X条"）
3. **确认操作**：涉及提交申请等写操作时，必须先展示摘要请用户确认
4. **个性化**：结合当前员工的身份、部门、级别给出个性化建议
5. **诚实边界**：不确定的内容明确告知，不猜测

## 输出格式
- 使用清晰的 Markdown 格式
- 重要信息用 **加粗** 标注
- 列表项用 - 或数字编号
- 涉及金额、天数等关键数据要突出显示`;

// --- Agent Engine ---
export class AgentEngine {
  private config: LLMConfig;
  private conversationHistory: ChatMessage[] = [];
  private maxIterations = 6;

  constructor(config: LLMConfig) {
    this.config = config;
  }

  updateConfig(config: LLMConfig): void {
    this.config = config;
  }

  getHistory(): ChatMessage[] {
    return [...this.conversationHistory];
  }

  clearHistory(): void {
    this.conversationHistory = [];
  }

  async *run(userMessage: string): AsyncGenerator<AgentEvent> {
    // Add user message to history
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    };
    this.conversationHistory.push(userMsg);

    // Retrieve relevant knowledge
    yield { type: 'status', status: 'thinking' };
    yield { type: 'node_enter', node: 'knowledge_retrieval' };

    const knowledge = retrieveKnowledge(userMessage, 3);
    let contextPrompt = '';
    if (knowledge.length > 0) {
      contextPrompt = '\n\n## 相关政策知识（检索结果）\n' +
        knowledge.map((k, i) =>
          `### [${i + 1}] ${k.title}（${k.docId}）\n${k.content}`
        ).join('\n\n');
    }

    yield { type: 'node_exit', node: 'knowledge_retrieval' };

    // ReAct loop
    let iteration = 0;
    const messages: Array<Record<string, unknown>> = [
      { role: 'system', content: SYSTEM_PROMPT + contextPrompt },
      ...this.conversationHistory.map(m => ({
        role: m.role,
        content: m.content,
        ...(m.toolCallId ? { tool_call_id: m.toolCallId } : {}),
        ...(m.name ? { name: m.name } : {}),
      })),
    ];

    while (iteration < this.maxIterations) {
      iteration++;
      yield { type: 'node_enter', node: 'reasoning' };

      try {
        const response = await this.callLLM(messages);
        yield { type: 'node_exit', node: 'reasoning' };

        // Check if there are tool calls
        if (response.toolCalls && response.toolCalls.length > 0) {
          // Add assistant message with tool calls
          messages.push({
            role: 'assistant',
            content: response.content || '',
            tool_calls: response.toolCalls.map(tc => ({
              id: tc.id,
              type: 'function',
              function: { name: tc.name, arguments: JSON.stringify(tc.arguments) },
            })),
          });

          // Execute each tool
          for (const tc of response.toolCalls) {
            yield { type: 'tool_call', toolCall: tc };
            yield { type: 'status', status: 'tool_calling' };
            yield { type: 'node_enter', node: 'tool_execution' };

            const result = await executeTool(tc);
            yield { type: 'tool_result', result };

            // Add tool result to messages
            messages.push({
              role: 'tool',
              tool_call_id: tc.id,
              name: tc.name,
              content: JSON.stringify(result.data || result.error, null, 2),
            });

            yield { type: 'node_exit', node: 'tool_execution' };
          }

          // Continue loop to get final response
          continue;
        }

        // No tool calls - this is the final response
        // Stream the response
        yield { type: 'status', status: 'responding' };
        yield { type: 'node_enter', node: 'response_generation' };

        let fullContent = '';

        if (response.stream) {
          for await (const chunk of response.stream) {
            fullContent += chunk;
            yield { type: 'token', content: chunk };
          }
        } else {
          fullContent = response.content;
          yield { type: 'token', content: response.content };
        }

        yield { type: 'node_exit', node: 'response_generation' };

        // Add to conversation history
        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: fullContent,
          timestamp: Date.now(),
        };
        this.conversationHistory.push(assistantMsg);

        yield { type: 'message_complete', message: assistantMsg };
        yield { type: 'status', status: 'idle' };
        return;

      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        yield { type: 'error', error: errorMsg };
        yield { type: 'status', status: 'error' };
        return;
      }
    }

    // Max iterations reached
    yield { type: 'error', error: 'Agent 达到最大迭代次数，请简化您的问题' };
    yield { type: 'status', status: 'idle' };
  }

  // --- Call LLM API ---
  private async callLLM(messages: Array<Record<string, unknown>>): Promise<{
    content: string;
    toolCalls?: ToolCallInfo[];
    stream?: AsyncIterable<string>;
  }> {
    const { baseUrl, apiKey, model, temperature, maxTokens } = this.config;

    if (!apiKey) {
      throw new Error('请先配置 API Key（点击右上角设置按钮）');
    }

    const url = `${baseUrl.replace(/\/$/, '')}/chat/completions`;

    const body = {
      model,
      messages: messages.map(m => {
        if (m.role === 'tool') {
          return { role: 'tool', tool_call_id: m.tool_call_id, content: m.content };
        }
        if (m.tool_calls) {
          return { role: 'assistant', content: m.content, tool_calls: m.tool_calls };
        }
        return { role: m.role, content: m.content };
      }),
      tools: getToolsForLLM(),
      temperature,
      max_tokens: maxTokens,
      stream: true,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`LLM API 错误 (${response.status}): ${errorText}`);
    }

    // Parse SSE stream
    return this.parseStream(response);
  }

  // --- Parse SSE Stream ---
  private async parseStream(response: Response): Promise<{
    content: string;
    toolCalls?: ToolCallInfo[];
    stream?: AsyncIterable<string>;
  }> {
    const reader = response.body?.getReader();
    if (!reader) throw new Error('无法读取响应流');

    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';
    const toolCallsMap: Map<number, ToolCallInfo & { _argsStr?: string }> = new Map();
    const chunks: string[] = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (data === '[DONE]') continue;

        try {
          const parsed = JSON.parse(data);
          const delta = parsed.choices?.[0]?.delta;
          if (!delta) continue;

          if (delta.tool_calls) {
            for (const tc of delta.tool_calls) {
              const idx = tc.index;
              if (!toolCallsMap.has(idx)) {
                toolCallsMap.set(idx, {
                  id: tc.id || '',
                  name: tc.function?.name || '',
                  arguments: {},
                  _argsStr: '',
                });
              }
              const existing = toolCallsMap.get(idx)!;
              if (tc.id) existing.id = tc.id;
              if (tc.function?.name) existing.name = tc.function.name;
              if (tc.function?.arguments) {
                existing._argsStr = (existing._argsStr || '') + tc.function.arguments;
              }
            }
          }

          if (delta.content) {
            chunks.push(delta.content);
            fullContent += delta.content;
          }
        } catch {
          // Skip malformed JSON
        }
      }
    }

    if (toolCallsMap.size > 0) {
      const toolCalls: ToolCallInfo[] = Array.from(toolCallsMap.values()).map(tc => {
        try {
          tc.arguments = JSON.parse(tc._argsStr || '{}');
        } catch {
          tc.arguments = {};
        }
        return { id: tc.id, name: tc.name, arguments: tc.arguments };
      });
      return { content: fullContent, toolCalls };
    }

    const self = this;
    async function* genChunks() {
      for (const chunk of chunks) {
        yield chunk;
      }
    }

    return { content: fullContent, stream: genChunks() };
  }
}
