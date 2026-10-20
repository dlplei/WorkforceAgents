export default function ContextSection() {
  const memoryTypes = [
    { title: '工作记忆', subtitle: 'Working Memory', icon: 'fa-microchip', desc: '当前会话上下文，短期保持', tech: 'Redis + In-Context Window', ttl: '会话期间', bgClass: 'bg-blue-500/10 border-blue-500/20', iconClass: 'text-blue-400' },
    { title: '情景记忆', subtitle: 'Episodic Memory', icon: 'fa-history', desc: '历史交互记录，支持检索', tech: 'Vector DB + PostgreSQL', ttl: '永久（可定期清理）', bgClass: 'bg-purple-500/10 border-purple-500/20', iconClass: 'text-purple-400' },
    { title: '语义记忆', subtitle: 'Semantic Memory', icon: 'fa-book-open', desc: '企业政策、流程知识', tech: 'Vector DB + Elasticsearch', ttl: '随政策更新', bgClass: 'bg-cyan-500/10 border-cyan-500/20', iconClass: 'text-cyan-400' },
    { title: '用户画像', subtitle: 'User Profile Memory', icon: 'fa-id-card', desc: '员工偏好、行为模式', tech: 'PostgreSQL + Cache', ttl: '随 HRIS 同步', bgClass: 'bg-green-500/10 border-green-500/20', iconClass: 'text-green-400' },
  ];

  const forbiddenMemory = [
    '健康信息、医疗证明',
    '家庭成员隐私详情',
    '薪资细节与薪酬谈判记录',
    '证件号码（身份证、护照等）',
    '敏感绩效信息与纪律处分记录',
    '银行卡号等金融信息',
  ];

  return (
    <section id="context" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent">数据流与 Memory 系统</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">Agent 如何将员工信息、企业政策、业务上下文有机融合，驱动智能决策</p>
        </div>

        {/* Context Fusion */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">上下文融合架构 (Context Fusion)</h3>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-blue-300 flex items-center"><i className="fas fa-sign-in-alt mr-2"></i>输入上下文</h4>
              {[
                { icon: 'fa-user', label: '员工 Profile', desc: '职级、部门、地点、假期余额' },
                { icon: 'fa-building', label: '组织上下文', desc: '团队结构、汇报关系、项目归属' },
                { icon: 'fa-comments', label: '对话历史', desc: '当前会话 + 近期交互记录' },
                { icon: 'fa-calendar', label: '业务日历', desc: '项目里程碑、团队排期' },
              ].map((item, i) => (
                <div key={i} className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 flex items-start space-x-3">
                  <i className={`fas ${item.icon} text-blue-400 mt-0.5`}></i>
                  <div>
                    <div className="text-sm font-medium text-white">{item.label}</div>
                    <div className="text-xs text-slate-400">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center">
              <div className="bg-gradient-to-br from-purple-500/20 to-cyan-500/20 border border-purple-500/30 rounded-2xl p-5 w-full text-center">
                <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-xl flex items-center justify-center">
                  <i className="fas fa-brain text-white text-xl"></i>
                </div>
                <h4 className="text-sm font-bold text-white mb-2">Context Fusion Engine</h4>
                <div className="space-y-1.5 text-left">
                  {['上下文注入 (Context Injection)', '相关性排序 (Relevance Ranking)', '冲突检测 (Conflict Detection)', 'Prompt 增强 (Augmentation)'].map((item, i) => (
                    <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                      <i className="fas fa-chevron-right text-purple-400 text-[10px]"></i>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-green-300 flex items-center"><i className="fas fa-sign-out-alt mr-2"></i>增强输出</h4>
              {[
                { icon: 'fa-check-double', label: '个性化回答', desc: '基于员工身份定制' },
                { icon: 'fa-tasks', label: '可执行方案', desc: '含具体步骤和预估时间' },
                { icon: 'fa-exclamation-triangle', label: '风险提示', desc: '政策/时间冲突预警' },
                { icon: 'fa-link', label: '关联推荐', desc: '后续操作建议' },
              ].map((item, i) => (
                <div key={i} className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 flex items-start space-x-3">
                  <i className={`fas ${item.icon} text-green-400 mt-0.5`}></i>
                  <div>
                    <div className="text-sm font-medium text-white">{item.label}</div>
                    <div className="text-xs text-slate-400">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Memory System */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">Memory 系统设计</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {memoryTypes.map((mem, i) => (
              <div key={i} className={`${mem.bgClass} border rounded-xl p-4`}>
                <div className="flex items-center space-x-2 mb-2">
                  <i className={`fas ${mem.icon} ${mem.iconClass}`}></i>
                  <h4 className="text-sm font-semibold text-white">{mem.title}</h4>
                </div>
                <p className="text-xs text-slate-500 font-mono mb-2">{mem.subtitle}</p>
                <p className="text-xs text-slate-400 mb-3">{mem.desc}</p>
                <div className="space-y-1">
                  <div className="text-[10px] text-slate-500"><span className="text-slate-400">技术:</span> {mem.tech}</div>
                  <div className="text-[10px] text-slate-500"><span className="text-slate-400">生命周期:</span> {mem.ttl}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Privacy Boundary */}
        <div className="bg-rose-500/5 border border-rose-500/30 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <i className="fas fa-ban text-rose-400 mr-3"></i>
            隐私边界：不可长期记忆的信息
          </h3>
          <p className="text-sm text-slate-400 mb-4">以下信息严禁写入长期记忆，仅在必要时短期使用并立即销毁：</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {forbiddenMemory.map((item, i) => (
              <div key={i} className="flex items-center space-x-2 bg-rose-500/10 border border-rose-500/20 rounded-lg p-3">
                <i className="fas fa-times-circle text-rose-400 text-sm"></i>
                <span className="text-sm text-slate-300">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
