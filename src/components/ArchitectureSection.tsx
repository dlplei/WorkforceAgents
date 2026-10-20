export default function ArchitectureSection() {
  return (
    <section id="architecture" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              系统架构设计
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            基于 Agentic AI 的多层架构，融合 LLM 推理、企业知识、工具调用与流程自动化
          </p>
        </div>

        {/* Architecture Diagram */}
        <div className="relative bg-slate-800/30 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 sm:p-8 lg:p-12">
          {/* Layer Labels */}
          <div className="space-y-6">
            {/* Layer 1: User Interface */}
            <div className="relative">
              <div className="absolute -left-2 top-1/2 -translate-y-1/2 -translate-x-full hidden lg:block">
                <span className="text-xs text-slate-500 font-mono whitespace-nowrap">接入层</span>
              </div>
              <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-xl p-4 sm:p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <i className="fas fa-desktop text-blue-400"></i>
                  <h3 className="text-blue-300 font-semibold">用户接入层 (User Interface Layer)</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {['企业 IM 集成\n(钉钉/飞书/Teams)', 'Web Portal\n员工自助', '移动端\nApp/小程序', '语音交互\nIVR/AI Phone'].map((item, i) => (
                    <div key={i} className="bg-slate-800/80 rounded-lg p-3 text-center text-xs text-slate-300 border border-slate-600/50">
                      {item.split('\n').map((line, j) => (
                        <div key={j} className={j === 0 ? 'font-medium text-white' : 'text-slate-400 mt-0.5'}>{line}</div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <div className="flex flex-col items-center">
                <i className="fas fa-arrow-down text-slate-500"></i>
                <span className="text-xs text-slate-500 mt-1">NLU / Intent</span>
              </div>
            </div>

            {/* Layer 2: Agent Core */}
            <div className="relative">
              <div className="absolute -left-2 top-1/2 -translate-y-1/2 -translate-x-full hidden lg:block">
                <span className="text-xs text-slate-500 font-mono whitespace-nowrap">Agent层</span>
              </div>
              <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/30 rounded-xl p-4 sm:p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <i className="fas fa-brain text-purple-400"></i>
                  <h3 className="text-purple-300 font-semibold">Agent 核心层 (Agent Core Layer)</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-slate-800/80 rounded-lg p-4 border border-purple-500/20">
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">🧠 推理引擎</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• LLM 推理 (GPT-4/Claude)</li>
                      <li>• Chain-of-Thought 规划</li>
                      <li>• ReAct 模式执行</li>
                      <li>• 多步任务分解</li>
                    </ul>
                  </div>
                  <div className="bg-slate-800/80 rounded-lg p-4 border border-purple-500/20">
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">📋 任务编排器</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• 意图识别 & 槽位填充</li>
                      <li>• 任务图 (Task Graph)</li>
                      <li>• 条件分支 & 循环</li>
                      <li>• 并行/串行执行</li>
                    </ul>
                  </div>
                  <div className="bg-slate-800/80 rounded-lg p-4 border border-purple-500/20">
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">💾 Memory 系统</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• 短期记忆 (会话上下文)</li>
                      <li>• 长期记忆 (用户画像)</li>
                      <li>• 情景记忆 (历史交互)</li>
                      <li>• 向量检索 (RAG)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <div className="flex flex-col items-center">
                <i className="fas fa-arrows-alt-v text-slate-500"></i>
                <span className="text-xs text-slate-500 mt-1">Tool Calls / API</span>
              </div>
            </div>

            {/* Layer 3: Knowledge & Tools */}
            <div className="relative">
              <div className="absolute -left-2 top-1/2 -translate-y-1/2 -translate-x-full hidden lg:block">
                <span className="text-xs text-slate-500 font-mono whitespace-nowrap">能力层</span>
              </div>
              <div className="bg-gradient-to-r from-cyan-500/10 to-cyan-600/10 border border-cyan-500/30 rounded-xl p-4 sm:p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <i className="fas fa-tools text-cyan-400"></i>
                  <h3 className="text-cyan-300 font-semibold">知识与工具层 (Knowledge & Tool Layer)</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="bg-slate-800/80 rounded-lg p-4 border border-cyan-500/20">
                    <h4 className="text-sm font-semibold text-cyan-300 mb-2">📚 知识引擎</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• 企业政策知识库 (RAG)</li>
                      <li>• HR 流程文档 (向量化)</li>
                      <li>• 法规合规库</li>
                      <li>• FAQ & 最佳实践</li>
                    </ul>
                  </div>
                  <div className="bg-slate-800/80 rounded-lg p-4 border border-cyan-500/20">
                    <h4 className="text-sm font-semibold text-cyan-300 mb-2">🔧 工具集 (Tools)</h4>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• HRIS 系统接口 (Workday/SAP)</li>
                      <li>• 审批流引擎 (BPM)</li>
                      <li>• 日历 & 排班系统</li>
                      <li>• 财务/差旅系统</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <div className="flex flex-col items-center">
                <i className="fas fa-arrow-down text-slate-500"></i>
                <span className="text-xs text-slate-500 mt-1">API / Event</span>
              </div>
            </div>

            {/* Layer 4: Backend Systems */}
            <div className="relative">
              <div className="absolute -left-2 top-1/2 -translate-y-1/2 -translate-x-full hidden lg:block">
                <span className="text-xs text-slate-500 font-mono whitespace-nowrap">系统层</span>
              </div>
              <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 border border-green-500/30 rounded-xl p-4 sm:p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <i className="fas fa-server text-green-400"></i>
                  <h3 className="text-green-300 font-semibold">企业后端系统层 (Backend Systems)</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {['HRIS\n(Workday)', '审批系统\n(BPM)', '财务系统\n(ERP)', '差旅系统\n(TMC)', 'IM/OA\n(钉钉)'].map((item, i) => (
                    <div key={i} className="bg-slate-800/80 rounded-lg p-3 text-center text-xs text-slate-300 border border-green-500/20">
                      {item.split('\n').map((line, j) => (
                        <div key={j} className={j === 0 ? 'font-medium text-white' : 'text-slate-400 mt-0.5'}>{line}</div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Cross-cutting concerns */}
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <i className="fas fa-shield-alt text-amber-400"></i>
                <h4 className="text-sm font-semibold text-amber-300">安全与合规</h4>
              </div>
              <p className="text-xs text-slate-400">RBAC 权限控制、数据脱敏、审计日志、GDPR/个保法合规</p>
            </div>
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <i className="fas fa-chart-line text-rose-400"></i>
                <h4 className="text-sm font-semibold text-rose-300">监控与可观测</h4>
              </div>
              <p className="text-xs text-slate-400">Agent 行为追踪、Token 用量、延迟监控、异常告警</p>
            </div>
            <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <i className="fas fa-sync-alt text-indigo-400"></i>
                <h4 className="text-sm font-semibold text-indigo-300">持续优化</h4>
              </div>
              <p className="text-xs text-slate-400">反馈闭环、A/B 测试、Prompt 版本管理、效果评估</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
