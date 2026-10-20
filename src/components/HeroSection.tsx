export default function HeroSection() {
  return (
    <section id="overview" className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
      </div>
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }}></div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center space-x-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-6">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span className="text-sm text-blue-300">合并完整版 · v0.2</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">
              智能员工服务
            </span>
            <br />
            <span className="text-white">与人力运营 Agent</span>
          </h1>
          <p className="text-lg text-slate-300 max-w-3xl mx-auto mb-4 leading-relaxed">
            构建面向员工日常 HR 和企业内部服务场景的智能运营 Agent，使员工能够通过自然语言完成
            <span className="text-blue-300">休假、调动、差旅</span>、政策咨询、审批准备和 HR Service Request 等任务。
            与传统 HR Chatbot 不同，该 Agent 能够结合员工信息、企业政策和业务上下文，
            <span className="text-purple-300">自主规划并推动相关流程执行</span>。
          </p>
        </div>

        {/* 核心定位对比 */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-4 text-center">核心定位：传统 Chatbot vs Workforce Agent</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-600">
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">能力维度</th>
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">传统 HR Chatbot</th>
                  <th className="text-left py-2 px-3 text-blue-400 font-medium">Workforce Agent</th>
                </tr>
              </thead>
              <tbody className="text-slate-300">
                <tr className="border-b border-slate-700/50"><td className="py-2 px-3">交互方式</td><td className="py-2 px-3 text-slate-500">问答式</td><td className="py-2 px-3">任务驱动，多轮澄清</td></tr>
                <tr className="border-b border-slate-700/50"><td className="py-2 px-3">信息来源</td><td className="py-2 px-3 text-slate-500">静态 FAQ</td><td className="py-2 px-3">知识库+上下文+业务系统</td></tr>
                <tr className="border-b border-slate-700/50"><td className="py-2 px-3">执行动作</td><td className="py-2 px-3 text-slate-500">提供链接</td><td className="py-2 px-3">调用系统执行操作</td></tr>
                <tr className="border-b border-slate-700/50"><td className="py-2 px-3">流程能力</td><td className="py-2 px-3 text-slate-500">简单指引</td><td className="py-2 px-3">规划→拆解→校验→提交→追踪</td></tr>
                <tr className="border-b border-slate-700/50"><td className="py-2 px-3">个性化</td><td className="py-2 px-3 text-slate-500">较弱</td><td className="py-2 px-3">基于身份/岗位/地区定制</td></tr>
                <tr><td className="py-2 px-3">主动性</td><td className="py-2 px-3 text-slate-500">被动响应</td><td className="py-2 px-3">主动推送提醒</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 核心技术标签 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-4xl mx-auto">
          {[
            { icon: 'fa-brain', label: 'Agentic Workflow', desc: '自主规划执行' },
            { icon: 'fa-database', label: '上下文融合', desc: '企业知识+用户信息' },
            { icon: 'fa-cogs', label: 'Tool Calling', desc: '系统工具调用' },
            { icon: 'fa-user-shield', label: 'Human-in-Loop', desc: '审批闭环' },
          ].map((item, i) => (
            <div key={i} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 hover:border-blue-500/30 transition-all group text-center">
              <div className="w-10 h-10 mx-auto mb-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg flex items-center justify-center">
                <i className={`fas ${item.icon} text-blue-400`}></i>
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{item.label}</h3>
              <p className="text-xs text-slate-400">{item.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 flex justify-center">
          <a href="#scenarios" className="inline-flex items-center space-x-2 text-slate-400 hover:text-white transition-colors">
            <span>查看完整方案</span>
            <i className="fas fa-chevron-down animate-bounce"></i>
          </a>
        </div>
      </div>
    </section>
  );
}
