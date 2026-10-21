// ============================================================
// Configuration
// ============================================================

export interface AppConfig {
  backendUrl: string;
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

export const defaultConfig: AppConfig = {
  backendUrl: 'http://localhost:8000',
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
