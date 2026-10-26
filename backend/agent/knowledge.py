"""
RAG 知识库 - Mock 政策文档 + 检索器
"""
import os
import re
from pathlib import Path
from typing import List, Optional
import httpx
import yaml
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None
from models import PolicyDocument, KnowledgeChunk

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8002"))
COLLECTION_NAME = "hr_policy_collection"
EMBEDDING_MODEL = "bge-m3"

_chroma_client = None
_chroma_collection = None


def get_chroma_collection():
    """获取或初始化 Chroma 向量集合"""
    global _chroma_client, _chroma_collection
    if chromadb is None:
        return None
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



# ============ 政策文档加载器 (Data Layer) ============

POLICIES_DIR = Path(os.getenv("POLICIES_DIR", Path(__file__).resolve().parent.parent / "data" / "policies"))


def parse_markdown_policy(file_path: Path) -> Optional[PolicyDocument]:
    """解析包含 YAML Frontmatter 的 Markdown 政策文档"""
    try:
        text = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        if match:
            frontmatter_text, content = match.groups()
            meta = yaml.safe_load(frontmatter_text) or {}
        else:
            meta = {}
            content = text

        doc_id = str(meta.get("id", file_path.stem))
        title = str(meta.get("title", file_path.stem))
        category = str(meta.get("category", "综合"))
        effective_date = str(meta.get("effective_date", "2025-01-01"))
        applicable_to = meta.get("applicable_to", ["全职员工"])
        if isinstance(applicable_to, str):
            applicable_to = [applicable_to]

        return PolicyDocument(
            id=doc_id,
            title=title,
            category=category,
            effective_date=effective_date,
            applicable_to=list(applicable_to),
            content=content.strip(),
        )
    except Exception as e:
        print(f"[Knowledge] Failed to load policy from {file_path}: {e}")
        return None


def load_policies_from_dir(dir_path: Path = POLICIES_DIR) -> List[PolicyDocument]:
    """从本地 Markdown 政策文件目录动态加载所有政策"""
    if not dir_path.exists():
        print(f"[Knowledge] Policy directory not found: {dir_path}")
        return []

    docs: List[PolicyDocument] = []
    for md_file in sorted(dir_path.glob("*.md")):
        doc = parse_markdown_policy(md_file)
        if doc:
            docs.append(doc)

    print(f"[Knowledge] Loaded {len(docs)} policy documents from {dir_path}")
    return docs


def reload_policies(dir_path: Path = POLICIES_DIR) -> List[PolicyDocument]:
    """热重载政策文档"""
    global policy_documents
    policy_documents = load_policies_from_dir(dir_path)
    return policy_documents


# 初始化加载政策文档
policy_documents: List[PolicyDocument] = load_policies_from_dir()


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
