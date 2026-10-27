// ============================================================
// Configuration
// ============================================================

export interface AppConfig {
  backendUrl: string;    // 本地 FastAPI 后端地址
  llmBaseUrl: string;    // LLM API 服务地址
  apiKey: string;        // LLM API Key
  model: string;
  temperature: number;
  maxTokens: number;
}

export const defaultConfig: AppConfig = {
  // 默认留空 => 前端用相对路径 /api/*，由 Vite dev server 代理到后端（同源、无 CORS、不受浏览器代理影响）。
  // 如需直连后端，可在设置面板填入 http://localhost:8000
  backendUrl: '',
  llmBaseUrl: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-4o-mini',
  temperature: 0.7,
  maxTokens: 2048,
};

// Load/save config from localStorage
export function loadConfig(): AppConfig {
  try {
    const saved = localStorage.getItem('woa_config');
    if (saved) return { ...defaultConfig, ...JSON.parse(saved) };
  } catch { /* ignore */ }
  return { ...defaultConfig };
}

export function saveConfig(config: AppConfig): void {
  localStorage.setItem('woa_config', JSON.stringify(config));
}

// Mock employee data (for UI display only)
export const currentEmployee = {
  id: 'E10293',
  name: '张明',
  department: '技术研发部',
  position: '高级前端工程师',
  level: 'P6',
  location: '北京',
  manager: '李伟',
  leaveBalance: { annual: 7, sick: 5, personal: 2 },
};
