from pydantic import BaseModel
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

# Local imports
from config.dependencies import templates
from services.chat import chat


router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

# Endpoint: Chat page
@router.get("", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )

# Endpoint
@router.post("")
async def do_chat(req: ChatRequest):
    answer = await chat(
        message=req.message,
        history=req.history
    )
    return JSONResponse({"answer": answer})