import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일을 환경변수로 로드

# ─── 클라이언트 설정 ──────────────────────────────────────────────────────────
# Anthropic (Claude) — 크레딧 필요, console.anthropic.com에서 충전
# from anthropic import AsyncAnthropic
# claude_client = AsyncAnthropic()  # 환경변수: ANTHROPIC_API_KEY

# Gemini — 무료 티어 제공, aistudio.google.com/apikey에서 발급
import google.genai as genai
from google.genai import types
from memory import save_memory, recall_memory

# genai.configure(api_key=os.environ["GEMINI_API_KEY"])


# ─── 단일 에이전트 호출 ───────────────────────────────────────────────────────

# [Claude 버전]
# async def call_agent(system: str, message: str) -> str:
#     """단일 Claude 에이전트 호출"""
#     response = await claude_client.messages.create(
#         model="claude-sonnet-4-6",
#         max_tokens=1024,
#         system=system,
#         messages=[{"role": "user", "content": message}],
#     )
#     return response.content[0].text

# [Gemini 버전]
async def call_agent(system: str, message: str, topic: str = None) -> str:
    """단일 Gemini 에이전트 호출"""

    # Call client
    client = genai.Client()

    # Memory calling
    memories = recall_memory(client, message, topic=topic) if topic else []
    if memories:
        memory_context = "\n".join(f"- {m}" for m in memories)
        system = f"{system}\n\n[관련 기억]\n{memory_context}\n(참고만 하되, 현재 주제와 무관하다면 무시하세요.)"

    # Tools & configs
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[grounding_tool]
    )

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=message,
        config=config
    )

    result = response.text

    # Save memories
    if topic:
        save_memory(client, result[:500], topic=topic, importance=0.8)

    return result


# ─── 앙상블 패턴 ─────────────────────────────────────────────────────────────
# 여러 에이전트를 asyncio.gather로 동시에 실행 후 종합
async def run_ensemble(topic: str) -> dict:
    agents = [
        {
            "name": "분석가",
            "system": "당신은 냉정하고 객관적인 분석가입니다. 데이터와 사실에 기반하여 주어진 주제를 분석하세요. 핵심 요소, 트렌드, 맥락을 중심으로 3~4문장으로 분석해주세요.",
        },
        {
            "name": "비평가",
            "system": "당신은 날카로운 비평가입니다. 주어진 주제의 문제점, 위험 요소, 간과되기 쉬운 부정적 측면을 지적하세요. 균형 잡힌 시각을 위해 3~4문장으로 비평해주세요.",
        },
        {
            "name": "낙관론자",
            "system": "당신은 열정적인 낙관론자입니다. 주어진 주제에서 기회, 가능성, 긍정적 변화를 발견하세요. 희망적이고 건설적인 관점에서 3~4문장으로 서술해주세요.",
        },
    ]

    # 핵심: 3개 에이전트를 동시에 실행
    results = await asyncio.gather(*[
        call_agent(agent["system"], f"주제: {topic}", topic) for agent in agents
    ])

    # 종합 에이전트가 세 결과를 통합
    context = "\n\n".join(
        f"[{agents[i]['name']}]\n{result}" for i, result in enumerate(results)
    )
    summary = await call_agent(
        "당신은 여러 관점을 통합하는 종합 에이전트입니다. 분석가, 비평가, 낙관론자의 의견을 균형 있게 종합하여 가장 통찰력 있는 최종 답변을 작성하세요.",
        context,
        topic
    )

    return {
        "agents": [
            {"name": agents[i]["name"], "result": result}
            for i, result in enumerate(results)
        ],
        "summary": summary,
    }


# ─── 파이프라인 패턴 ──────────────────────────────────────────────────────────
# 각 단계의 출력이 다음 단계의 입력으로 연결되는 순차 처리
# AsyncGenerator로 SSE 스트리밍 — 단계 완료시마다 프론트에 즉시 전송
async def run_pipeline(topic: str) -> AsyncGenerator[str, None]:
    steps = [
        {
            "name": "기획",
            "system": """
                당신은 창의로운 기획자입니다. 아래 규칙에 맞추어 작업을 하십시오.
                - 검색을 통해 토픽에 관한 정보를 습득할 것
                - 습득한 정보를 바탕으로 적절한 서론, 본론, 결론의 제목을 작성할 것
                - 필요에 따라 소제목을 사용할 수 있음
            """,
        },
        {
            "name": "작성",
            "system": """
                당신은 숙련된 칼럼니스트입니다. 아래 규칙에 맞추어 작업하십시오.
                - 기획된 제목에 따라 알맞은 내용을 작성할 것
                - 각 부분마다 최소 300자 이상 작성할 것
                - 필요에 따라 검색을 통해 정보를 습득하여 이를 바탕으로 적을 것
                - 검색을 이용할 경우 참고한 경로의 레퍼런스 url을 가장 아래에 기재할 것     
            """,
        },
        {
            "name": "비평",
            "system": """
                당신은 엄격한 비평가입니다. 아래 규칙에 맞추어 작성합시오.
                - 작성된 글의 구조, 문맥, 독자의 관점에서 읽기 좋은 글인지 판단할 것
                - 판단을 근거로 초고를 개선할 수 있는 부분을 최소 3가지 이상 지적할 것
            """,
        },
        {
            "name": "최종화",
            "system": """
                당신은 시니어 에디터입니다. 초안과 비평을 바탕으로 완성도 높은 최종 블로그 포스트를 작성하세요. 아래 규칙에 맞추어 작성하십시오.
                - 기획, 작성, 비평 단계의 내용을 모두 반영할 것
                - 독자가 이해하기 쉽도록 명확하고 간결하게 작성할 것
                - SEO를 고려하여 핵심 키워드를 적절히 포함할 것
                - 레퍼런스를 절대 생략하지 말 것
            """,
        },
    ]

    context = f"주제: {topic}"

    for n, step in enumerate(steps):
        if n == 0:
            message = context
        else:
            message = f"{context}\n\n---\n지금 당신이 해야 할 작업: {step['name']}\n위 내용을 바탕으로 지금 즉시 작성을 시작하세요."
        result = await call_agent(step["system"], message, topic)
        safe_result = result.replace('\n', "↵")
        # SSE 형식으로 yield (프론트가 data: 파싱)
        yield f"data: {step['name']}||{safe_result}\n\n"
        # 다음 단계를 위해 컨텍스트에 누적
        context += f"\n\n[{step['name']} 결과]\n{result}"
        
        # print(n, context)
