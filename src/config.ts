// ============================================================
// Configuration & Mock Data
// ============================================================
import type { LLMConfig, EmployeeProfile } from './types';

// --- LLM Configuration (user-configurable via UI) ---
export const defaultLLMConfig: LLMConfig = {
  baseUrl: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-4o-mini',
  embeddingModel: 'text-embedding-3-small',
  temperature: 0.7,
  maxTokens: 2048,
};

// Load/save config from localStorage
export function loadConfig(): LLMConfig {
  try {
    const saved = localStorage.getItem('woa_config');
    if (saved) return { ...defaultLLMConfig, ...JSON.parse(saved) };
  } catch { /* ignore */ }
  return { ...defaultLLMConfig };
}

export function saveConfig(config: LLMConfig): void {
  localStorage.setItem('woa_config', JSON.stringify(config));
}

// --- Mock Employee Data ---
export const mockEmployees: Record<string, EmployeeProfile> = {
  'E10293': {
    id: 'E10293',
    name: '张明',
    department: '技术研发部',
    position: '高级前端工程师',
    level: 'P6',
    location: '北京',
    manager: '李伟',
    hireDate: '2022-03-15',
    contractType: '全职',
    leaveBalance: { annual: 7, sick: 5, personal: 2 },
    benefits: ['五险一金', '补充商业保险', '年度体检', '弹性工作'],
  },
  'E10456': {
    id: 'E10456',
    name: '王芳',
    department: '人力资源部',
    position: 'HRBP',
    level: 'P7',
    location: '上海',
    manager: '赵静',
    hireDate: '2020-08-01',
    contractType: '全职',
    leaveBalance: { annual: 12, sick: 8, personal: 3 },
    benefits: ['五险一金', '补充商业保险', '年度体检', '弹性工作', '股票期权'],
  },
};

// Default logged-in employee
export const currentEmployeeId = 'E10293';
export const currentEmployee = mockEmployees[currentEmployeeId];

// --- Mock Approval Data ---
export const mockApprovals = [
  { id: 'APR-001', type: '年假申请', status: 'pending', applicant: '张明', date: '2026-01-15' },
  { id: 'APR-002', type: '差旅报销', status: 'approved', applicant: '张明', date: '2026-01-10' },
];

// --- Mock Calendar ---
export const mockCalendarEvents = [
  { date: '2026-01-20', title: '项目评审会', type: 'meeting' },
  { date: '2026-01-22', title: 'Sprint Planning', type: 'meeting' },
  { date: '2026-02-01', title: '春节假期开始', type: 'holiday' },
];
