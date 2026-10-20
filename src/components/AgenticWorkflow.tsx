export default function AgenticWorkflow() {
  const steps = [
    {
      num: 1,
      title: '意图理解',
      subtitle: 'Intent Understanding',
      icon: 'fa-comments',
      color: 'blue',
      description: 'Agent 接收用户自然语言输入，结合员工身份信息进行意图识别',
      details: [
        'NLU 解析用户输入',
        '加载员工 Profile 上下文',
        '多轮对话澄清歧义',
        '确定任务类型与参数',
      ],
      example: '输入: "我想从北京调到上海办公室"\n→ 意图: 员工调动\n→ 参数: {from: "北京", to: "上海"}\n→ 上下文: 当前部门=技术部, 职级=P6',
    },
    {
      num: 2,
      title: '策略规划',
      subtitle: 'Planning & Reasoning',
      icon: 'fa-project-diagram',
      color: 'purple',
      description: 'Agent 基于任务类型，规划执行步骤和所需工具调用',
      details: [
        '生成 Task Graph (任务图)',
        '确定工具调用顺序',
        '识别前置条件与依赖',
        '评估 Policy Grounding',
      ],
      example: 'Task Graph:\n1. 查询目标城市 HC\n2. 检查调动政策条件\n3. 计算薪酬变动\n4. 生成调动方案\n5. 提交审批',
    },
    {
      num: 3,
      title: '工具执行',
      subtitle: 'Tool Execution',
      icon: 'fa-cogs',
      color: 'cyan',
      description: 'Agent 按计划调用企业系统工具，获取数据或触发操作',
      details: [
        '调用 HRIS 查询接口',
        '检索政策知识库',
        '调用计算引擎',
        '结果校验与重试',
      ],
      example: 'Tool Calls:\n→ query_headcount(city="上海")\n→ check_transfer_policy(level="P6")\n→ calculate_salary_change(...)\n→ search_knowledge_base("跨城调动")',
    },
    {
      num: 4,
      title: '结果整合',
      subtitle: 'Synthesis & Response',
      icon: 'fa-file-alt',
      color: 'green',
      description: 'Agent 整合工具返回结果，生成结构化的方案或回答',
      details: [
        '多源信息融合',
        '生成可读方案报告',
        '标注关键决策点',
        '提供选项对比',
      ],
      example: '输出:\n"上海技术部目前有 2 个 HC，符合您的调动条件。\n薪酬调整: 基础+15%, 住房补贴 ¥5000/月\n预计生效: 审批通过后次月1日\n[查看详情] [提交申请]"',
    },
    {
      num: 5,
      title: '人工确认',
      subtitle: 'Human-in-the-Loop',
      icon: 'fa-user-check',
      color: 'amber',
      description: '关键操作需人工确认，确保 Agent 在权限边界内执行',
      details: [
        '展示操作摘要',
        '用户确认/修改/取消',
        '敏感操作二次验证',
        '审批流程触发',
      ],
      example: 'Agent: "即将为您提交调动申请:\n- 调动类型: 跨城市调动\n- 目标: 上海技术部\n- 预计薪酬变动: +15%\n\n确认提交? [确认] [修改] [取消]"',
    },
    {
      num: 6,
      title: '执行与追踪',
      subtitle: 'Execute & Monitor',
      icon: 'fa-rocket',
      color: 'rose',
      description: '确认后 Agent 执行操作并持续追踪状态，主动推送进展',
      details: [
        '提交审批/执行变更',
        '状态轮询与推送',
        '异常处理与升级',
        '完成后更新 Memory',
      ],
      example: '执行:\n→ 提交调动审批工单 #HR-2026-0892\n→ 通知审批人(直属Leader + HRBP)\n→ 设置状态追踪\n→ 预计 3 个工作日内完成',
    },
  ];

  const colorClasses: Record<string, { bg: string; border: string; text: string; dot: string }> = {
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-500' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-500' },
    cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400', dot: 'bg-cyan-500' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-500' },
    amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-500' },
    rose: { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400', dot: 'bg-rose-500' },
  };

  return (
    <section id="workflow" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
              Agent 工作流程
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            基于 ReAct 模式的 Agentic Workflow：感知 → 规划 → 执行 → 确认 → 追踪
          </p>
        </div>

        {/* Workflow Steps */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-6 sm:left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 via-cyan-500 via-green-500 via-amber-500 to-rose-500 hidden sm:block"></div>

          <div className="space-y-6">
            {steps.map((step) => {
              const colors = colorClasses[step.color];
              return (
                <div key={step.num} className="relative flex items-start space-x-4 sm:space-x-6">
                  {/* Step number circle */}
                  <div className={`relative z-10 flex-shrink-0 w-12 h-12 sm:w-16 sm:h-16 rounded-full ${colors.bg} border-2 ${colors.border} flex items-center justify-center`}>
                    <span className={`text-lg sm:text-xl font-bold ${colors.text}`}>{step.num}</span>
                  </div>

                  {/* Content card */}
                  <div className={`flex-1 ${colors.bg} ${colors.border} border rounded-xl p-4 sm:p-6`}>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-bold text-white flex items-center">
                          <i className={`fas ${step.icon} mr-2 ${colors.text}`}></i>
                          {step.title}
                        </h3>
                        <p className="text-xs text-slate-500 font-mono">{step.subtitle}</p>
                      </div>
                    </div>
                    <p className="text-sm text-slate-300 mb-3">{step.description}</p>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">关键动作</h4>
                        <ul className="space-y-1">
                          {step.details.map((detail, i) => (
                            <li key={i} className="text-xs text-slate-400 flex items-center space-x-2">
                              <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`}></span>
                              <span>{detail}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">示例</h4>
                        <pre className="text-xs text-slate-400 bg-slate-900/50 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                          {step.example}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Key Principles */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-blue-500/10 rounded-xl flex items-center justify-center">
              <i className="fas fa-brain text-blue-400 text-xl"></i>
            </div>
            <h4 className="font-semibold text-white mb-2">自主规划</h4>
            <p className="text-xs text-slate-400">Agent 能够自主分解任务、规划步骤，而非简单的一问一答</p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-purple-500/10 rounded-xl flex items-center justify-center">
              <i className="fas fa-shield-alt text-purple-400 text-xl"></i>
            </div>
            <h4 className="font-semibold text-white mb-2">权限边界</h4>
            <p className="text-xs text-slate-400">敏感操作必须经过人工确认，Agent 不会越权执行</p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-green-500/10 rounded-xl flex items-center justify-center">
              <i className="fas fa-sync text-green-400 text-xl"></i>
            </div>
            <h4 className="font-semibold text-white mb-2">持续学习</h4>
            <p className="text-xs text-slate-400">通过 Memory 系统积累经验，不断优化决策质量</p>
          </div>
        </div>
      </div>
    </section>
  );
}
