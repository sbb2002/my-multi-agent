from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# Local imports
from routers import (
    ens_router, pip_router, mem_router, ing_router, cha_router)
from config.dependencies import templates


# Lifecycle handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    # forget_old_memories()
    yield
    # Shutdown event

# App starts
app = FastAPI(title="Multi-Gemini-Demo", lifespane=lifespan)
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
        )

# Register the routers
app.include_router(ens_router)
app.include_router(pip_router)
app.include_router(mem_router)
app.include_router(ing_router)
app.include_router(cha_router)