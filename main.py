from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info(f"Starting application on port {os.getenv('PORT', '10000')}")

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Initialize settings
Settings.llm = anthropic_client
Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable for the index
index = None

class ChatMessage(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize the index on startup if transcripts are available"""
    global index
    try:
        logger.info("Starting initialization...")
        if os.path.exists("transcripts") and any(os.scandir("transcripts")):
            logger.info("Loading transcripts...")
            documents = SimpleDirectoryReader("transcripts").load_data()
            logger.info(f"Loaded {len(documents)} documents")
            logger.info("Creating index...")
            storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            logger.info("Successfully loaded and indexed transcripts")
        else:
            logger.warning("No transcripts found in /transcripts directory")
    except Exception as e:
        logger.error(f"Error initializing index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Transcript Chat API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {"status": "healthy", "index_loaded": index is not None}

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat with the loaded transcripts"""
    global index
    
    if not index:
        logger.error("No transcripts loaded")
        raise HTTPException(status_code=400, detail="No transcripts loaded")
    
    try:
        logger.info(f"Processing chat message: {message.message[:50]}...")
        query_engine = index.as_query_engine()
        response = query_engine.query(message.message)
        logger.info("Successfully generated response")
        return {"response": str(response)}
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
