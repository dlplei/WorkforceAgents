export default function TechStack() {
  const categories = [
    {
      title: 'LLM & AI 引擎',
      icon: 'fa-brain',
      color: 'purple',
      items: [
        { name: 'GPT-4 / Claude 3.5', desc: '主推理模型，复杂任务规划', tag: 'Core' },
        { name: 'GPT-4o-mini / Haiku', desc: '轻量任务，意图分类', tag: 'Fast' },
        { name: 'Embedding (text-embedding-3)', desc: '向量化用于 RAG 检索', tag: 'RAG' },
        { name: 'LangChain / LlamaIndex', desc: 'Agent 框架与编排', tag: 'Framework' },
      ],
    },
    {
      title: 'Agent 框架',
      icon: 'fa-robot',
      color: 'blue',
      items: [
        { name: 'LangGraph', desc: '状态机驱动的 Agent 工作流', tag: 'Core' },
        { name: 'CrewAI / AutoGen', desc: '多 Agent 协作编排', tag: 'Multi' },
        { name: 'Semantic Kernel', desc: '企业级 AI 编排框架', tag: 'Enterprise' },
        { name: '自研 Orchestrator', desc: '任务图引擎 + 状态管理', tag: 'Custom' },
      ],
    },
    {
      title: '知识管理',
      icon: 'fa-database',
      color: 'cyan',
      items: [
        { name: 'Pinecone / Weaviate', desc: '向量数据库，政策知识检索', tag: 'Vector DB' },
        { name: 'Elasticsearch', desc: '全文检索 + 结构化查询', tag: 'Search' },
        { name: 'Redis', desc: '会话缓存 + 短期记忆', tag: 'Cache' },
        { name: 'PostgreSQL + pgvector', desc: '业务数据 + 轻量向量', tag: 'SQL' },
      ],
    },
    {
      title: '基础设施',
      icon: 'fa-cloud',
      color: 'green',
      items: [
        { name: 'Kubernetes (EKS/ACK)', desc: '容器编排与弹性伸缩', tag: 'Infra' },
        { name: 'API Gateway (Kong)', desc: 'API 管理、限流、鉴权', tag: 'Gateway' },
        { name: 'Kafka / RabbitMQ', desc: '事件驱动，异步任务', tag: 'MQ' },
        { name: 'Prometheus + Grafana', desc: '监控告警与可观测性', tag: 'Monitor' },
      ],
    },
    {
      title: '集成与接口',
      icon: 'fa-plug',
      color: 'amber',
      items: [
        { name: 'Workday / SAP SuccessFactors', desc: '核心 HRIS 系统', tag: 'HRIS' },
        { name: '钉钉/飞书/Teams SDK', desc: 'IM 集成与消息推送', tag: 'IM' },
        { name: 'Camunda / Flowable', desc: 'BPM 审批流引擎', tag: 'BPM' },
        { name: 'OAuth2 / SAML', desc: '统一身份认证', tag: 'Auth' },
      ],
    },
    {
      title: '安全与合规',
      icon: 'fa-lock',
      color: 'rose',
      items: [
        { name: 'Guardrails AI', desc: 'LLM 输出安全护栏', tag: 'Safety' },
        { name: 'Azure Purview / AWS Macie', desc: '数据分类与脱敏', tag: 'DLP' },
        { name: 'Vault (HashiCorp)', desc: '密钥与凭证管理', tag: 'Secret' },
        { name: 'Audit Log Service', desc: '全链路审计追踪', tag: 'Audit' },
      ],
    },
  ];

  const colorClasses: Record<string, { bg: string; border: string; text: string; tag: string }> = {
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', tag: 'bg-purple-500/20 text-purple-300' },
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', tag: 'bg-blue-500/20 text-blue-300' },
    cyan: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400', tag: 'bg-cyan-500/20 text-cyan-300' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', tag: 'bg-green-500/20 text-green-300' },
    amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', tag: 'bg-amber-500/20 text-amber-300' },
    rose: { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400', tag: 'bg-rose-500/20 text-rose-300' },
  };

  return (
    <section id="techstack" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
              技术栈选型
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            企业级技术选型，兼顾性能、安全与可扩展性
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => {
            const colors = colorClasses[category.color];
            return (
              <div key={category.title} className={`${colors.bg} ${colors.border} border rounded-xl p-5 hover:scale-[1.02] transition-transform`}>
                <div className="flex items-center space-x-2 mb-4">
                  <i className={`fas ${category.icon} ${colors.text} text-lg`}></i>
                  <h3 className={`font-semibold ${colors.text}`}>{category.title}</h3>
                </div>
                <div className="space-y-3">
                  {category.items.map((item) => (
                    <div key={item.name} className="bg-slate-800/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white">{item.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors.tag}`}>{item.tag}</span>
                      </div>
                      <p className="text-xs text-slate-400">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
