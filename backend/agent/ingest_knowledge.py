"""
将 HR 政策文档向量化并存入 Chroma 向量数据库
使用 Ollama 托管的 BGE-M3 (1024-dim) 嵌入模型
"""
import os
import re
from typing import List, Dict, Any
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import chromadb
from chromadb.config import Settings

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8002"))
COLLECTION_NAME = "hr_policy_collection"
EMBEDDING_MODEL = "bge-m3"


def get_embedding(text: str) -> List[float]:
    """通过本地 Ollama 获取文本的 BGE 向量"""
    url = f"{OLLAMA_URL}/api/embeddings"
    with httpx.Client(timeout=60.0, trust_env=False) as client:
        resp = client.post(url, json={"model": EMBEDDING_MODEL, "prompt": text})
        resp.raise_for_status()
        return resp.json()["embedding"]


def chunk_document(doc_id: str, title: str, category: str, content: str, effective_date: str = "") -> List[Dict[str, Any]]:
    """按条款/章节切分文档"""
    chunks = []
    # 按照 "一、"、"二、" 等条款章节分割
    sections = re.split(r'\n(?=[一二三四五六七八九十]+、)', content)
    chunk_index = 0
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        chunk_text = f"【{title} - {category}】\n{sec}"
        chunks.append({
            "id": f"{doc_id}-c{chunk_index}",
            "doc_id": doc_id,
            "title": title,
            "category": category,
            "effective_date": effective_date,
            "content": chunk_text
        })
        chunk_index += 1
    return chunks


def ingest():
    """执行知识库向量化入库（读取 backend/data/policies/*.md）"""
    from knowledge import policy_documents

    print(f"Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}...")
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )

    # 获取或创建集合（使用余弦相似度 cosine）
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # 统计切片
    all_chunks = []
    for doc in policy_documents:
        chunks = chunk_document(doc.id, doc.title, doc.category, doc.content, getattr(doc, "effective_date", ""))
        all_chunks.extend(chunks)

    print(f"Total chunks to ingest: {len(all_chunks)} (from {len(policy_documents)} Markdown policies)")
    
    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for idx, c in enumerate(all_chunks):
        chunk_id = c["id"]
        content = c["content"]
        print(f"[{idx+1}/{len(all_chunks)}] Generating embedding for {c['title']} ({chunk_id})...")
        emb = get_embedding(content)
        
        ids.append(chunk_id)
        documents.append(content)
        metadatas.append({
            "doc_id": c["doc_id"],
            "title": c["title"],
            "category": c["category"],
            "effective_date": c.get("effective_date", ""),
        })
        embeddings.append(emb)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )
    print(f"Successfully ingested {len(ids)} chunks into Chroma collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    ingest()
