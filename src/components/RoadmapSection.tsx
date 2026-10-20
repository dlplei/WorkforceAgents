export default function RoadmapSection() {
  const phases = [
    {
      phase: 'Phase 1', title: 'MVP 基础能力', duration: '6-10 周', color: 'blue', status: 'current',
      goals: ['搭建 Agent 基础框架 (LangGraph)', '接入 LLM + Prompt 工程', '实现政策知识库 RAG', 'HR 政策问答 + 年假余额查询', '休假申请草稿 + HR 工单创建', '审批状态查询'],
      kpis: ['意图识别准确率 > 85%', '政策问答准确率 > 90%', '响应时间 < 3s'],
    },
    {
      phase: 'Phase 2', title: '流程型 Agent', duration: '8-12 周', color: 'purple', status: 'planned',
      goals: ['差旅申请全流程', '证明开具 + 信息变更', '入职/离职服务引导', '转岗/调动流程准备', '完善 Memory + HITL', '接入 HRIS (Workday)'],
      kpis: ['任务完成率 > 80%', '用户满意度 > 4.0/5', '人工干预率 < 30%'],
    },
    {
      phase: 'Phase 3', title: '智能运营优化', duration: '持续迭代', color: 'green', status: 'planned',
      goals: ['假期到期主动提醒', '新员工入职任务跟进', '审批超时提醒', '工单自动分类分派', '多语言 + 全场景覆盖', '体验分析与洞察'],
      kpis: ['任务完成率 > 90%', '员工覆盖率 > 80%', 'HR 工单减少 40%', 'NPS > 50'],
    },
  ];

  const team = [
    { role: 'AI/LLM 工程师', count: '2-3', icon: 'fa-brain' },
    { role: '后端工程师', count: '2-3', icon: 'fa-server' },
    { role: '前端工程师', count: '1-2', icon: 'fa-code' },
    { role: 'HR 领域专家', count: '1-2', icon: 'fa-user-tie' },
    { role: '产品经理', count: '1', icon: 'fa-lightbulb' },
    { role: '安全/合规', count: '1', icon: 'fa-shield-alt' },
  ];

  const risks = [
    { risk: 'LLM 幻觉风险', level: 'high', mitigation: 'Policy Grounding + 输出校验 + Guardrails + 引用溯源' },
    { risk: '数据安全泄露', level: 'high', mitigation: '脱敏 + 最小权限 + 审计日志 + 数据分级' },
    { risk: '合规风险', level: 'high', mitigation: '法务审核 + 合规评估 + 定期审计 + PIPL/GDPR 对齐' },
    { risk: '系统集成复杂度', level: 'medium', mitigation: '标准化 API 封装 + 渐进式接入 + 适配器模式' },
    { risk: '用户接受度', level: 'medium', mitigation: '渐进推广 + 反馈闭环 + 人工兜底 + 体验优化' },
    { risk: '成本控制', level: 'medium', mitigation: '模型分级 + 缓存策略 + Token 预算 + 用量监控' },
  ];

  const colorMap: Record<string, { bg: string; border: string; text: string; dot: string; badge: string }> = {
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-500', badge: 'bg-blue-500/20 text-blue-300' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-500', badge: 'bg-purple-500/20 text-purple-300' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-500', badge: 'bg-green-500/20 text-green-300' },
  };

  return (
    <section id="roadmap" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">实施路线图</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">分三阶段推进 + 团队配置 + 风险分析</p>
        </div>

        {/* Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-12">
          {phases.map((phase) => {
            const c = colorMap[phase.color];
            return (
              <div key={phase.phase} className={`${c.bg} ${c.border} border rounded-xl p-5`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs px-2 py-1 rounded-full ${c.badge}`}>{phase.duration}</span>
                  {phase.status === 'current' && (
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-300 flex items-center space-x-1">
                      <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                      <span>进行中</span>
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-bold text-white mb-1">{phase.title}</h3>
                <p className={`text-xs ${c.text} mb-3`}>{phase.phase}</p>
                <div className="space-y-3">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 mb-2">目标</h4>
                    <ul className="space-y-1">
                      {phase.goals.map((goal, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start space-x-1.5">
                          <i className={`fas fa-check mt-0.5 text-[8px] ${c.text}`}></i><span>{goal}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 mb-2">KPI</h4>
                    <div className="flex flex-wrap gap-1">
                      {phase.kpis.map((kpi, i) => (
                        <span key={i} className="text-[10px] bg-green-500/10 text-green-300 px-2 py-0.5 rounded">{kpi}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Team */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-5 text-center">建议团队配置</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {team.map((m, i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 text-center">
                <div className="w-9 h-9 mx-auto mb-2 bg-slate-700/50 rounded-lg flex items-center justify-center">
                  <i className={`fas ${m.icon} text-slate-400 text-sm`}></i>
                </div>
                <div className="text-xs font-medium text-white">{m.role}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">{m.count} 人</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 text-center mt-3">建议核心团队 8-12 人，可根据企业规模调整</p>
        </div>

        {/* Risks */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-5 text-center">关键风险与应对</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-2 px-3 text-slate-300 font-semibold">风险</th>
                  <th className="text-left py-2 px-3 text-slate-300 font-semibold">等级</th>
                  <th className="text-left py-2 px-3 text-slate-300 font-semibold">应对措施</th>
                </tr>
              </thead>
              <tbody>
                {risks.map((r, i) => (
                  <tr key={i} className="border-b border-slate-700/50">
                    <td className="py-2 px-3 text-slate-300">{r.risk}</td>
                    <td className="py-2 px-3">
                      <span className={`text-xs px-2 py-0.5 rounded ${r.level === 'high' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
                        {r.level === 'high' ? '高' : '中'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400 text-xs">{r.mitigation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
