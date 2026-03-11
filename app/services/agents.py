import asyncio
from typing import AsyncGenerator

from services.request import (
    request_answering,
    request_summarization
    )
from services.metric import get_similarity
from services.memory import save_memory, remember_memory, process_memory_system_msg
from services.core.loader import load_role


# Basic API calling
async def call_agent(system: str, message: str) -> str:
    """단일 Gemini 에이전트 호출"""

    # 질문에 대해 기억이 있는지 확인
    memory = remember_memory(message)
    system = process_memory_system_msg(system, memory)

    # 질문에 대한 답변
    answer = await request_answering(system=system, question=message)

    # 답변에 대한 요약
    summary = await request_summarization(question=message, answer=answer)

    # 요약에 대해 중요도 평가
    similarity = get_similarity(message, summary)

    # TODO: 요약의 중요도에 따라 기억하기
    # 지금은 similarity -> importance라고 간주하여 기억하기.
    save_memory(summary, similarity)

    return answer


# Ensemble pattern -- using call_agent()
async def run_ensemble(message: str) -> dict:
    # 핵심: 3개 에이전트를 동시에 실행
    path_analyzer = 'ens_analyzer.yaml'
    path_critic = 'ens_critic.yaml'
    path_optimist = 'ens_optimist.yaml'

    agent_analyzer = load_role(path_analyzer)
    agent_critic = load_role(path_critic)
    agent_optimist = load_role(path_optimist)

    agents = [
        agent_analyzer,
        agent_critic,
        agent_optimist
    ]

    results = await asyncio.gather(*[
        call_agent(agent["system"], f"\n\n{message}")
        for agent in agents
    ])

    # 종합 에이전트가 세 결과를 통합
    context = "\n\n".join(
        f"[{agents[i]['name']}]\n{result}" 
        for i, result in enumerate(results)
    )

    path_editor = 'ens_editor.yaml'
    agent_editor = load_role(path_editor)

    summary = await call_agent(
        agent_editor['system'],
        context
    )

    return {
        "agents": [
            {"name": agents[i]["name"], "result": result}
            for i, result in enumerate(results)
        ],
        "summary": summary,
    }


# Ensemble pattern -- using call_agent()
async def run_pipeline(message: str) -> AsyncGenerator[str, None]:

    # 4개 agent의 역할 불러오기
    path_planner = 'pip_planner.yaml'
    path_writer = 'pip_writer.yaml'
    path_critic = 'pip_critic.yaml'
    path_editor = 'pip_editor.yaml'

    agent_planner = load_role(path_planner)
    agent_writer = load_role(path_writer)
    agent_critic = load_role(path_critic)
    agent_editor = load_role(path_editor)

    agents = [
        agent_planner,
        agent_writer,
        agent_critic,
        agent_editor
    ]

    context = f"[요청] {message}"

    for n, agent in enumerate(agents):
        context = f"{context}\n\n[역할] {agent['name']}"
        article = await call_agent(agent['system'], context)
        article_for_frontend = article.replace('\n', "↵")
        yield f"data: {agent['name']}||{article_for_frontend}\n\n"

        context += f"\n\n[{agent['name']} 결과\n{article}"