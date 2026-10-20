export default function SecuritySection() {
  return (
    <section id="security" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-rose-400 to-amber-400 bg-clip-text text-transparent">安全与权限设计</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">多层安全防护体系，确保 Agent 在明确的权限边界内运行</p>
        </div>

        {/* Permission Boundary */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-5 text-center">权限边界模型 (Permission Boundary)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-green-500/5 border-2 border-green-500/30 rounded-xl p-4">
              <div className="text-xs font-semibold text-green-300 mb-2">🟢 自主执行区</div>
              <p className="text-[11px] text-slate-400 mb-2">Agent 可自主完成，无需人工确认</p>
              {['查询假期余额', '检索政策信息', '查询审批状态', '生成方案草稿', '回答 FAQ'].map((item, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs text-slate-300 py-0.5">
                  <i className="fas fa-check text-green-400 text-[10px]"></i><span>{item}</span>
                </div>
              ))}
            </div>
            <div className="bg-amber-500/5 border-2 border-amber-500/30 rounded-xl p-4">
              <div className="text-xs font-semibold text-amber-300 mb-2">🟡 确认执行区</div>
              <p className="text-[11px] text-slate-400 mb-2">需用户确认后执行</p>
              {['提交请假申请', '提交差旅申请', '修改个人信息', '开具证明文件', '触发审批流程'].map((item, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs text-slate-300 py-0.5">
                  <i className="fas fa-hand-paper text-amber-400 text-[10px]"></i><span>{item}</span>
                </div>
              ))}
            </div>
            <div className="bg-rose-500/5 border-2 border-rose-500/30 rounded-xl p-4">
              <div className="text-xs font-semibold text-rose-300 mb-2">🔴 受限执行区</div>
              <p className="text-[11px] text-slate-400 mb-2">需多级审批或人工介入</p>
              {['薪酬调整操作', '跨级调动审批', '批量数据修改', '敏感信息导出', '系统配置变更'].map((item, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs text-slate-300 py-0.5">
                  <i className="fas fa-lock text-rose-400 text-[10px]"></i><span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* HITL Table */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <i className="fas fa-user-check text-amber-400 mr-3"></i>
            Human-in-the-Loop 审批场景
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-2 px-3 text-slate-300 font-semibold">场景</th>
                  <th className="text-left py-2 px-3 text-slate-300 font-semibold">处理方式</th>
                </tr>
              </thead>
              <tbody className="text-slate-400">
                {[
                  ['政策不明确', '转 HR 专员确认'],
                  ['信息不完整', '请求员工补充'],
                  ['超出政策标准', '进入例外审批'],
                  ['涉及薪酬或合同', 'HRBP 或经理审核'],
                  ['涉及敏感个人信息', '加强身份和权限校验'],
                  ['高影响组织变更', '多级审批'],
                  ['Agent 置信度低', '人工复核后再执行'],
                ].map((row, i) => (
                  <tr key={i} className="border-b border-slate-700/50">
                    <td className="py-2 px-3 text-slate-300">{row[0]}</td>
                    <td className="py-2 px-3">{row[1]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Guardrails */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          {[
            { title: '输入侧防护', icon: 'fa-shield-alt', color: 'blue', items: ['Prompt Injection 检测', '越权查询检测', '敏感信息识别', '上传文档安全扫描'] },
            { title: '推理侧防护', icon: 'fa-brain', color: 'purple', items: ['政策回答基于检索结果', '工具调用前参数校验', '高风险任务人工确认', '权限判断前置'] },
            { title: '输出侧防护', icon: 'fa-file-export', color: 'green', items: ['避免暴露无权限数据', '敏感字段脱敏', '标注政策依据', '明确不确定边界'] },
          ].map((g, i) => (
            <div key={i} className={`bg-${g.color}-500/10 border border-${g.color}-500/20 rounded-xl p-5`}>
              <div className="flex items-center space-x-2 mb-3">
                <i className={`fas ${g.icon} text-${g.color}-400`}></i>
                <h4 className="text-sm font-semibold text-white">{g.title}</h4>
              </div>
              <ul className="space-y-1.5">
                {g.items.map((item, j) => (
                  <li key={j} className="text-xs text-slate-300 flex items-center space-x-2">
                    <i className={`fas fa-check text-${g.color}-400 text-[10px]`}></i>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* RBAC + ABAC */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
              <i className="fas fa-users-cog text-blue-400 mr-2"></i>RBAC：基于角色
            </h4>
            <div className="flex flex-wrap gap-2">
              {['普通员工', '直属经理', 'HR 专员', 'HRBP', '财务审批人', '系统管理员'].map((role, i) => (
                <span key={i} className="text-xs bg-blue-500/10 text-blue-300 px-2 py-1 rounded">{role}</span>
              ))}
            </div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
              <i className="fas fa-sliders-h text-purple-400 mr-2"></i>ABAC：基于属性
            </h4>
            <div className="flex flex-wrap gap-2">
              {['国家/地区', '部门', '成本中心', '员工类型', '汇报关系', '数据敏感级别'].map((attr, i) => (
                <span key={i} className="text-xs bg-purple-500/10 text-purple-300 px-2 py-1 rounded">{attr}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
