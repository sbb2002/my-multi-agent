from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from agents import run_ensemble, run_pipeline
from memory import forget_old_memories

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    forget_old_memories()  # 서버 시작 시 오래된 기억 정리
    yield


app = FastAPI(title="Multi-Agent Demo", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


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
