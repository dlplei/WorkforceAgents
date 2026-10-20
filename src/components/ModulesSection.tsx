import { useState } from 'react';

const modules = [
  {
    id: 'orchestration', title: 'Agent Orchestration 层', icon: 'fa-brain', color: 'purple',
    desc: '系统核心，负责"理解、规划、执行、纠错"',
    items: [
      { name: '意图识别', desc: '识别政策咨询、休假、差旅、调动、工单等意图，支持多轮澄清' },
      { name: '任务规划', desc: '将复杂目标拆分为身份校验、上下文获取、政策检索、草稿生成等步骤' },
      { name: 'Tool Router', desc: '根据任务步骤选择工具，调用前执行参数校验、权限校验和风险评估' },
      { name: 'Memory Manager', desc: '管理会话短期记忆、任务记忆和低敏偏好记忆，支持中断恢复' },
      { name: 'Policy Guard', desc: '确保政策回答基于检索结果，避免幻觉，不确定内容提示人工确认' },
      { name: 'HITL Engine', desc: '高风险/低置信度/越权边缘场景引入人工审批' },
    ],
  },
  {
    id: 'knowledge', title: '知识与 Policy Grounding 层', icon: 'fa-book', color: 'cyan',
    desc: '知识来源：员工手册、HR政策、差旅政策、薪酬福利、劳动法规、流程规范',
    items: [
      { name: '查询重写', desc: 'Query Rewrite 优化检索效果' },
      { name: '权限过滤', desc: 'ACL-based Filtering 确保数据访问合规' },
      { name: '混合检索', desc: '向量检索 + 关键词检索 Hybrid Search' },
      { name: '政策召回', desc: 'Policy Chunk Retrieval 精准匹配' },
      { name: 'Grounded 生成', desc: '基于政策生成回答，标注引用来源' },
      { name: '适用条件', desc: '返回适用范围、生效日期和限制条件' },
    ],
  },
  {
    id: 'context', title: '用户上下文融合层', icon: 'fa-user', color: 'blue',
    desc: '融合员工身份、组织关系、权限、福利、流程状态等多维上下文',
    items: [
      { name: '基础信息', desc: '员工ID、姓名、岗位、部门' },
      { name: '雇佣信息', desc: '入职日期、合同类型、员工类型' },
      { name: '组织信息', desc: '汇报经理、成本中心、所在地' },
      { name: '权限信息', desc: '是否HR、是否经理、是否审批人' },
      { name: '福利信息', desc: '假期余额、福利资格' },
      { name: '流程状态', desc: '当前审批、历史工单、待补充事项' },
    ],
  },
];

const tools = [
  { name: 'Employee Profile API', desc: '查询员工基础信息', scene: '所有场景前置' },
  { name: 'Leave Balance API', desc: '查询休假余额', scene: '休假咨询' },
  { name: 'Leave Request API', desc: '创建/查询休假申请', scene: '休假申请' },
  { name: 'Travel Request API', desc: '创建差旅申请、检查预算', scene: '差旅申请' },
  { name: 'Policy Search Tool', desc: '检索企业政策与FAQ', scene: '政策咨询' },
  { name: 'Approval Workflow API', desc: '发起/查询/催办审批', scene: '所有审批' },
  { name: 'HR Ticket API', desc: '创建/分类/查询工单', scene: 'Service Request' },
  { name: 'Org Chart API', desc: '查询组织关系/汇报链', scene: '调动/审批' },
  { name: 'Calendar API', desc: '检查日程冲突', scene: '休假/差旅' },
  { name: 'Notification API', desc: '发送各类通知提醒', scene: '全场景' },
  { name: 'Document Generation', desc: '生成申请材料/证明', scene: '审批准备' },
  { name: 'Transfer API', desc: '发起调动流程', scene: '员工调动' },
  { name: 'Compensation Calc', desc: '计算薪酬/社保变动', scene: '调动评估' },
];

const colorMap: Record<string, { bg: string; border: string; text: string }> = {
  purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-300' },
  cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-300' },
  blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-300' },
};

export default function ModulesSection() {
  const [activeTab, setActiveTab] = useState<'modules' | 'tools'>('modules');

  return (
    <section id="modules" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">核心模块 & 工具清单</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">Agent 核心能力模块与企业系统工具 API 清单</p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center space-x-4 mb-8">
          <button
            onClick={() => setActiveTab('modules')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'modules' ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50'
            }`}
          >
            <i className="fas fa-cubes mr-2"></i>核心模块
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'tools' ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50'
            }`}
          >
            <i className="fas fa-wrench mr-2"></i>工具 API 清单
          </button>
        </div>

        {activeTab === 'modules' ? (
          <div className="space-y-6">
            {modules.map((mod) => {
              const c = colorMap[mod.color];
              return (
                <div key={mod.id} className={`${c.bg} ${c.border} border rounded-xl p-5`}>
                  <div className="flex items-center space-x-3 mb-4">
                    <i className={`fas ${mod.icon} ${c.text} text-lg`}></i>
                    <div>
                      <h3 className={`font-bold ${c.text}`}>{mod.title}</h3>
                      <p className="text-xs text-slate-400">{mod.desc}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {mod.items.map((item, i) => (
                      <div key={i} className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/50">
                        <h4 className="text-sm font-semibold text-white mb-1">{item.name}</h4>
                        <p className="text-xs text-slate-400">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-800/80 border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">工具名称</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">功能</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">调用场景</th>
                  </tr>
                </thead>
                <tbody>
                  {tools.map((tool, i) => (
                    <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors">
                      <td className="py-3 px-4 text-cyan-300 font-medium">{tool.name}</td>
                      <td className="py-3 px-4 text-slate-300">{tool.desc}</td>
                      <td className="py-3 px-4"><span className="text-xs bg-cyan-500/10 text-cyan-300 px-2 py-0.5 rounded">{tool.scene}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
