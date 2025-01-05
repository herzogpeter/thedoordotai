import logging
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for chat engine and index
chat_engine = None

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[list] = None

class ChatResponse(BaseModel):
    response: str

@app.on_event("startup")
async def startup_event():
    """Initialize the chat engine on startup."""
    global chat_engine

    try:
        # Check for storage directory
        if not os.path.exists("storage"):
            logger.error("No storage directory found. Please run build_index.py first.")
            return

        # Initialize embedding model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Load pre-built index
        logger.info("Loading pre-built index...")
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = VectorStoreIndex(
            [],  # Empty documents list since we're loading from storage
            storage_context=storage_context,
        )
        logger.info("Index loaded successfully")

        # Initialize chat engine with Anthropic
        logger.info("Initializing chat engine...")
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            llm=Anthropic(model="claude-2"),
            verbose=True,
        )
        logger.info("Chat engine initialized successfully")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests."""
    if not chat_engine:
        raise HTTPException(
            status_code=503,
            detail="Chat engine not initialized. Please check server logs."
        )

    try:
        # Get response from chat engine
        response = chat_engine.chat(request.message)
        return ChatResponse(response=str(response))

    except Exception as e:
        logger.error(f"Error during chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not chat_engine:
        raise HTTPException(
            status_code=503,
            detail="Chat engine not initialized"
        )
    return {"status": "healthy"}
