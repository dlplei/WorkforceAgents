import { useState } from 'react';

const modules = [
  {
    id: 'leave',
    icon: 'fa-calendar-check',
    title: '休假管理',
    color: 'blue',
    description: '员工通过自然语言完成请假申请、余额查询、假期类型推荐',
    features: [
      '自然语言请假："我下周三到周五想请年假"',
      '自动查询假期余额与政策',
      '智能推荐最优请假方案（结合项目排期）',
      '自动生成审批所需材料',
      '审批状态追踪与提醒',
    ],
    tools: ['HRIS 假期余额查询', '日历系统排期检查', '审批流提交', '消息通知'],
  },
  {
    id: 'transfer',
    icon: 'fa-exchange-alt',
    title: '员工调动',
    color: 'purple',
    description: '支持跨部门、跨地区调动流程的智能化引导与执行',
    features: [
      '调动意向确认与政策匹配',
      '自动评估调动影响（薪酬、福利、社保）',
      '生成调动方案对比报告',
      '协调多部门审批流程',
      '调动后系统信息自动更新',
    ],
    tools: ['组织架构查询', '薪酬计算引擎', '社保公积金计算器', '审批流编排'],
  },
  {
    id: 'travel',
    icon: 'fa-plane',
    title: '差旅管理',
    color: 'cyan',
    description: '从出差申请到报销的全流程智能化服务',
    features: [
      '出差申请自动生成（基于会议/项目信息）',
      '差旅政策合规检查',
      '机票酒店预订推荐（符合差标）',
      '行程单自动生成与审批',
      '报销单据智能整理与提交',
    ],
    tools: ['差旅政策引擎', 'TMC 预订接口', '日历协调', '财务报销系统'],
  },
  {
    id: 'policy',
    icon: 'fa-book',
    title: '政策咨询',
    color: 'green',
    description: '基于企业政策知识库的精准问答与指引',
    features: [
      'RAG 驱动的政策精准回答',
      '多轮对话澄清模糊需求',
      '个性化政策解读（结合员工身份）',
      '政策变更主动通知',
      '关联流程一键触发',
    ],
    tools: ['向量知识库检索', '员工信息上下文', '政策版本管理', '流程触发器'],
  },
  {
    id: 'approval',
    icon: 'fa-clipboard-check',
    title: '审批准备',
    color: 'amber',
    description: '智能准备审批材料，加速审批流程',
    features: [
      '自动收集审批所需信息',
      '生成结构化审批材料',
      '预检查审批通过概率',
      '审批人偏好适配',
      '催办与状态追踪',
    ],
    tools: ['文档生成引擎', '审批历史分析', '组织架构查询', '消息推送'],
  },
  {
    id: 'service',
    icon: 'fa-headset',
    title: 'HR Service Request',
    color: 'rose',
    description: '各类 HR 服务请求的统一入口与智能处理',
    features: [
      '证明开具（在职/收入/离职）',
      '信息变更（银行卡/地址/紧急联系人）',
      '社保公积金咨询与办理',
      '入职/离职 Checklist 引导',
      '工单自动创建与追踪',
    ],
    tools: ['文档模板引擎', 'HRIS 信息更新', '工单系统', '电子签章'],
  },
];

const colorMap: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-300', icon: 'text-blue-400' },
  purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-300', icon: 'text-purple-400' },
  cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-300', icon: 'text-cyan-400' },
  green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-300', icon: 'text-green-400' },
  amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-300', icon: 'text-amber-400' },
  rose: { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-300', icon: 'text-rose-400' },
};

export default function CoreModules() {
  const [activeModule, setActiveModule] = useState(modules[0].id);
  const currentModule = modules.find(m => m.id === activeModule) || modules[0];
  const colors = colorMap[currentModule.color];

  return (
    <section id="modules" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              核心功能模块
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            六大核心业务场景，覆盖员工日常 HR 服务的主要需求
          </p>
        </div>

        {/* Module Tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {modules.map((module) => {
            const c = colorMap[module.color];
            return (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeModule === module.id
                    ? `${c.bg} ${c.border} border ${c.text}`
                    : 'bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:text-white hover:border-slate-600'
                }`}
              >
                <i className={`fas ${module.icon} ${activeModule === module.id ? c.icon : ''}`}></i>
                <span>{module.title}</span>
              </button>
            );
          })}
        </div>

        {/* Module Detail */}
        <div className={`${colors.bg} ${colors.border} border rounded-2xl p-6 sm:p-8 transition-all`}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className={`w-12 h-12 rounded-xl ${colors.bg} border ${colors.border} flex items-center justify-center`}>
                  <i className={`fas ${currentModule.icon} text-xl ${colors.icon}`}></i>
                </div>
                <div>
                  <h3 className={`text-xl font-bold ${colors.text}`}>{currentModule.title}</h3>
                  <p className="text-sm text-slate-400">{currentModule.description}</p>
                </div>
              </div>

              <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                <i className="fas fa-sparkles mr-2 text-yellow-400"></i>
                Agent 能力
              </h4>
              <ul className="space-y-2">
                {currentModule.features.map((feature, i) => (
                  <li key={i} className="flex items-start space-x-2 text-sm text-slate-300">
                    <i className={`fas fa-check-circle mt-0.5 ${colors.icon} text-xs`}></i>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                <i className="fas fa-wrench mr-2 text-cyan-400"></i>
                调用的工具 (Tools)
              </h4>
              <div className="space-y-2">
                {currentModule.tools.map((tool, i) => (
                  <div key={i} className="bg-slate-800/80 border border-slate-600/50 rounded-lg p-3 flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-lg ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                      <span className="text-xs font-mono font-bold text-slate-300">T{i + 1}</span>
                    </div>
                    <span className="text-sm text-slate-300">{tool}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6 bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">示例对话</h4>
                <div className="space-y-2">
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-user text-xs text-blue-400"></i>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg rounded-tl-none px-3 py-2 text-xs text-slate-300">
                      "我下周想请两天年假去看演唱会，帮我看看怎么请最划算"
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-robot text-xs text-purple-400"></i>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg rounded-tl-none px-3 py-2 text-xs text-slate-300">
                      "好的，我来帮您查看。您目前年假余额 8 天。下周三四请假可以连周末形成 4 天假期，且不影响周三的项目评审会。需要我帮您提交申请吗？"
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
