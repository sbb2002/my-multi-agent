from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

# Local imports
from config.dependencies import templates
from services.agents import run_ensemble

router = APIRouter(prefix="/ensemble", tags=["ensemble"])

# Endpoint: Ensemble
@router.post("", response_class=HTMLResponse)
async def do_ensemble(request: Request, message: str=Form(...)):
    result = await run_ensemble(message)
    
    name = "partials/ensemble_result.html"
    context = {
        "request": request,
        "agents": result["agents"],
        "summary": result["summary"]
    }
    return templates.TemplateResponse(
        name=name,
        context=context
    )