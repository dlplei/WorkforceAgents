export default function ArchitectureSection() {
  return (
    <section id="architecture" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">系统架构设计</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">基于 Agentic AI 的多层架构，融合 LLM 推理、企业知识、工具调用与流程自动化</p>
        </div>

        <div className="relative bg-slate-800/30 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 sm:p-8">
          <div className="space-y-4">
            {/* Layer 1: User Interface */}
            <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-xl p-4 sm:p-5">
              <div className="flex items-center space-x-2 mb-3">
                <i className="fas fa-desktop text-blue-400"></i>
                <h3 className="text-blue-300 font-semibold text-sm sm:text-base">用户接入层 (User Interface Layer)</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {['Teams / Slack', '企业微信 / 飞书', 'Web Portal', 'Mobile App / IVR'].map((item, i) => (
                  <div key={i} className="bg-slate-800/80 rounded-lg p-2.5 text-center text-xs text-slate-300 border border-slate-600/50">{item}</div>
                ))}
              </div>
            </div>

            <div className="flex justify-center"><i className="fas fa-arrow-down text-slate-500"></i></div>

            {/* Layer 2: API Gateway */}
            <div className="bg-gradient-to-r from-indigo-500/10 to-indigo-600/10 border border-indigo-500/30 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <i className="fas fa-shield-alt text-indigo-400"></i>
                <h3 className="text-indigo-300 font-semibold text-sm">API Gateway</h3>
              </div>
              <p className="text-xs text-slate-400">认证 / 限流 / 日志 / 请求路由 / 安全过滤</p>
            </div>

            <div className="flex justify-center"><i className="fas fa-arrow-down text-slate-500"></i></div>

            {/* Layer 3: Agent Core */}
            <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/30 rounded-xl p-4 sm:p-5">
              <div className="flex items-center space-x-2 mb-3">
                <i className="fas fa-brain text-purple-400"></i>
                <h3 className="text-purple-300 font-semibold text-sm sm:text-base">Agent 核心层 (Agent Core Layer)</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-slate-800/80 rounded-lg p-3 border border-purple-500/20">
                  <h4 className="text-xs font-semibold text-purple-300 mb-1.5">🧠 推理引擎</h4>
                  <ul className="text-[11px] text-slate-400 space-y-0.5">
                    <li>• LLM 推理 (GPT-4/Claude)</li>
                    <li>• Chain-of-Thought 规划</li>
                    <li>• ReAct 模式执行</li>
                  </ul>
                </div>
                <div className="bg-slate-800/80 rounded-lg p-3 border border-purple-500/20">
                  <h4 className="text-xs font-semibold text-purple-300 mb-1.5">📋 任务编排器</h4>
                  <ul className="text-[11px] text-slate-400 space-y-0.5">
                    <li>• 意图识别 & 槽位填充</li>
                    <li>• Task Graph 任务图</li>
                    <li>• Plan-and-Execute</li>
                  </ul>
                </div>
                <div className="bg-slate-800/80 rounded-lg p-3 border border-purple-500/20">
                  <h4 className="text-xs font-semibold text-purple-300 mb-1.5">💾 Memory 系统</h4>
                  <ul className="text-[11px] text-slate-400 space-y-0.5">
                    <li>• 短期记忆 (会话上下文)</li>
                    <li>• 长期记忆 (用户画像)</li>
                    <li>• 情景记忆 (历史交互)</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-center"><i className="fas fa-arrows-alt-v text-slate-500"></i></div>

            {/* Layer 4: Knowledge & Tools */}
            <div className="bg-gradient-to-r from-cyan-500/10 to-cyan-600/10 border border-cyan-500/30 rounded-xl p-4 sm:p-5">
              <div className="flex items-center space-x-2 mb-3">
                <i className="fas fa-tools text-cyan-400"></i>
                <h3 className="text-cyan-300 font-semibold text-sm sm:text-base">知识与工具层 (Knowledge & Tool Layer)</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-slate-800/80 rounded-lg p-3 border border-cyan-500/20">
                  <h4 className="text-xs font-semibold text-cyan-300 mb-1.5">📚 知识检索</h4>
                  <p className="text-[11px] text-slate-400">RAG / Policy Grounding / ACL 过滤 / 向量检索</p>
                </div>
                <div className="bg-slate-800/80 rounded-lg p-3 border border-cyan-500/20">
                  <h4 className="text-xs font-semibold text-cyan-300 mb-1.5">👤 用户上下文</h4>
                  <p className="text-[11px] text-slate-400">Employee Profile / Org Chart / 权限 / 流程状态</p>
                </div>
                <div className="bg-slate-800/80 rounded-lg p-3 border border-cyan-500/20">
                  <h4 className="text-xs font-semibold text-cyan-300 mb-1.5">🔧 工具调用</h4>
                  <p className="text-[11px] text-slate-400">HRIS / BPM / ITSM / 差旅 / 财务 / 通知</p>
                </div>
              </div>
            </div>

            <div className="flex justify-center"><i className="fas fa-arrow-down text-slate-500"></i></div>

            {/* Layer 5: Backend Systems */}
            <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 border border-green-500/30 rounded-xl p-4 sm:p-5">
              <div className="flex items-center space-x-2 mb-3">
                <i className="fas fa-server text-green-400"></i>
                <h3 className="text-green-300 font-semibold text-sm sm:text-base">企业后端系统层 (Backend Systems)</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {['Workday', 'SAP SF', 'Oracle HCM', 'ServiceNow', 'Concur'].map((item, i) => (
                  <div key={i} className="bg-slate-800/80 rounded-lg p-2.5 text-center text-xs text-slate-300 border border-green-500/20">{item}</div>
                ))}
              </div>
            </div>

            {/* Cross-cutting */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <i className="fas fa-shield-alt text-amber-400 text-sm"></i>
                  <h4 className="text-xs font-semibold text-amber-300">安全与合规</h4>
                </div>
                <p className="text-[11px] text-slate-400">RBAC+ABAC / 数据脱敏 / 审计 / GDPR/PIPL</p>
              </div>
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <i className="fas fa-chart-line text-rose-400 text-sm"></i>
                  <h4 className="text-xs font-semibold text-rose-300">监控与可观测</h4>
                </div>
                <p className="text-[11px] text-slate-400">Agent 行为追踪 / Token 用量 / 延迟监控</p>
              </div>
              <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <i className="fas fa-sync-alt text-indigo-400 text-sm"></i>
                  <h4 className="text-xs font-semibold text-indigo-300">持续优化</h4>
                </div>
                <p className="text-[11px] text-slate-400">反馈闭环 / A/B 测试 / Prompt 版本管理</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
