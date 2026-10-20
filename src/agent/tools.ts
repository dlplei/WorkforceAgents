// ============================================================
// Tool Calling Framework - Pluggable Tools
// ============================================================
import type { ToolDefinition, ToolResult, ToolCallInfo } from '../types';
import { currentEmployee, mockEmployees, mockApprovals, mockCalendarEvents } from '../config';
import { retrieveKnowledge } from './knowledge';

// --- Tool Registry ---
const toolRegistry: Map<string, ToolDefinition> = new Map();

export function registerTool(tool: ToolDefinition): void {
  toolRegistry.set(tool.name, tool);
}

export function getTool(name: string): ToolDefinition | undefined {
  return toolRegistry.get(name);
}

export function getAllTools(): ToolDefinition[] {
  return Array.from(toolRegistry.values());
}

export function getToolsForLLM(): Array<{
  type: 'function';
  function: { name: string; description: string; parameters: unknown };
}> {
  return getAllTools().map(t => ({
    type: 'function' as const,
    function: {
      name: t.name,
      description: t.description,
      parameters: t.parameters,
    },
  }));
}

// --- Execute Tool ---
export async function executeTool(call: ToolCallInfo): Promise<ToolResult> {
  const tool = getTool(call.name);
  if (!tool) {
    return {
      toolName: call.name,
      success: false,
      data: null,
      error: `Tool "${call.name}" not found`,
      executionTime: 0,
    };
  }

  const start = performance.now();
  try {
    const result = await tool.handler(call.arguments);
    return {
      toolName: call.name,
      success: result.success,
      data: result.data,
      error: result.error,
      executionTime: performance.now() - start,
    };
  } catch (err) {
    return {
      toolName: call.name,
      success: false,
      data: null,
      error: err instanceof Error ? err.message : String(err),
      executionTime: performance.now() - start,
    };
  }
}

// ============================================================
// Tool Definitions
// ============================================================

// --- 1. Query Leave Balance ---
registerTool({
  name: 'query_leave_balance',
  description: '查询指定员工的假期余额，包括年假、病假、事假等。如果不指定员工ID，则查询当前登录员工。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      employee_id: { type: 'string', description: '员工ID，不填则查询当前员工' },
      leave_type: { type: 'string', description: '假期类型：annual(年假)/sick(病假)/personal(事假)，不填则查询全部', enum: ['annual', 'sick', 'personal'] },
    },
    required: [],
  },
  handler: async (params) => {
    const empId = (params.employee_id as string) || currentEmployee.id;
    const emp = mockEmployees[empId];
    if (!emp) return { success: false, data: null, error: `员工 ${empId} 不存在` };

    const leaveType = params.leave_type as string | undefined;
    if (leaveType) {
      const balance = emp.leaveBalance[leaveType as keyof typeof emp.leaveBalance];
      return { success: true, data: { employee: emp.name, leave_type: leaveType, balance } };
    }
    return { success: true, data: { employee: emp.name, leave_balance: emp.leaveBalance } };
  },
});

// --- 2. Query Employee Profile ---
registerTool({
  name: 'query_employee_profile',
  description: '查询员工的基本信息，包括部门、职位、汇报关系、入职日期等。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      employee_id: { type: 'string', description: '员工ID' },
    },
    required: ['employee_id'],
  },
  handler: async (params) => {
    const emp = mockEmployees[params.employee_id as string];
    if (!emp) return { success: false, data: null, error: '员工不存在' };
    return { success: true, data: emp };
  },
});

// --- 3. Search Policy ---
registerTool({
  name: 'search_policy',
  description: '检索企业政策知识库，返回与查询相关的政策条款。支持按类别过滤。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      query: { type: 'string', description: '查询关键词或问题' },
      category: { type: 'string', description: '政策类别过滤', enum: ['休假', '差旅', '调动', '服务', '考勤', '福利'] },
      top_k: { type: 'string', description: '返回结果数量，默认3' },
    },
    required: ['query'],
  },
  handler: async (params) => {
    const results = retrieveKnowledge(
      params.query as string,
      parseInt(params.top_k as string) || 3,
      params.category as string | undefined
    );
    return { success: true, data: results };
  },
});

// --- 4. Check Calendar Conflict ---
registerTool({
  name: 'check_calendar',
  description: '检查指定日期范围内是否有日历冲突（会议、项目里程碑等）。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      start_date: { type: 'string', description: '开始日期，格式 YYYY-MM-DD' },
      end_date: { type: 'string', description: '结束日期，格式 YYYY-MM-DD' },
    },
    required: ['start_date', 'end_date'],
  },
  handler: async (params) => {
    const start = params.start_date as string;
    const end = params.end_date as string;
    const conflicts = mockCalendarEvents.filter(e => e.date >= start && e.date <= end);
    return {
      success: true,
      data: {
        start_date: start,
        end_date: end,
        conflicts,
        has_conflict: conflicts.length > 0,
      },
    };
  },
});

// --- 5. Submit Leave Request ---
registerTool({
  name: 'submit_leave_request',
  description: '提交休假申请。这是一个需要确认的操作，会创建审批流程。',
  category: 'action',
  permissionLevel: 'confirmation',
  parameters: {
    type: 'object',
    properties: {
      leave_type: { type: 'string', description: '假期类型', enum: ['annual', 'sick', 'personal'] },
      start_date: { type: 'string', description: '开始日期 YYYY-MM-DD' },
      end_date: { type: 'string', description: '结束日期 YYYY-MM-DD' },
      reason: { type: 'string', description: '请假原因' },
    },
    required: ['leave_type', 'start_date', 'end_date'],
  },
  handler: async (params) => {
    const requestId = `LV-${Date.now().toString(36).toUpperCase()}`;
    return {
      success: true,
      data: {
        request_id: requestId,
        status: 'pending_approval',
        approver: currentEmployee.manager,
        leave_type: params.leave_type,
        start_date: params.start_date,
        end_date: params.end_date,
        message: `休假申请已提交，等待 ${currentEmployee.manager} 审批`,
      },
    };
  },
});

// --- 6. Query Approval Status ---
registerTool({
  name: 'query_approval_status',
  description: '查询审批流程状态。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      request_id: { type: 'string', description: '申请单号' },
    },
    required: [],
  },
  handler: async (params) => {
    if (params.request_id) {
      return {
        success: true,
        data: {
          request_id: params.request_id,
          status: 'pending_approval',
          current_approver: currentEmployee.manager,
          submitted_at: '2026-01-15T10:30:00',
        },
      };
    }
    return { success: true, data: { approvals: mockApprovals } };
  },
});

// --- 7. Calculate Travel Budget ---
registerTool({
  name: 'calculate_travel_budget',
  description: '根据出差目的地、天数和员工级别计算差旅预算（住宿+餐饮+交通标准）。',
  category: 'query',
  permissionLevel: 'autonomous',
  parameters: {
    type: 'object',
    properties: {
      destination: { type: 'string', description: '目的地城市' },
      days: { type: 'string', description: '出差天数' },
      city_tier: { type: 'string', description: '城市级别', enum: ['一线', '二线', '三线及以下'] },
    },
    required: ['destination', 'days', 'city_tier'],
  },
  handler: async (params) => {
    const days = parseInt(params.days as string);
    const tier = params.city_tier as string;
    const level = currentEmployee.level;

    const accommodation: Record<string, Record<string, number>> = {
      '一线': { 'P5': 400, 'P6': 600, 'P7': 600, 'P8': 1000 },
      '二线': { 'P5': 300, 'P6': 500, 'P7': 500, 'P8': 800 },
      '三线及以下': { 'P5': 250, 'P6': 400, 'P7': 400, 'P8': 600 },
    };
    const meal: Record<string, number> = { '一线': 100, '二线': 80, '三线及以下': 60 };

    const accRate = accommodation[tier]?.[level] || 400;
    const mealRate = meal[tier] || 80;

    return {
      success: true,
      data: {
        destination: params.destination,
        days,
        employee_level: level,
        accommodation_per_night: accRate,
        meal_per_day: mealRate,
        total_accommodation: accRate * (days - 1),
        total_meal: mealRate * days,
        total_budget: accRate * (days - 1) + mealRate * days,
        note: '交通费需根据实际出行方式另行计算',
      },
    };
  },
});

// --- 8. Generate Document ---
registerTool({
  name: 'generate_document',
  description: '生成各类证明文件（在职证明、收入证明等）。',
  category: 'action',
  permissionLevel: 'confirmation',
  parameters: {
    type: 'object',
    properties: {
      doc_type: { type: 'string', description: '证明类型', enum: ['在职证明', '收入证明', '离职证明'] },
      purpose: { type: 'string', description: '用途（如：贷款、签证等）' },
      language: { type: 'string', description: '语言版本', enum: ['中文', '英文'] },
    },
    required: ['doc_type'],
  },
  handler: async (params) => {
    return {
      success: true,
      data: {
        document_id: `DOC-${Date.now().toString(36).toUpperCase()}`,
        type: params.doc_type,
        employee: currentEmployee.name,
        status: 'processing',
        estimated_time: '1-2个工作日',
        message: `${params.doc_type}申请已提交，预计1-2个工作日内完成`,
      },
    };
  },
});
