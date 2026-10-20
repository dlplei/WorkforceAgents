export default function MetricsSection() {
  const priorities = [
    { num: 1, title: '企业政策 RAG 问答', desc: '覆盖员工手册、休假政策、差旅政策、福利政策' },
    { num: 2, title: '员工上下文服务', desc: '对接 HRIS，读取员工基本信息、组织关系、休假余额' },
    { num: 3, title: '休假申请 Agent', desc: '第一个端到端流程型场景，复杂度适中、价值明显' },
    { num: 4, title: 'HR Service Request Agent', desc: '支持创建、分类、查询 HR 工单' },
    { num: 5, title: '审批前检查能力', desc: '自动检查材料完整性、政策符合性和审批路径' },
    { num: 6, title: 'HITL 审批机制', desc: '对高风险事项引入人工确认和审批' },
  ];

  return (
    <section id="metrics" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">衡量指标与优先建设</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">多维度评估体系 + 优先建设能力建议 + 方案总结</p>
        </div>

        {/* 衡量指标 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-9 h-9 bg-blue-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-smile text-blue-400"></i>
              </div>
              <h3 className="font-semibold text-white">员工体验指标</h3>
            </div>
            <ul className="space-y-2 text-sm text-slate-300">
              {['首次响应时间', '任务完成时间', '员工满意度 (CSAT)', '自助解决率', '多轮对话完成率'].map((item, i) => (
                <li key={i} className="flex items-center space-x-2">
                  <i className="fas fa-chart-line text-blue-400 text-xs"></i>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-9 h-9 bg-green-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-tachometer-alt text-green-400"></i>
              </div>
              <h3 className="font-semibold text-white">运营效率指标</h3>
            </div>
            <ul className="space-y-2 text-sm text-slate-300">
              {['HR 工单减少比例', '人均服务成本降低', '自动化流程提交比例', '审批材料一次通过率', 'HR 专员处理时长降低'].map((item, i) => (
                <li key={i} className="flex items-center space-x-2">
                  <i className="fas fa-chart-line text-green-400 text-xs"></i>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-9 h-9 bg-amber-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-shield-alt text-amber-400"></i>
              </div>
              <h3 className="font-semibold text-white">质量与安全指标</h3>
            </div>
            <ul className="space-y-2 text-sm text-slate-300">
              {['政策回答准确率', '工具调用成功率', '越权访问拦截率', '人工介入率', '幻觉率 / 无依据回答率'].map((item, i) => (
                <li key={i} className="flex items-center space-x-2">
                  <i className="fas fa-chart-line text-amber-400 text-xs"></i>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 优先建设建议 */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-12">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center">
            <i className="fas fa-star text-yellow-400 mr-3"></i>
            优先建设能力建议
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {priorities.map((p) => (
              <div key={p.num} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 flex items-start space-x-3">
                <div className="w-8 h-8 bg-yellow-500/10 border border-yellow-500/30 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-yellow-400">{p.num}</span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white mb-1">{p.title}</h4>
                  <p className="text-xs text-slate-400">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 方案总结 */}
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-6 sm:p-8">
          <h3 className="text-xl font-bold text-white mb-4 text-center">方案总结</h3>
          <div className="max-w-3xl mx-auto">
            <p className="text-slate-300 text-center mb-6 leading-relaxed">
              <span className="text-blue-300 font-semibold">Workforce Operations Agent 的核心不是简单 HR 问答</span>，
              而是一个结合企业知识、员工上下文、流程自动化和权限治理的智能运营系统。
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
              {[
                '理解员工自然语言需求',
                '检索并引用企业政策',
                '结合个人上下文个性化判断',
                '拆解并推进流程',
                '调用企业系统执行操作',
                '关键节点请求人工确认',
              ].map((item, i) => (
                <div key={i} className="flex items-center space-x-2 bg-slate-800/50 rounded-lg p-3">
                  <i className="fas fa-check-circle text-green-400 text-sm"></i>
                  <span className="text-xs text-slate-300">{item}</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-slate-400 text-center">
              通过分阶段实施、持续迭代优化，最终实现员工服务体验的全面提升和 HR 运营效率的显著增长。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
