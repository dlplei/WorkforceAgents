export default function DataFlow() {
  return (
    <section id="dataflow" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent">
              数据流与上下文融合
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Agent 如何将员工信息、企业政策、业务上下文有机融合，驱动智能决策
          </p>
        </div>

        {/* Context Fusion Diagram */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8 mb-12">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">上下文融合架构 (Context Fusion)</h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Contexts */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-blue-300 mb-3 flex items-center">
                <i className="fas fa-sign-in-alt mr-2"></i>输入上下文
              </h4>
              {[
                { icon: 'fa-user', label: '员工 Profile', desc: '职级、部门、地点、入职日期、假期余额', color: 'blue' },
                { icon: 'fa-building', label: '组织上下文', desc: '团队结构、汇报关系、项目归属', color: 'blue' },
                { icon: 'fa-comments', label: '对话历史', desc: '当前会话 + 近期交互记录', color: 'blue' },
                { icon: 'fa-calendar', label: '业务日历', desc: '项目里程碑、团队排期、公司假期', color: 'blue' },
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

            {/* Processing */}
            <div className="flex flex-col items-center justify-center">
              <div className="bg-gradient-to-br from-purple-500/20 to-cyan-500/20 border border-purple-500/30 rounded-2xl p-6 w-full text-center">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-xl flex items-center justify-center">
                  <i className="fas fa-brain text-white text-2xl"></i>
                </div>
                <h4 className="text-sm font-bold text-white mb-2">Context Fusion Engine</h4>
                <p className="text-xs text-slate-400 mb-4">多源上下文融合与增强</p>
                <div className="space-y-2 text-left">
                  {[
                    '上下文注入 (Context Injection)',
                    '相关性排序 (Relevance Ranking)',
                    '冲突检测 (Conflict Detection)',
                    'Prompt 增强 (Prompt Augmentation)',
                  ].map((item, i) => (
                    <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                      <i className="fas fa-chevron-right text-purple-400 text-[10px]"></i>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Output */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-green-300 mb-3 flex items-center">
                <i className="fas fa-sign-out-alt mr-2"></i>增强输出
              </h4>
              {[
                { icon: 'fa-check-double', label: '个性化回答', desc: '基于员工身份定制的回答与建议', color: 'green' },
                { icon: 'fa-tasks', label: '可执行方案', desc: '包含具体步骤和预估时间的行动方案', color: 'green' },
                { icon: 'fa-exclamation-triangle', label: '风险提示', desc: '政策冲突、时间冲突等预警', color: 'green' },
                { icon: 'fa-link', label: '关联推荐', desc: '可能需要的后续操作建议', color: 'green' },
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

        {/* Data Flow Sequence */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">请求处理时序 (Request Sequence)</h3>
          
          <div className="overflow-x-auto">
            <div className="min-w-[600px]">
              {/* Headers */}
              <div className="grid grid-cols-5 gap-2 mb-4">
                {['用户', 'Agent Core', 'Memory', 'Knowledge', 'Tools'].map((h, i) => (
                  <div key={i} className="text-center">
                    <div className="bg-slate-700 rounded-lg px-3 py-2 text-xs font-semibold text-white">
                      {h}
                    </div>
                  </div>
                ))}
              </div>

              {/* Flow lines */}
              <div className="space-y-3">
                {[
                  { from: 0, to: 1, label: '1. 自然语言输入', type: 'request' },
                  { from: 1, to: 2, label: '2. 加载用户上下文', type: 'internal' },
                  { from: 1, to: 3, label: '3. RAG 检索相关政策', type: 'internal' },
                  { from: 1, to: 1, label: '4. 推理 & 规划', type: 'process' },
                  { from: 1, to: 4, label: '5. 调用业务工具', type: 'tool' },
                  { from: 4, to: 1, label: '6. 返回工具结果', type: 'response' },
                  { from: 1, to: 2, label: '7. 更新 Memory', type: 'internal' },
                  { from: 1, to: 0, label: '8. 返回结构化回答', type: 'response' },
                ].map((flow, i) => (
                  <div key={i} className="relative flex items-center h-8">
                    <div className="absolute inset-0 grid grid-cols-5 gap-2">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <div key={j} className="border-t border-dashed border-slate-700 h-full flex items-center justify-center">
                          {j >= Math.min(flow.from, flow.to) && j <= Math.max(flow.from, flow.to) && (
                            <div className={`w-full h-0.5 ${
                              flow.type === 'request' ? 'bg-blue-500' :
                              flow.type === 'response' ? 'bg-green-500' :
                              flow.type === 'tool' ? 'bg-cyan-500' :
                              flow.type === 'process' ? 'bg-purple-500' :
                              'bg-slate-500'
                            }`}></div>
                          )}
                        </div>
                      ))}
                    </div>
                    <div className="relative z-10 w-full text-center">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                        flow.type === 'request' ? 'bg-blue-500/20 text-blue-300' :
                        flow.type === 'response' ? 'bg-green-500/20 text-green-300' :
                        flow.type === 'tool' ? 'bg-cyan-500/20 text-cyan-300' :
                        flow.type === 'process' ? 'bg-purple-500/20 text-purple-300' :
                        'bg-slate-500/20 text-slate-300'
                      }`}>
                        {flow.label}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Memory Architecture */}
        <div className="mt-8 bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">Memory 系统设计</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                title: '工作记忆',
                subtitle: 'Working Memory',
                icon: 'fa-microchip',
                desc: '当前会话上下文，短期保持',
                tech: 'Redis + In-Context Window',
                ttl: '会话期间',
                bgClass: 'bg-blue-500/10 border-blue-500/20',
                iconClass: 'text-blue-400',
              },
              {
                title: '情景记忆',
                subtitle: 'Episodic Memory',
                icon: 'fa-history',
                desc: '历史交互记录，支持检索',
                tech: 'Vector DB + PostgreSQL',
                ttl: '永久 (可清理)',
                bgClass: 'bg-purple-500/10 border-purple-500/20',
                iconClass: 'text-purple-400',
              },
              {
                title: '语义记忆',
                subtitle: 'Semantic Memory',
                icon: 'fa-book-open',
                desc: '企业政策、流程知识',
                tech: 'Vector DB + Elasticsearch',
                ttl: '随政策更新',
                bgClass: 'bg-cyan-500/10 border-cyan-500/20',
                iconClass: 'text-cyan-400',
              },
              {
                title: '用户画像',
                subtitle: 'User Profile Memory',
                icon: 'fa-id-card',
                desc: '员工偏好、行为模式',
                tech: 'PostgreSQL + Cache',
                ttl: '随 HRIS 同步',
                bgClass: 'bg-green-500/10 border-green-500/20',
                iconClass: 'text-green-400',
              },
            ].map((mem, i) => (
              <div key={i} className={`${mem.bgClass} border rounded-xl p-4`}>
                <div className="flex items-center space-x-2 mb-2">
                  <i className={`fas ${mem.icon} ${mem.iconClass}`}></i>
                  <h4 className="text-sm font-semibold text-white">{mem.title}</h4>
                </div>
                <p className="text-xs text-slate-500 font-mono mb-2">{mem.subtitle}</p>
                <p className="text-xs text-slate-400 mb-3">{mem.desc}</p>
                <div className="space-y-1">
                  <div className="text-[10px] text-slate-500">
                    <span className="text-slate-400">技术:</span> {mem.tech}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    <span className="text-slate-400">生命周期:</span> {mem.ttl}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
