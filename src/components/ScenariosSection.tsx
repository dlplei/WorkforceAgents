export default function ScenariosSection() {
  const scenarios = [
    {
      icon: 'fa-calendar-check', title: '休假管理', color: 'blue',
      desc: '员工通过自然语言完成请假申请、余额查询、假期类型推荐',
      features: ['自然语言请假', '自动查询余额与政策', '智能推荐最优方案', '审批材料自动生成', '状态追踪与提醒'],
    },
    {
      icon: 'fa-plane', title: '差旅管理', color: 'cyan',
      desc: '从出差申请到报销的全流程智能化服务',
      features: ['申请自动生成', '差旅政策合规检查', '超标预警', '机票酒店预订推荐', '报销单据智能整理'],
    },
    {
      icon: 'fa-exchange-alt', title: '员工调动', color: 'purple',
      desc: '支持跨部门、跨地区调动流程的智能化引导与执行',
      features: ['调动意向确认', '影响评估（薪酬/社保）', '方案对比报告', '多部门审批协调', '系统信息自动更新'],
    },
    {
      icon: 'fa-book', title: '政策咨询', color: 'green',
      desc: '基于企业政策知识库的精准问答与指引',
      features: ['RAG 精准回答', '多轮对话澄清', '个性化政策解读', '政策变更通知', '关联流程触发'],
    },
    {
      icon: 'fa-clipboard-check', title: '审批准备', color: 'amber',
      desc: '智能准备审批材料，加速审批流程',
      features: ['自动收集审批信息', '结构化材料生成', '通过率预估', '审批人偏好适配', '催办与追踪'],
    },
    {
      icon: 'fa-headset', title: 'HR Service Request', color: 'rose',
      desc: '各类 HR 服务请求的统一入口与智能处理',
      features: ['证明开具', '信息变更', '社保公积金咨询', '入离职 Checklist', '工单自动创建'],
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

  return (
    <section id="scenarios" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">典型业务场景</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">六大核心业务场景，覆盖员工日常 HR 服务的主要需求</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {scenarios.map((s, i) => {
            const c = colorMap[s.color];
            return (
              <div key={i} className={`${c.bg} ${c.border} border rounded-xl p-5 hover:scale-[1.02] transition-transform`}>
                <div className="flex items-center space-x-3 mb-3">
                  <div className={`w-10 h-10 rounded-lg ${c.bg} border ${c.border} flex items-center justify-center`}>
                    <i className={`fas ${s.icon} ${c.icon}`}></i>
                  </div>
                  <h3 className={`font-bold ${c.text}`}>{s.title}</h3>
                </div>
                <p className="text-sm text-slate-400 mb-3">{s.desc}</p>
                <ul className="space-y-1.5">
                  {s.features.map((f, j) => (
                    <li key={j} className="text-xs text-slate-300 flex items-center space-x-2">
                      <i className={`fas fa-check ${c.icon} text-[10px]`}></i>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
