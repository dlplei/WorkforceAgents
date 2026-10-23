"""
RAG 知识库 - Mock 政策文档 + 检索器
"""
import os
import re
from typing import List, Optional
import httpx
import chromadb
from chromadb.config import Settings
from models import PolicyDocument, KnowledgeChunk

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = "hr_policy_collection"
EMBEDDING_MODEL = "bge-m3"

_chroma_client = None
_chroma_collection = None


def get_chroma_collection():
    """获取或初始化 Chroma 向量集合"""
    global _chroma_client, _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection

    try:
        if _chroma_client is None:
            _chroma_client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT,
                settings=Settings(allow_reset=True, anonymized_telemetry=False)
            )
        _chroma_collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        return _chroma_collection
    except Exception as e:
        print(f"[Knowledge] Failed to connect to Chroma: {e}")
        return None


def get_query_embedding(query: str) -> Optional[List[float]]:
    """调用 Ollama 获取 Query 向量"""
    try:
        url = f"{OLLAMA_URL}/api/embeddings"
        with httpx.Client(timeout=30.0, trust_env=False) as client:
            resp = client.post(url, json={"model": EMBEDDING_MODEL, "prompt": query})
            if resp.status_code == 200:
                return resp.json()["embedding"]
    except Exception as e:
        print(f"[Knowledge] Ollama embedding failed: {e}")
    return None



# ============ Mock 政策文档 ============

policy_documents: List[PolicyDocument] = [
    PolicyDocument(
        id="POL-001",
        title="员工年假管理办法",
        category="休假",
        effective_date="2025-01-01",
        applicable_to=["全职员工"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-002",
        title="员工病假管理规定",
        category="休假",
        effective_date="2025-01-01",
        applicable_to=["全职员工"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-003",
        title="差旅管理制度",
        category="差旅",
        effective_date="2025-03-01",
        applicable_to=["全职员工"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-004",
        title="员工调动管理办法",
        category="调动",
        effective_date="2025-01-01",
        applicable_to=["全职员工（入职满1年）"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-005",
        title="证明开具管理规定",
        category="服务",
        effective_date="2025-01-01",
        applicable_to=["全体员工"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-006",
        title="弹性工作制度",
        category="考勤",
        effective_date="2025-06-01",
        applicable_to=["技术研发部", "产品设计部", "市场部"],
        content="""
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
""",
    ),
    PolicyDocument(
        id="POL-007",
        title="员工福利手册",
        category="福利",
        effective_date="2025-01-01",
        applicable_to=["全职员工"],
        content="""
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
""",
    ),
]


# ============ 检索器 ============

def tokenize(text: str) -> List[str]:
    """简单分词"""
    tokens = []
    # 提取中文词（2-4字）
    chinese_matches = re.findall(r"[\u4e00-\u9fa5]{2,4}", text)
    tokens.extend(chinese_matches)
    # 提取英文词
    english_matches = re.findall(r"[a-zA-Z]{2,}", text)
    tokens.extend(english_matches)
    # 添加单字
    single_chars = re.findall(r"[\u4e00-\u9fa5]", text)
    tokens.extend(single_chars)
    return list(set(tokens))


def extract_relevant_paragraphs(content: str, query_tokens: List[str]) -> str:
    """提取相关段落"""
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    scored = []
    for p in paragraphs:
        p_lower = p.lower()
        score = sum(1 for token in query_tokens if token in p_lower)
        scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [p for p, s in scored if s > 0][:5]

    if not top:
        return content[:300]
    return "\n".join(top)


def _retrieve_by_keywords(
    query: str,
    top_k: int = 3,
    category_filter: Optional[str] = None,
) -> List[KnowledgeChunk]:
    """兜底：基于关键词匹配的本地检索"""
    query_lower = query.lower()
    query_tokens = tokenize(query_lower)

    scored: List[KnowledgeChunk] = []

    category_keywords = {
        "休假": ["请假", "年假", "病假", "休假", "假期", "放假", "leave"],
        "差旅": ["出差", "差旅", "机票", "酒店", "住宿", "交通", "travel"],
        "调动": ["调动", "转岗", "转移", "城市", "transfer"],
        "服务": ["证明", "开具", "申请", "service"],
        "考勤": ["考勤", "打卡", "弹性", "远程", "加班", "上班"],
        "福利": ["福利", "保险", "公积金", "补贴", "体检", "benefit"],
    }

    for doc in policy_documents:
        if category_filter and doc.category != category_filter:
            continue

        content_lower = doc.content.lower()
        title_lower = doc.title.lower()

        score = 0
        for token in query_tokens:
            if token in title_lower:
                score += 3
        for token in query_tokens:
            matches = len(re.findall(re.escape(token), content_lower))
            score += matches
        for cat, keywords in category_keywords.items():
            if cat == doc.category:
                for kw in keywords:
                    if kw in query_lower:
                        score += 2

        if score > 0:
            relevant_content = extract_relevant_paragraphs(doc.content, query_tokens)
            scored.append(
                KnowledgeChunk(
                    doc_id=doc.id,
                    title=doc.title,
                    content=relevant_content,
                    score=float(score),
                    category=doc.category,
                )
            )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    category_filter: Optional[str] = None,
) -> List[KnowledgeChunk]:
    """
    语义向量 RAG 检索器：
    1. 优先使用 Ollama BGE-M3 生成向量并查询 Chroma
    2. 支持 Cosine 相似度评分过滤
    3. 发生网络或服务故障时无缝退回关键词匹配
    """
    try:
        collection = get_chroma_collection()
        if collection:
            query_emb = get_query_embedding(query)
            if query_emb:
                where_filter = {"category": category_filter} if category_filter else None
                results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
                
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                
                if docs:
                    chunks = []
                    for doc_text, meta, dist in zip(docs, metas, distances):
                        # 余弦距离转为余弦相似度分数 (1.0 - distance)
                        sim_score = max(0.0, round(1.0 - float(dist), 4))
                        chunks.append(
                            KnowledgeChunk(
                                doc_id=meta.get("doc_id", "DOC"),
                                title=meta.get("title", ""),
                                content=doc_text,
                                score=sim_score,
                                category=meta.get("category", "")
                            )
                        )
                    return chunks
    except Exception as e:
        print(f"[Knowledge] Vector retrieval fallback triggered: {e}")

    # Fallback 到关键词检索
    return _retrieve_by_keywords(query, top_k=top_k, category_filter=category_filter)



def get_policy_categories() -> List[str]:
    """获取所有政策类别"""
    return list(set(d.category for d in policy_documents))


def get_policy_by_id(doc_id: str) -> Optional[PolicyDocument]:
    """根据 ID 获取政策"""
    for doc in policy_documents:
        if doc.id == doc_id:
            return doc
    return None
