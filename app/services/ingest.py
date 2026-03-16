import re
import hashlib
import pymupdf4llm as pml
from pathlib import Path
from tqdm import tqdm

# Local imports
from services.core.client import rag_collection
from services.request import request_embedding


# Path docs_db
DOCS_DIR = Path(__file__).parents[2] / 'docs_db'

def parse_chunks(text: str, source: str) -> list[dict]:
    """소제목 단위로 청킹하는 메서드"""
    
    # Split by pattern of title
    title_pattern = r'\d+.\d+\s.*\n'
    comp = re.compile(title_pattern)
    parts = comp.split(text)

    chunks = []
    for i in range(1, len(parts)-1, 2):
        title = parts[i].strip()
        content = parts[i+1].strip()
        if not content:
            continue

        chunks.append({
            "title": title,
            "content": f"{title}\n{content}",
            "source": source,
        })

    return chunks

def ingest_file(filepath: Path):
    """PDF 1개를 읽어 markdown 양식으로 바꾼 후 rag_collection에 저장하는 메서드."""
    
    # Convert PDF into MD
    text = pml.to_markdown(filepath)
    source = filepath.name
    chunks = parse_chunks(text, source)

    for chunk in chunks:
        
        doc_id = hashlib.md5(
            chunk['content'].encode()
        ).hexdigest()

        # If already exists in DB, skip
        existing = rag_collection.get(ids=[doc_id])
        if existing['ids']:
            print(f"[Skip] This chunk exists already. Title: {chunk['title']}")
            continue

        # Or not, add this chunk into DB
        embedding = request_embedding(chunk['content'])
        rag_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk['content']],
            metadatas=[{
                "title": chunk['title'],
                "source": chunk['source']
            }]
        )
        # print(f"[저장] {chunk['title']}")

def ingest_all():
    """docs_db/ 내 모든 pdf 파일을 ingestion하는 메서드."""
    filepaths = list(DOCS_DIR.glob("*.pdf"))
    if not filepaths:
        print(f"There is no file at `{DOCS_DIR}`.")
        return

    desc = "Ingesting..."
    for filepath in tqdm(filepaths, desc=desc):
        ingest_file(filepath)
    
    print(f"[인제스트] 완료")