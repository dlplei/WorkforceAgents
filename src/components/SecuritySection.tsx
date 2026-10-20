export default function SecuritySection() {
  return (
    <section id="security" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-rose-400 to-amber-400 bg-clip-text text-transparent">
              安全与权限设计
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            多层安全防护体系，确保 Agent 在明确的权限边界内运行
          </p>
        </div>

        {/* Permission Boundary Model */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 sm:p-8 mb-8">
          <h3 className="text-lg font-semibold text-white mb-6 text-center">权限边界模型 (Permission Boundary)</h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Autonomous Zone */}
            <div className="bg-green-500/5 border-2 border-green-500/30 rounded-xl p-5 relative">
              <div className="absolute -top-3 left-4 bg-green-500/20 border border-green-500/30 px-3 py-1 rounded-full">
                <span className="text-xs font-semibold text-green-300">🟢 自主执行区</span>
              </div>
              <div className="mt-3 space-y-2">
                <p className="text-xs text-slate-400 mb-3">Agent 可自主完成，无需人工确认</p>
                {[
                  '查询假期余额',
                  '检索政策信息',
                  '查询审批状态',
                  '生成方案草稿',
                  '回答 FAQ',
                ].map((item, i) => (
                  <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                    <i className="fas fa-check text-green-400 text-[10px]"></i>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Confirmation Zone */}
            <div className="bg-amber-500/5 border-2 border-amber-500/30 rounded-xl p-5 relative">
              <div className="absolute -top-3 left-4 bg-amber-500/20 border border-amber-500/30 px-3 py-1 rounded-full">
                <span className="text-xs font-semibold text-amber-300">🟡 确认执行区</span>
              </div>
              <div className="mt-3 space-y-2">
                <p className="text-xs text-slate-400 mb-3">需用户确认后执行</p>
                {[
                  '提交请假申请',
                  '提交差旅申请',
                  '修改个人信息',
                  '开具证明文件',
                  '触发审批流程',
                ].map((item, i) => (
                  <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                    <i className="fas fa-hand-paper text-amber-400 text-[10px]"></i>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Restricted Zone */}
            <div className="bg-rose-500/5 border-2 border-rose-500/30 rounded-xl p-5 relative">
              <div className="absolute -top-3 left-4 bg-rose-500/20 border border-rose-500/30 px-3 py-1 rounded-full">
                <span className="text-xs font-semibold text-rose-300">🔴 受限执行区</span>
              </div>
              <div className="mt-3 space-y-2">
                <p className="text-xs text-slate-400 mb-3">需多级审批或人工介入</p>
                {[
                  '薪酬调整操作',
                  '跨级调动审批',
                  '批量数据修改',
                  '敏感信息导出',
                  '系统配置变更',
                ].map((item, i) => (
                  <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                    <i className="fas fa-lock text-rose-400 text-[10px]"></i>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Security Measures */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* RBAC */}
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-users-cog text-blue-400"></i>
              </div>
              <h4 className="font-semibold text-white">RBAC 权限控制</h4>
            </div>
            <ul className="space-y-2 text-sm text-slate-400">
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-blue-400 mt-1 text-xs"></i>
                <span>基于角色的 Agent 能力授权（员工/经理/HRBP/HR Admin）</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-blue-400 mt-1 text-xs"></i>
                <span>Tool 级别的细粒度权限控制</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-blue-400 mt-1 text-xs"></i>
                <span>数据访问范围与员工层级绑定</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-blue-400 mt-1 text-xs"></i>
                <span>动态权限评估（考虑时间、地点等上下文）</span>
              </li>
            </ul>
          </div>

          {/* Data Protection */}
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-user-shield text-purple-400"></i>
              </div>
              <h4 className="font-semibold text-white">数据保护</h4>
            </div>
            <ul className="space-y-2 text-sm text-slate-400">
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-purple-400 mt-1 text-xs"></i>
                <span>PII 自动识别与脱敏（身份证号、银行卡号等）</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-purple-400 mt-1 text-xs"></i>
                <span>LLM 输入/输出过滤（防止 Prompt Injection）</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-purple-400 mt-1 text-xs"></i>
                <span>传输加密 (TLS 1.3) + 存储加密 (AES-256)</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-purple-400 mt-1 text-xs"></i>
                <span>数据最小化原则，按需加载上下文</span>
              </li>
            </ul>
          </div>

          {/* Audit */}
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-clipboard-list text-green-400"></i>
              </div>
              <h4 className="font-semibold text-white">审计追踪</h4>
            </div>
            <ul className="space-y-2 text-sm text-slate-400">
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-green-400 mt-1 text-xs"></i>
                <span>全链路操作日志（用户输入 → Agent 推理 → 工具调用 → 结果）</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-green-400 mt-1 text-xs"></i>
                <span>不可篡改的审计日志存储</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-green-400 mt-1 text-xs"></i>
                <span>异常行为检测与告警</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-green-400 mt-1 text-xs"></i>
                <span>支持合规审计导出</span>
              </li>
            </ul>
          </div>

          {/* Compliance */}
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-amber-500/10 rounded-lg flex items-center justify-center">
                <i className="fas fa-balance-scale text-amber-400"></i>
              </div>
              <h4 className="font-semibold text-white">合规保障</h4>
            </div>
            <ul className="space-y-2 text-sm text-slate-400">
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-amber-400 mt-1 text-xs"></i>
                <span>个人信息保护法 (PIPL) 合规</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-amber-400 mt-1 text-xs"></i>
                <span>GDPR 数据处理协议 (DPA)</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-amber-400 mt-1 text-xs"></i>
                <span>AI 伦理准则：透明性、可解释性、公平性</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="fas fa-angle-right text-amber-400 mt-1 text-xs"></i>
                <span>定期安全评估与渗透测试</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Human-in-the-Loop Detail */}
        <div className="mt-8 bg-gradient-to-r from-amber-500/5 to-rose-500/5 border border-amber-500/20 rounded-2xl p-6 sm:p-8">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <i className="fas fa-user-check text-amber-400 mr-3"></i>
            Human-in-the-Loop 机制详解
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { step: '1', title: '操作预览', desc: 'Agent 展示即将执行的操作摘要，包含影响范围', icon: 'fa-eye' },
              { step: '2', title: '用户确认', desc: '用户可选择确认、修改参数或取消操作', icon: 'fa-thumbs-up' },
              { step: '3', title: '二次验证', desc: '高敏感操作需额外身份验证（如 OTP）', icon: 'fa-fingerprint' },
              { step: '4', title: '执行反馈', desc: '执行结果即时反馈，失败时提供回退方案', icon: 'fa-redo' },
            ].map((item, i) => (
              <div key={i} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-7 h-7 bg-amber-500/20 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-amber-300">{item.step}</span>
                  </div>
                  <i className={`fas ${item.icon} text-amber-400 text-sm`}></i>
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">{item.title}</h4>
                <p className="text-xs text-slate-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
