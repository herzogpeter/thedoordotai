from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Settings, load_index_from_storage
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info(f"Starting application on port {os.getenv('PORT', '10000')}")

# Initialize settings
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.embed_model = embed_model
Settings.llm = Anthropic(model="claude-3-5-sonnet-20241022")

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
    """Initialize the index on startup"""
    global index
    try:
        logger.info("Starting initialization...")
        index_path = os.getenv("INDEX_PATH", "index.json")

        if os.path.exists(index_path):
            logger.info(f"Loading pre-built index from {index_path}...")
            try:
                # Load the storage context with the pre-built embeddings
                storage_context = StorageContext.from_defaults(persist_dir=index_path)
                index = load_index_from_storage(storage_context)
                logger.info("Successfully loaded pre-built index")
                return
            except Exception as e:
                logger.error(f"Error loading pre-built index: {str(e)}")
                raise  # Re-raise the exception as this is critical

        else:
            logger.error(f"No index found at {index_path}")
            raise FileNotFoundError(f"Index not found at {index_path}")

    except Exception as e:
        logger.error(f"Error initializing index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise  # Re-raise to prevent the application from starting without an index

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
        logger.error("No index loaded")
        raise HTTPException(status_code=500, detail="Index not loaded")
    
    try:
        logger.info(f"Processing chat message: {message.message[:50]}...")
        query_engine = index.as_query_engine(
            response_mode="tree_summarize",
            retrieve_source_nodes=True,
            similarity_top_k=3
        )
        response = query_engine.query(message.message)
        logger.info("Successfully generated response")
        
        # Format response with source information
        sources = []
        for node in response.source_nodes:
            sources.append({
                "text": node.node.text,
                "score": float(node.score),
                "metadata": node.node.metadata
            })
        
        return {
            "response": str(response),
            "sources": sorted(sources, key=lambda x: x["score"], reverse=True)
        }
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
