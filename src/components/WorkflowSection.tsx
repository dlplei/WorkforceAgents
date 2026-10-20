import { useState } from 'react';

export default function WorkflowSection() {
  const [showJson, setShowJson] = useState(false);

  const steps = [
    { num: 1, title: '意图理解', icon: 'fa-comments', color: 'blue', desc: 'NLU 解析 → 加载员工 Profile → 多轮对话澄清 → 确定任务类型与参数' },
    { num: 2, title: '策略规划', icon: 'fa-project-diagram', color: 'purple', desc: '生成 Task Graph → 确定工具调用顺序 → 识别前置条件 → 评估 Policy Grounding' },
    { num: 3, title: '工具执行', icon: 'fa-cogs', color: 'cyan', desc: '调用 HRIS 查询 → 检索政策知识库 → 调用计算引擎 → 结果校验与重试' },
    { num: 4, title: '结果整合', icon: 'fa-file-alt', color: 'green', desc: '多源信息融合 → 生成可读方案 → 标注关键决策点 → 提供选项对比' },
    { num: 5, title: '人工确认', icon: 'fa-user-check', color: 'amber', desc: '展示操作摘要 → 用户确认/修改/取消 → 敏感操作二次验证 → 审批触发' },
    { num: 6, title: '执行追踪', icon: 'fa-rocket', color: 'rose', desc: '提交审批/执行变更 → 状态推送 → 异常处理与升级 → 更新 Memory' },
  ];

  const colorMap: Record<string, { bg: string; border: string; text: string }> = {
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' },
    cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
    amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400' },
    rose: { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400' },
  };

  const jsonExample = `{
  "task_id": "leave-request-20260917-001",
  "employee_id": "E10293",
  "intent": "annual_leave_request",
  "status": "waiting_for_user_confirmation",
  "steps_completed": [
    "identity_verified",
    "leave_balance_checked",
    "policy_validated",
    "calendar_conflict_checked",
    "draft_generated"
  ],
  "pending_action": "user_confirm",
  "context": {
    "leave_type": "annual",
    "start_date": "2026-10-08",
    "end_date": "2026-10-10",
    "days": 3,
    "remaining_balance": 7,
    "approver": "王经理",
    "policy_ref": "《员工年假管理办法》第3.2条"
  }
}`;

  return (
    <section id="workflow" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">Agent 工作流</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">基于 ReAct 模式的 Agentic Workflow：感知 → 规划 → 执行 → 确认 → 追踪</p>
        </div>

        {/* 六步工作流 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          {steps.map((step) => {
            const c = colorMap[step.color];
            return (
              <div key={step.num} className={`${c.bg} ${c.border} border rounded-xl p-4`}>
                <div className="flex items-center space-x-3 mb-2">
                  <div className={`w-8 h-8 rounded-full ${c.bg} border ${c.border} flex items-center justify-center`}>
                    <span className={`text-sm font-bold ${c.text}`}>{step.num}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <i className={`fas ${step.icon} ${c.text}`}></i>
                    <h3 className="font-semibold text-white text-sm">{step.title}</h3>
                  </div>
                </div>
                <p className="text-xs text-slate-400">{step.desc}</p>
              </div>
            );
          })}
        </div>

        {/* 示例：年假申请 */}
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <i className="fas fa-calendar-check text-blue-400 mr-3"></i>
            示例：员工申请年假
          </h3>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-4">
            <p className="text-sm text-slate-300">
              <span className="text-slate-500">用户输入：</span>
              "我想 10 月 8 日到 10 月 10 日请年假，帮我申请。"
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Agent 执行步骤 */}
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Agent 执行步骤</h4>
              <div className="bg-slate-900/50 rounded-lg p-4 text-xs text-slate-400 font-mono space-y-1">
                <p>1. 识别意图：annual_leave_request</p>
                <p>2. 获取员工身份：employee_id</p>
                <p>3. 查询员工信息：地区、合同、入职时间</p>
                <p>4. 查询假期余额</p>
                <p>5. 检索年假政策</p>
                <p>6. 校验日期和余额</p>
                <p>7. 检查日历冲突</p>
                <p>8. 生成申请草稿</p>
                <p>9. 展示给员工确认 (HITL)</p>
                <p>10. 确认后调用 Leave API</p>
                <p>11. 创建审批流</p>
                <p>12. 返回申请编号</p>
              </div>
            </div>

            {/* Agent 回复 */}
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Agent 回复示例</h4>
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4 text-xs text-slate-300 leading-relaxed">
                <p className="mb-2">我已检查你的年假余额和公司年假政策。你当前剩余年假为 <span className="text-blue-300 font-semibold">7 天</span>，计划申请 2026-10-08 至 2026-10-10，共 3 个工作日，符合《员工年假管理办法》的申请条件。</p>
                <p className="mb-2">申请摘要：</p>
                <ul className="space-y-1 ml-3">
                  <li>• 假期类型：年假</li>
                  <li>• 日期：2026-10-08 至 2026-10-10</li>
                  <li>• 天数：3 天</li>
                  <li>• 审批人：直属经理王经理</li>
                </ul>
                <p className="mt-2 text-blue-300">请确认是否提交该申请？</p>
              </div>
            </div>
          </div>

          {/* JSON 状态模型 */}
          <div className="mt-4">
            <button
              onClick={() => setShowJson(!showJson)}
              className="flex items-center space-x-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <i className={`fas fa-chevron-${showJson ? 'down' : 'right'}`}></i>
              <span>{showJson ? '收起' : '展开'}任务状态模型 (Task State JSON)</span>
            </button>
            {showJson && (
              <pre className="mt-3 bg-slate-900/80 rounded-lg p-4 text-xs text-green-300 font-mono overflow-x-auto">
                {jsonExample}
              </pre>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
