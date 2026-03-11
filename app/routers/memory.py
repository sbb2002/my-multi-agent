# General imports
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Business imports
from services.memory import get_memory, delete_memory
from config.dependencies import templates


router = APIRouter(prefix="/memories", tags=["memory"])

# Endpoint: Memory monitoring
@router.get("", response_class=HTMLResponse)
async def view_memories(request: Request):
    memories = get_memory()
    context = {
        "request": request,
        "memories": memories
    }
    return templates.TemplateResponse(
        name="memories.html",
        context=context
        )

# Endpoint: Memory clear
@router.get("/clear")
async def clear_memories():
    delete_memory()
    return RedirectResponse(url="/")