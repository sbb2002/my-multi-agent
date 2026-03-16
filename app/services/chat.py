from google.genai import types

# Local imports
from services.core.client import gemini_client
from services.memory import (
    remember_memory, process_memory_system_msg, save_memory)
from services.request import request_summarization, retrieve_rag_context
from services.metric import get_similarity
from services.core.loader import load_role


def build_history(history: list[dict]) -> dict:
    """프론트(채팅창)에서 받은 history를 gemini api 형식으로 반환"""
    gemini_history = []
    for item in history:
        role = 'user' if item['role'] == 'user' else 'model'
        gemini_history.append(
            types.Content(
                role=role,
                parts=[types.Part(text=item['content'])]
            )
        )
    return gemini_history

async def chat(message: str, history: list[dict]) -> str:
    """History-based Gemini Chatbot 호출"""
    
    # System role
    system = load_role('chatbot.yaml')

    # Inject the memories
    memory = remember_memory(message)
    system = process_memory_system_msg(system, memory)

    # Inject RAG context
    rag_context = retrieve_rag_context(message)
    if rag_context:
        system += f"\n\n[참고 문서]\n{rag_context}\n"

    # Combine previous talk + new message
    contents = build_history(history) +[
        types.Content(
            role='user',
            parts=[types.Part(text=message)]
        )
    ]

    # Request to API; Answering
    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )

    response = await gemini_client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=config
    )

    answer = response.text

    # Summarization & Similarity evaluation
    summary = await request_summarization(
        question=message,
        answer=answer
    )
    similarity = get_similarity(message, summary)
    save_memory(summary, similarity)

    return answer