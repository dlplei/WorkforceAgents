export default function RoadmapSection() {
  const phases = [
    {
      phase: 'Phase 1',
      title: '基础能力构建',
      duration: 'Month 1-3',
      color: 'blue',
      status: 'current',
      goals: [
        '搭建 Agent 基础框架 (LangGraph)',
        '接入 LLM (GPT-4) + 基础 Prompt 工程',
        '实现政策知识库 RAG',
        '完成员工 Profile 上下文加载',
        '上线政策咨询场景 (FAQ)',
      ],
      deliverables: ['Agent 框架 MVP', '政策知识库 v1', 'IM 集成 (钉钉)', '基础监控'],
      kpis: ['意图识别准确率 > 85%', '政策问答准确率 > 90%', '响应时间 < 3s'],
    },
    {
      phase: 'Phase 2',
      title: '核心场景落地',
      duration: 'Month 4-6',
      color: 'purple',
      status: 'planned',
      goals: [
        '实现休假管理全流程',
        '实现差旅申请与报销',
        '接入 HRIS 系统 (Workday)',
        '实现审批流集成',
        '完善 Memory 系统',
      ],
      deliverables: ['休假管理功能', '差旅管理功能', 'HRIS 集成', '审批流对接'],
      kpis: ['任务完成率 > 80%', '用户满意度 > 4.0/5', '人工干预率 < 30%'],
    },
    {
      phase: 'Phase 3',
      title: '智能化增强',
      duration: 'Month 7-9',
      color: 'cyan',
      status: 'planned',
      goals: [
        '实现员工调动场景',
          '多 Agent 协作 (复杂任务)',
        '主动服务推送 (Proactive)',
        '个性化推荐引擎',
        'A/B 测试框架',
      ],
      deliverables: ['调动管理功能', '多 Agent 编排', '主动推送引擎', '效果评估系统'],
      kpis: ['任务完成率 > 90%', '主动服务采纳率 > 60%', 'Token 成本优化 30%'],
    },
    {
      phase: 'Phase 4',
      title: '规模化运营',
      duration: 'Month 10-12',
      color: 'green',
      status: 'planned',
      goals: [
        '全场景覆盖 (HR Service Request)',
        '多语言支持',
        '全公司推广',
        '持续优化与反馈闭环',
        '合规审计完善',
      ],
      deliverables: ['全场景上线', '多语言版本', '运营 Dashboard', '合规报告'],
      kpis: ['员工覆盖率 > 80%', 'HR 工单减少 40%', 'NPS > 50'],
    },
  ];

  const colorClasses: Record<string, { bg: string; border: string; text: string; dot: string; badge: string }> = {
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-500', badge: 'bg-blue-500/20 text-blue-300' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-500', badge: 'bg-purple-500/20 text-purple-300' },
    cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400', dot: 'bg-cyan-500', badge: 'bg-cyan-500/20 text-cyan-300' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-500', badge: 'bg-green-500/20 text-green-300' },
  };

  return (
    <section id="roadmap" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">
              实施路线图
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            分四个阶段推进，从 MVP 到全面上线，每阶段有明确目标和交付物
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Horizontal line */}
          <div className="hidden lg:block absolute top-12 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 via-cyan-500 to-green-500"></div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {phases.map((phase) => {
              const colors = colorClasses[phase.color];
              return (
                <div key={phase.phase} className="relative">
                  {/* Timeline dot */}
                  <div className="hidden lg:flex absolute top-8 left-1/2 -translate-x-1/2 z-10">
                    <div className={`w-8 h-8 rounded-full ${colors.dot} flex items-center justify-center shadow-lg ${phase.status === 'current' ? 'ring-4 ring-white/20 animate-pulse' : ''}`}>
                      <span className="text-xs font-bold text-white">{phase.phase.slice(-1)}</span>
                    </div>
                  </div>

                  {/* Card */}
                  <div className={`${colors.bg} ${colors.border} border rounded-xl p-5 mt-0 lg:mt-16`}>
                    <div className="flex items-center justify-between mb-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${colors.badge}`}>
                        {phase.duration}
                      </span>
                      {phase.status === 'current' && (
                        <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-300 flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                          <span>进行中</span>
                        </span>
                      )}
                    </div>

                    <h3 className="text-lg font-bold text-white mb-1">{phase.title}</h3>
                    <p className={`text-xs ${colors.text} mb-4`}>{phase.phase}</p>

                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2">目标</h4>
                        <ul className="space-y-1">
                          {phase.goals.map((goal, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start space-x-1.5">
                              <i className={`fas fa-check mt-0.5 text-[8px] ${colors.text}`}></i>
                              <span>{goal}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2">交付物</h4>
                        <div className="flex flex-wrap gap-1">
                          {phase.deliverables.map((d, i) => (
                            <span key={i} className="text-[10px] bg-slate-700/50 px-2 py-0.5 rounded text-slate-300">
                              {d}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2">KPI</h4>
                        <ul className="space-y-1">
                          {phase.kpis.map((kpi, i) => (
                            <li key={i} className="text-[10px] text-slate-400 flex items-center space-x-1">
                              <i className="fas fa-chart-bar text-[8px] text-slate-500"></i>
                              <span>{kpi}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Team Structure */}
        <div className="mt-16 bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">建议团队配置</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { role: 'AI/LLM 工程师', count: '2-3', icon: 'fa-brain' },
              { role: '后端工程师', count: '2-3', icon: 'fa-server' },
              { role: '前端工程师', count: '1-2', icon: 'fa-code' },
              { role: 'HR 领域专家', count: '1-2', icon: 'fa-user-tie' },
              { role: '产品经理', count: '1', icon: 'fa-lightbulb' },
              { role: '安全/合规', count: '1', icon: 'fa-shield-alt' },
            ].map((member, i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-center">
                <div className="w-10 h-10 mx-auto mb-2 bg-slate-700/50 rounded-lg flex items-center justify-center">
                  <i className={`fas ${member.icon} text-slate-400`}></i>
                </div>
                <div className="text-sm font-medium text-white">{member.role}</div>
                <div className="text-xs text-slate-400 mt-1">{member.count} 人</div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Risks */}
        <div className="mt-8 bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">关键风险与应对</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { risk: 'LLM 幻觉风险', mitigation: 'Policy Grounding + 输出校验 + Guardrails', level: 'high' },
              { risk: '数据安全泄露', mitigation: '脱敏 + 最小权限 + 审计日志', level: 'high' },
              { risk: '系统集成复杂度', mitigation: '标准化 API 封装 + 渐进式接入', level: 'medium' },
              { risk: '用户接受度', mitigation: '渐进推广 + 反馈闭环 + 人工兜底', level: 'medium' },
              { risk: '成本控制', mitigation: '模型分级 + 缓存策略 + Token 预算', level: 'medium' },
              { risk: '合规风险', mitigation: '法务审核 + 合规评估 + 定期审计', level: 'high' },
            ].map((item, i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">{item.risk}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    item.level === 'high' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {item.level === 'high' ? '高风险' : '中风险'}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  <span className="text-slate-500">应对: </span>{item.mitigation}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
