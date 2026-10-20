// ============================================================
// RAG Knowledge Base - Mock Policies + Retrieval
// ============================================================
import type { PolicyDocument, KnowledgeChunk } from '../types';

// --- Mock Policy Documents ---
export const policyDocuments: PolicyDocument[] = [
  {
    id: 'POL-001',
    title: '员工年假管理办法',
    category: '休假',
    effectiveDate: '2025-01-01',
    applicableTo: ['全职员工'],
    content: `
一、年假天数标准：
- 入职满1年不满10年：5天/年
- 入职满10年不满20年：10天/年
- 入职满20年及以上：15天/年

二、申请规则：
- 请假如超过3天，需提前5个工作日申请
- 请假如超过5天，需提前10个工作日申请
- 单次请假最长不超过15个工作日
- 年假可分次使用，最小单位为0.5天

三、审批流程：
- 3天以内：直属经理审批
- 3-5天：直属经理 + 部门总监审批
- 5天以上：直属经理 + 部门总监 + HRBP审批

四、特殊情况：
- 项目关键期（如上线前2周）原则上不批年假
- 团队成员同时休假不得超过部门总人数的20%
- 未休完年假可在次年Q1前补休，过期作废

五、薪资计算：
- 年假期间正常发放工资
- 如年假与法定节假日相连，按实际工作日计算
`,
  },
  {
    id: 'POL-002',
    title: '员工病假管理规定',
    category: '休假',
    effectiveDate: '2025-01-01',
    applicableTo: ['全职员工'],
    content: `
一、病假天数：
- 每年享有5天带薪病假
- 超出部分按事假处理或提供医院证明后可申请特殊病假

二、申请规则：
- 当日生病可事后补假，但需在返岗后1个工作日内提交
- 超过1天的病假需提供医院诊断证明
- 连续病假超过3天需部门经理和HR双重审批

三、薪资计算：
- 5天以内带薪病假：100%工资
- 超出部分：按当地最低工资标准的80%发放
`,
  },
  {
    id: 'POL-003',
    title: '差旅管理制度',
    category: '差旅',
    effectiveDate: '2025-03-01',
    applicableTo: ['全职员工'],
    content: `
一、差旅审批：
- 市内出差：直属经理审批
- 国内出差：直属经理 + 部门总监审批
- 国际出差：直属经理 + 部门总监 + VP审批

二、交通标准：
- P5及以下：高铁二等座 / 经济舱
- P6-P7：高铁一等座 / 经济舱（4小时以上航程可商务舱）
- P8及以上：高铁商务座 / 商务舱

三、住宿标准（元/晚）：
- 一线城市（北上广深）：P6以下400元，P6-P7 600元，P8+ 1000元
- 二线城市：P6以下300元，P6-P7 500元，P8+ 800元
- 三线及以下：P6以下250元，P6-P7 400元，P8+ 600元

四、餐饮补贴（元/天）：
- 一线城市：100元/天
- 二线城市：80元/天
- 三线及以下：60元/天

五、报销规则：
- 出差结束后5个工作日内提交报销
- 需提供正规发票
- 超标部分需提前申请例外审批
`,
  },
  {
    id: 'POL-004',
    title: '员工调动管理办法',
    category: '调动',
    effectiveDate: '2025-01-01',
    applicableTo: ['全职员工（入职满1年）'],
    content: `
一、调动条件：
- 在当前岗位工作满1年
- 绩效评估达到B+及以上
- 目标岗位有空缺HC
- 获得现部门经理和目标部门经理双方同意

二、调动类型：
- 同城市跨部门调动
- 跨城市调动
- 跨子公司调动

三、审批流程：
- 同城市调动：双方部门经理 + HRBP
- 跨城市调动：双方部门经理 + 双方部门总监 + HRBP + 薪酬委员会
- 跨子公司：额外需要VP审批

四、薪酬调整：
- 同城市调动：原则上不调薪
- 跨城市调动：根据目标城市生活成本指数调整，幅度5%-20%
- 跨城市调动额外享有：搬迁补贴（最高2万元）、首月住房补贴

五、社保公积金：
- 跨城市调动次月转入新城市社保公积金
- 调动当月按原城市标准缴纳
`,
  },
  {
    id: 'POL-005',
    title: '证明开具管理规定',
    category: '服务',
    effectiveDate: '2025-01-01',
    applicableTo: ['全体员工'],
    content: `
一、可开具证明类型：
- 在职证明
- 收入证明
- 离职证明
- 实习证明

二、申请流程：
- 通过HR系统提交申请
- 选择证明类型和用途
- HR专员1-2个工作日内处理
- 电子证明即时生成，纸质证明需到HR窗口领取

三、收入证明特殊规则：
- 仅证明税前月收入
- 不包含奖金、股票等浮动收入
- 需注明用途（如贷款、签证等）
- 同一用途30天内不可重复开具

四、费用：
- 中文版本：免费
- 英文版本：免费
- 公证版本：需额外支付公证费用
`,
  },
  {
    id: 'POL-006',
    title: '弹性工作制度',
    category: '考勤',
    effectiveDate: '2025-06-01',
    applicableTo: ['技术研发部', '产品设计部', '市场部'],
    content: `
一、弹性工作时间：
- 核心工作时间：10:00 - 16:00（必须在岗）
- 弹性上班时段：7:00 - 10:00
- 弹性下班时段：16:00 - 20:00
- 每日工作时长不少于8小时

二、远程办公：
- 每周最多2天远程办公
- 需提前1天在系统申请
- 远程办公期间需保持即时通讯在线
- 部门可根据项目情况调整远程天数

三、加班规则：
- 工作日超过10小时部分计入调休
- 周末加班按1.5倍工资或调休（二选一）
- 法定节假日加班按3倍工资
- 每月加班不超过36小时（劳动法要求）
`,
  },
  {
    id: 'POL-007',
    title: '员工福利手册',
    category: '福利',
    effectiveDate: '2025-01-01',
    applicableTo: ['全职员工'],
    content: `
一、法定福利：
- 五险一金（养老、医疗、失业、工伤、生育 + 住房公积金）
- 公积金缴存比例：12%（公司+个人各12%）

二、补充福利：
- 补充商业医疗保险（覆盖员工+配偶+子女）
- 年度体检（含家属1名）
- 节日礼金（春节/中秋/端午各500元）
- 生日礼金（300元）
- 结婚礼金（2000元）
- 生育礼金（3000元）

三、发展福利：
- 年度培训经费（5000元/人）
- 外部认证考试报销（每年最多2次）
- 内部转岗机会（入职满1年可申请）

四、生活福利：
- 免费午餐补贴（25元/工作日）
- 健身房会员补贴（200元/月）
- 员工折扣平台
`,
  },
];

// --- Simple RAG Retriever ---
// Uses keyword matching + category filtering for demo purposes
// In production, this would use vector embeddings + cosine similarity

export function retrieveKnowledge(
  query: string,
  topK: number = 3,
  categoryFilter?: string
): KnowledgeChunk[] {
  const queryLower = query.toLowerCase();
  const queryTokens = tokenize(queryLower);

  const scored: KnowledgeChunk[] = [];

  for (const doc of policyDocuments) {
    // Category filter
    if (categoryFilter && doc.category !== categoryFilter) continue;

    const contentLower = doc.content.toLowerCase();
    const titleLower = doc.title.toLowerCase();

    // Calculate relevance score
    let score = 0;

    // Title match (high weight)
    for (const token of queryTokens) {
      if (titleLower.includes(token)) score += 3;
    }

    // Content keyword match
    for (const token of queryTokens) {
      const matches = (contentLower.match(new RegExp(escapeRegex(token), 'g')) || []).length;
      score += matches;
    }

    // Category keyword boost
    const categoryKeywords: Record<string, string[]> = {
      '休假': ['请假', '年假', '病假', '休假', '假期', '放假', 'leave'],
      '差旅': ['出差', '差旅', '机票', '酒店', '住宿', '交通', 'travel'],
      '调动': ['调动', '转岗', '转移', '城市', 'transfer'],
      '服务': ['证明', '开具', '申请', 'service'],
      '考勤': ['考勤', '打卡', '弹性', '远程', '加班', '上班'],
      '福利': ['福利', '保险', '公积金', '补贴', '体检', 'benefit'],
    };

    for (const [cat, keywords] of Object.entries(categoryKeywords)) {
      if (cat === doc.category) {
        for (const kw of keywords) {
          if (queryLower.includes(kw)) score += 2;
        }
      }
    }

    if (score > 0) {
      // Split content into relevant chunks
      const relevantContent = extractRelevantParagraphs(doc.content, queryTokens);
      scored.push({
        docId: doc.id,
        title: doc.title,
        content: relevantContent || doc.content.slice(0, 500),
        score,
        category: doc.category,
      });
    }
  }

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK);
}

function tokenize(text: string): string[] {
  // Simple tokenization: split by non-Chinese/non-alphanumeric chars
  const tokens: string[] = [];
  // Extract Chinese words (2-4 chars)
  const chineseMatches = text.match(/[\u4e00-\u9fa5]{2,4}/g) || [];
  tokens.push(...chineseMatches);
  // Extract English words
  const englishMatches = text.match(/[a-zA-Z]{2,}/g) || [];
  tokens.push(...englishMatches);
  // Also add individual significant Chinese chars
  const singleChars = text.match(/[\u4e00-\u9fa5]/g) || [];
  tokens.push(...singleChars);
  return [...new Set(tokens)];
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function extractRelevantParagraphs(content: string, queryTokens: string[]): string {
  const paragraphs = content.split('\n').filter(p => p.trim().length > 0);
  const scoredParagraphs = paragraphs.map(p => {
    const pLower = p.toLowerCase();
    let score = 0;
    for (const token of queryTokens) {
      if (pLower.includes(token)) score++;
    }
    return { text: p.trim(), score };
  });

  scoredParagraphs.sort((a, b) => b.score - a.score);
  const topParagraphs = scoredParagraphs.filter(p => p.score > 0).slice(0, 5);

  if (topParagraphs.length === 0) return content.slice(0, 300);
  return topParagraphs.map(p => p.text).join('\n');
}

// Get all policy categories
export function getPolicyCategories(): string[] {
  return [...new Set(policyDocuments.map(d => d.category))];
}

// Get policy by ID
export function getPolicyById(id: string): PolicyDocument | undefined {
  return policyDocuments.find(d => d.id === id);
}
