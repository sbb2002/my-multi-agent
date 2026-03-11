from fastapi import APIRouter, Form
from fastapi.responses import StreamingResponse

# Local imports
from services.agents import run_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Endpoint: Pipeline
@router.post("/stream")
async def do_pipeline_stream(message: str = Form(...)):
    return StreamingResponse(
        run_pipeline(message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )