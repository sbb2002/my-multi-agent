# General imports
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv

# API imports
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Source imports
from routers import ens_router, pip_router, mem_router
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
    return templates.TemplateResponse("index.html", {"request": request})

# Register the routers
app.include_router(ens_router)
app.include_router(pip_router)
app.include_router(mem_router)