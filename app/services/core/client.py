import chromadb
from google import genai
from dotenv import load_dotenv


# Load confidential key
load_dotenv()

# Client defines
gemini_client = genai.Client()

# DB startup
db_client = chromadb.PersistentClient(path="./memory_db")
collection = db_client.get_or_create_collection(
    "agent_memory",
    metadata={"hnsw:space": "cosine"})