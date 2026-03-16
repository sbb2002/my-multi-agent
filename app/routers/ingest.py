from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Local imports
from services.ingest import ingest_all
from services.core.client import rag_collection


router = APIRouter(prefix="/ingest", tags=["ingest"])


# Endpoint: Ingest the documents
# 1) http://localhost:8000/docs에서 실행
# 2) 터미널에서 `curl -X POST http://localhost:8000/ingest`
@router.post("")
async def do_ingest():
    ingest_all()
    return JSONResponse({
        "message": "ingestion 완료",
        "total_chunks": rag_collection.count()
        }
    )

# Endopoint: RAG Collection Status Check
@router.get("/status")
async def ingest_status():
    return JSONResponse({
        "total_chunks": rag_collection.count()
    })