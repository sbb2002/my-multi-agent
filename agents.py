import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일을 환경변수로 로드

# ─── 클라이언트 설정 ──────────────────────────────────────────────────────────
# Gemini — 무료 티어 제공, aistudio.google.com/apikey에서 발급
import google.genai as genai
from google.genai import types
from memory import save_memory, recall_memory

# ─── 단일 에이전트 호출 ───────────────────────────────────────────────────────
# [Gemini 버전]
# Call client
client = genai.Client()

async def call_agent(system: str, message: str, topic: str = None) -> str:
    """단일 Gemini 에이전트 호출"""

    # Memory calling
    memories = recall_memory(client, message, topic=topic) if topic else []
    if memories:
        # print(f"Memory: \n{memories}")
        memory_context = "\n".join(f"- {m}" for m in memories)
        system = f"{system}\n\n[관련 기억]\n{memory_context}"

    # Tools & configs
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[grounding_tool]
    )

    # Response
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=message,
        config=config
    )

    result = response.text

    # Save memories
    # if topic:
        # save_memory(client, result[:500], topic=topic, importance=0.8)

    # i) Summarize first
    system_mem = """[요청]\n
        질문과 답변에 대하여 아래 규칙으로 요약하십시오.
        - 질문과 답변을 종합하여 [요약]을 1문장으로 기술하시오.
        - 질문과 답변 속 핵심적인 키워드는 [요약]에 항상 사용하여야 합니다.
        - 최대 300자 이내로 기술하시오.
        - 아래 양식대로 작성하되, 이외의 말은 하지 마시오.
            [주제] (키워드, 주제, 단어, 여러개, 가능, 중요도, 높은 순으로)
            [요약] (질문과 답변을 요약한 300자 이내의 글)

    """

    config_mem = types.GenerateContentConfig(
        system_instruction=system_mem,
        tools=[grounding_tool]
    )

    message_mem = f"""\n\n
    [질문] {message} \n\n
    [답변] {result} \n\n
    """

    response_mem = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=message_mem,
        config=config_mem
    )

    result_mem = response_mem.text

    # print("Memorized info: ", response_mem)

    # ii) Embedding & Save memory
    save_memory(client, result_mem, topic)


    return result


# ─── 앙상블 패턴 ─────────────────────────────────────────────────────────────
# 여러 에이전트를 asyncio.gather로 동시에 실행 후 종합
async def run_ensemble(topic: str) -> dict:
    agents = [
        {
            "name": "분석가",
            "system": """
                당신은 냉정하고 객관적인 분석가입니다. 아래 규칙에 따라 분석하여 답변하세요.
                - 데이터와 통계적인 수치에 기반하여 주제를 분석하시오.
                - 핵심 요소, 트렌드, 맥락을 중심으로 기술하시오.
                - 공신력이 있는 뉴스 기사나 논문에서만 그 내용을 참고하십시오.
                - 최소 3~4 마디의 문장 또는 불렛을 이용하여 요약문으로 정리할 수 있습니다.
            """,
        },
        {
            "name": "비평가",
            "system": """
                당신은 냉철한 비평가입니다. 아래 규칙에 따라 답변하세요.
                - 주어진 주제에 대해 문제점, 한계점, 위험 요소, 간과하기 쉬운 부정적 측면을 위주로 서술하시오.
                - 최종적으로는 이러한 단점을 극복하기 위하여 부정적 측면을 어떻게 극복할지 서술하시오.
                - 최소 3~4 마디의 문장 또는 불렛을 이용하여 요약문으로 정리할 수 있습니다.
            """,
        },
        {
            "name": "낙관론자",
            "system": """
                당신은 긍정적인 낙관론자입니다. 아래 규칙에 따라 답변하세요.
                - 주어진 주제에 대해 긍정적인 부분, 기대할 수 있는 잠재력 및 다른 것과의 시너지 효과 위주로 서술하시오.
                - 긍정적인 면을 극대화할 수 있는 방안 및 시너지를 위한 조건 등을 함께 서술하시오.
                - 최소 3~4 마디의 문장 또는 불렛을 이용하여 요약문으로 정리할 수 있습니다.
                """
            ,
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

    sys_msg = """
    당신은 여러 관점을 통합하는 종합 에이전트입니다. 아래 규칙에 따라 서술하세요.
    - 분석가, 비평가, 낙관론자의 의견을 균형 있게 종합하여 가장 통찰력 있는 최종 답변을 작성하시오.
    - 분석가, 비평가, 낙관론자의 의견을 인용할 때는 불렛 형식으로 요약하여 인용할 것.
    - 실현 가능성을 바탕으로 당신의 의견을 서술할 것.
    - 두괄식으로 서술할 것.
    - 최대 500자 이내로 서술할 것.
    - 나타내고자 하는 의견을 첫 문단에서 분명히 밝힐 것.
    - 의견을 달성하기 위한 실행 전략도 함께 서술할 것.
    - 만약 500자를 넘어설 경우 요약문도 함께 제공할 것.
    """
    summary = await call_agent(
        sys_msg,
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
                - 이전 기억을 활용할 수도 있음
            """,
        },
        {
            "name": "작성",
            "system": """
                당신은 숙련된 칼럼니스트입니다. 아래 규칙에 맞추어 작업하십시오.
                - 기획된 제목에 따라 알맞은 내용을 작성할 것
                - 각 부분마다 최소 300자 이상 작성할 것
                - 필요에 따라 검색을 통해 정보를 습득하여 이를 바탕으로 적을 것
                - 검색을 이용할 경우 참고한 경로의 레퍼런스의 url을 가장 아래에 반드시 기재할 것     
            """,
        },
        {
            "name": "비평",
            "system": """
                당신은 엄격한 비평가입니다. 아래 규칙에 맞추어 작성합시오.
                - 작성된 글의 구조, 문맥, 독자의 관점에서 읽기 좋은 글인지 판단할 것
                - 판단을 근거로 초고를 개선할 수 있는 부분을 최소 3가지 이상 지적할 것
                - 레퍼런스를 비평할 때 공신력이 있는 곳인지 반드시 확인할 것
                - 정확한 정보를 바탕으로 비평해야하므로 인터넷을 통해 검색하여 비평할 것
                - 커뮤니티에서의 의견은 공신력이 떨어질 수 있으므로 이를 인용할 경우 항상 주의할 것
                - 레퍼런스의 url이 없는 경우 반드시 이를 지적하고 가장 아래에 넣도록 지적할 것
                - 중복되는 내용이나 중복되는 정보를 담고 있는 레퍼런스는 중복되지 않도록 지적할 것
                - 작성 단계의 글이 만약 가상의 내용이라고 간주된다면 다시 인터넷 검색을 확인하여 진위여부를 파악할 것
                - 만약 가상이 아니라고 판단될 경우 가상의 내용이라고 언급해선 안됨
            """,
        },
        {
            "name": "최종화",
            "system": """
                당신은 시니어 에디터입니다. 초안과 비평을 바탕으로 완성도 높은 최종 블로그 포스트를 작성하세요. 아래 규칙에 맞추어 작성하십시오.
                - 작성 단계에서 완성된 글을 비평 단계의 내용을 수용하여 글을 편집할 것
                - 비평 단계에서 지적한 내용이 작성 단계의 글의 주제가 일치하지 않을 경우 해당하는 일부 비평을 무시할 수 있음
                - 비평가의 말을 무조건 수용할 필요는 없음
                - 독자가 이해하기 쉽도록 명확하고 간결하게 작성할 것
                - SEO를 고려하여 핵심 키워드를 적절히 포함할 것
                - 레퍼런스를 절대 생략하지 말 것
                - 레퍼런스 url이 인용한 내용이 있는 웹페이지로 정확히 접속하는지 반드시 검증할 것
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
