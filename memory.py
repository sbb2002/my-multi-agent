import time
import chromadb
import hashlib
from google import genai

# 벡터DB 초기화 (로컬 파일로 영속 저장)
chroma_client = chromadb.PersistentClient(path="./memory_db")
collection = chroma_client.get_or_create_collection("agent_memory")


def _embed(client, text: str) -> list[float]:
    """텍스트를 벡터로 변환 — 의미 기반 검색을 위해 필요"""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings


def save_memory(client, content: str, topic: str, importance: float = 1.0):
    """기억 저장 — importance가 낮을수록 망각 우선순위 높음"""
    memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()
    collection.add(
        ids=[memory_id],
        embeddings=[_embed(client, content)],
        documents=[content],
        metadatas=[{
            "topic": topic,
            "timestamp": time.time(),
            "importance": importance,
            "access_count": 0,  # 자주 참조될수록 망각 방지
        }]
    )


def recall_memory(client, query: str, topic: str = None, top_k: int = 3) -> list[str]:
    """관련 기억 검색 — 의미적으로 유사한 것만 꺼냄"""
    where = {"topic": topic} if topic else None
    results = collection.query(
        query_embeddings=[_embed(client, query)],
        n_results=top_k,
        where=where,
    )

    # 참조 횟수 업데이트 (자주 쓰이는 기억은 오래 유지)
    if results["ids"][0]:
        for mem_id in results["ids"][0]:
            existing = collection.get(ids=[mem_id])
            meta = existing["metadatas"][0]
            meta["access_count"] += 1
            collection.update(ids=[mem_id], metadatas=[meta])

    return results["documents"][0] if results["documents"] else []


def forget_old_memories(max_age_days: int = 7, min_importance: float = 0.5):
    """
    망각 메커니즘 — 핵심입니다
    오래되고 중요도 낮고 참조 안 된 기억을 삭제
    """
    all_memories = collection.get()
    now = time.time()
    to_delete = []

    for mem_id, meta in zip(all_memories["ids"], all_memories["metadatas"]):
        age_days = (now - meta["timestamp"]) / 86400
        importance = meta["importance"]
        access_count = meta.get("access_count", 0)

        # 망각 조건: 오래됐고 + 중요도 낮고 + 참조 없음
        should_forget = (
            age_days > max_age_days
            and importance < min_importance
            and access_count < 2
        )
        if should_forget:
            to_delete.append(mem_id)

    if to_delete:
        collection.delete(ids=to_delete)
        print(f"[Memory] {len(to_delete)}개 기억 망각")