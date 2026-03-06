from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime

from agents import run_ensemble, run_pipeline
from memory import forget_old_memories
from memory import collection

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    forget_old_memories()  # 서버 시작 시 오래된 기억 정리
    yield

def dt_reformat(dt):
    return datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M')

app = FastAPI(title="Multi-Agent Demo", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
templates.env.filters['dt_reformat'] = dt_reformat

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── 앙상블 엔드포인트 ────────────────────────────────────────────────────────
# HTMX가 POST 후 HTML partial을 받아 #ensemble-result에 삽입
@app.post("/ensemble", response_class=HTMLResponse)
async def ensemble(request: Request, topic: str = Form(...)):
    result = await run_ensemble(topic)
    return templates.TemplateResponse(
        "partials/ensemble_result.html",
        {
            "request": request,
            "agents": result["agents"],
            "summary": result["summary"],
        },
    )


# ─── 파이프라인 엔드포인트 ────────────────────────────────────────────────────
# SSE(Server-Sent Events)로 단계별 결과를 실시간 스트리밍
@app.post("/pipeline/stream")
async def pipeline_stream(topic: str = Form(...)):
    return StreamingResponse(
        run_pipeline(topic),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── 메모리 모니터링 ────────────────────────────────────────────────────
@app.get("/memories", response_class=HTMLResponse)
async def view_memories(request: Request):
    all_memories = collection.get()
    memories = [
        {"doc": doc, "meta": meta}
        for doc, meta in zip(all_memories["documents"], all_memories["metadatas"])
    ]
    return templates.TemplateResponse("memories.html", {
        "request": request,
        "memories": memories
    })

@app.get("/memories/clear")
async def clear_memories():
    all_ids = collection.get()["ids"]
    if all_ids:
        collection.delete(ids=all_ids)
    return RedirectResponse(url="/memories")