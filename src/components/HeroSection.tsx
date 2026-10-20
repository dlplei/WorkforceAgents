export default function HeroSection() {
  return (
    <section id="overview" className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl"></div>
      </div>

      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }}></div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center space-x-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-8">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          <span className="text-sm text-blue-300">技术方案 v1.0</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6">
          <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">
            智能员工服务
          </span>
          <br />
          <span className="text-white">与人力运营 Agent</span>
        </h1>

        <p className="text-xl sm:text-2xl text-slate-300 mb-4 font-light">
          Workforce Operations Agent
        </p>

        <p className="text-lg text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
          构建面向员工日常 HR 和企业内部服务场景的智能运营 Agent，使员工能够通过自然语言完成
          <span className="text-blue-300">休假、调动、差旅</span>、员工政策咨询、审批准备和 HR Service Request 等任务。
          与传统 HR Chatbot 不同，该 Agent 能够结合员工信息、企业政策和业务上下文，
          <span className="text-purple-300">自主规划并推动相关流程执行</span>。
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto">
          {[
            { icon: 'fa-brain', label: 'Agentic Workflow', desc: '自主规划执行' },
            { icon: 'fa-database', label: '上下文融合', desc: '企业知识+用户信息' },
            { icon: 'fa-cogs', label: 'Tool Calling', desc: '系统工具调用' },
            { icon: 'fa-user-shield', label: 'Human-in-Loop', desc: '审批闭环' },
          ].map((item, i) => (
            <div key={i} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 hover:border-blue-500/30 transition-all group">
              <div className="w-10 h-10 mx-auto mb-3 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg flex items-center justify-center group-hover:from-blue-500/30 group-hover:to-purple-500/30 transition-all">
                <i className={`fas ${item.icon} text-blue-400`}></i>
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{item.label}</h3>
              <p className="text-xs text-slate-400">{item.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 flex justify-center">
          <a href="#architecture" className="inline-flex items-center space-x-2 text-slate-400 hover:text-white transition-colors">
            <span>查看完整架构</span>
            <i className="fas fa-chevron-down animate-bounce"></i>
          </a>
        </div>
      </div>
    </section>
  );
}
