from google.genai import types
from services.core.loader import load_role

from services.core.client import gemini_client
from services.core.client import collection


############################## Gemini API Requests ##############################

# Embedding
def request_embedding(contents: str) -> list[float]:
    """텍스트 -> 임베딩 벡터 변환"""
    model = "gemini-embedding-001"
    emb_vector = gemini_client.models.embed_content(
        model=model,
        contents=str(contents)
    )
    return emb_vector.embeddings[0].values

# LLM Answering
async def request_answering(system:str, question: str) -> str:
    """LLM에게 질문을 주고 답변을 요청하는 메서드."""

    # Tools & configs
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[grounding_tool]
    )

    # Response
    response = await gemini_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=question,
        config=config
    )

    return response.text

# LLM Summarization
async def request_summarization(question: str, answer: str):
    path_summarizer = 'summarizer.yaml'
    agent_summarizer = load_role(path_summarizer)
    system_summarizer = agent_summarizer['system']

    config_summarizer = types.GenerateContentConfig(
        system_instruction=system_summarizer
    )

    contents_summarizer = f"""
    [질문] {question} \n\n
    [답변] {answer} \n\n
    """

    response_summarizer = await gemini_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_summarizer,
        config=config_summarizer
    )

    summary = response_summarizer.text
    return summary


############################## DB Requests ##############################

# Query to DB
def query_to_db(embedding: list, top_k: int=3):
    """DB에 검색을 위해 query를 날리는 메서드."""
    if int(collection.count()) < top_k:
        return None
    memory = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )
    return memory

# Add data into DB
def add_to_db(
        id: str,
        embedding: list,
        document: str,
        metadata: dict
    ):
    """DB에 데이터를 추가하는 메서드."""
    collection.add(
        ids=[id],
        embeddings=[embedding],
        documents=document,
        metadatas=[metadata]
    )

# Update data's info
def update_info(id: str, metadata: dict):
    collection.update(
        ids=[id],
        metadatas=[metadata]
    )