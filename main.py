from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import logging
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info(f"Starting application on port {os.getenv('PORT', '10000')}")

# Initialize settings
Settings.llm = Anthropic(model="claude-3-5-sonnet-20241022")
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
index = None
chat_engine = None
is_initializing = False

class Message(BaseModel):
    role: str
    content: str

class ChatMessage(BaseModel):
    message: str
    history: List[Message] = []

@app.on_event("startup")
async def startup_event():
    """Initialize the index and chat engine on startup if transcripts are available"""
    global index, chat_engine, is_initializing
    try:
        logger.info("Starting initialization...")
        is_initializing = True
        if os.path.exists("transcripts") and any(os.scandir("transcripts")):
            logger.info("Loading transcripts...")
            documents = SimpleDirectoryReader("transcripts").load_data()
            logger.info(f"Loaded {len(documents)} documents")
            logger.info("Creating index...")
            storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            
            # Initialize chat engine with memory
            memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
            chat_engine = index.as_chat_engine(
                chat_mode="context",
                memory=memory,
                similarity_top_k=3,
                system_prompt=(
                    "You are a helpful AI assistant that answers questions about sermon transcripts. "
                    "Use the provided context to answer questions accurately and concisely. "
                    "If you're not sure about something, say so."
                )
            )
            logger.info("Successfully loaded and indexed transcripts")
        else:
            logger.warning("No transcripts found in /transcripts directory")
        is_initializing = False
    except Exception as e:
        logger.error(f"Error initializing index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        is_initializing = False

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Transcript Chat API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    # Always return 200 OK, but with different status messages
    if is_initializing:
        return {"status": "ok", "state": "initializing", "message": "Loading and indexing transcripts"}
    elif chat_engine is not None:
        return {"status": "ok", "state": "ready", "index_loaded": True}
    else:
        return {"status": "ok", "state": "waiting", "message": "Waiting to start initialization"}

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat with the loaded transcripts"""
    global chat_engine
    
    if not chat_engine:
        logger.error("No transcripts loaded")
        raise HTTPException(status_code=400, detail="No transcripts loaded")
    
    try:
        logger.info(f"Processing chat message: {message.message[:50]}...")
        
        # Reset chat engine memory with conversation history
        chat_engine.reset()
        for msg in message.history[:-1]:  # Exclude the latest message as we'll send it separately
            if msg.role == "user":
                chat_engine.chat(msg.content)
        
        # Get response for the current message
        response = chat_engine.chat(message.message)
        logger.info("Successfully generated response")
        
        # Format response with source information
        sources = []
        if hasattr(response, 'source_nodes'):
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
