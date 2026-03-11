import re
import time
import hashlib
from services.core.client import collection
from services.request import request_embedding, query_to_db, add_to_db, update_info


def get_memory():
    """기억을 불러오는 메서드. (엔드포인트 정리용)"""
    all_memories = collection.get()
    memories = [
        {"doc": doc, "meta": meta}
        for doc, meta in zip(
            all_memories["documents"], 
            all_memories["metadatas"]
        )
    ]
    return memories

def delete_memory():
    """기억 소거 메서드."""
    all_ids = collection.get()["ids"]
    if all_ids:
        collection.delete(ids=all_ids)

def remember_memory(query: str, top_k:int = 3) -> list[str]:
    """DB에서 content에 대해 주제가 비슷한 것을 기억하는 메서드."""
    # 쿼리에 대해 유사한 기억 추출
    embedded_query = request_embedding(query)
    memories = query_to_db(embedded_query, top_k)

    # 참조 횟수 업데이트
    if memories is None:
        return []
    
    mem_ids = memories['ids'][0] if memories['ids'][0] else None
    if mem_ids is not None:
        for mem_id in mem_ids:
            memory = collection.get(ids=[mem_id])
            meta = memory['metadatas'][0]
            meta['access_count'] += 1

            update_info(id=mem_id, metadata=meta)
    
    documents = memories['documents'][0] if memories['documents'] else []

    return documents

def process_memory_system_msg(system: str, memory_documents: list = []) -> str:
    """쿼리에 대해 비슷한 기억을 가져오고 전처리하는 메서드."""
    if memory_documents:
        memory_context = "\n".join(
            f"- {m}" for m in memory_documents)
        system = f"{system}\n\n[관련 기억]\n{memory_context}\n\n"
    return system

def save_memory(content: str, importance: float = 1.0):
    """기억 저장 — importance가 낮을수록 망각 우선순위 높음"""
    
    # Content로부터 topic, summary 분리
    splitted_content = content.split('\n')
    topic_text = splitted_content[0]
    summary_text = splitted_content[1]
    
    topic_pattern = r'\[주제\]\s(.+)'
    summary_pattern = r'\[요약\]\s(.+)'

    topics = re.sub(topic_pattern, r'\1', topic_text)
    summary = re.sub(summary_pattern, r'\1', summary_text)

    # topic 별 임베딩
    topics = re.sub(r'[^\w,]', '', topics).split(',')
    for topic in topics:
        memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()
        metadata = {
                "topic" : topic,
                "timestamp" : time.time(),
                "importance" : importance,
                "access_count" : 0
            }
        add_to_db(
            id=memory_id,
            embedding=request_embedding(summary),
            document=summary,
            metadata=metadata
        )

