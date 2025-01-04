from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
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
        force_rebuild = os.getenv("FORCE_INDEX_REBUILD", "").lower() == "true"

        if os.path.exists(index_path) and not force_rebuild:
            logger.info(f"Loading pre-built index from {index_path}...")
            try:
                index = VectorStoreIndex.load_from_disk(index_path)
                logger.info("Successfully loaded pre-built index")
                return
            except Exception as e:
                logger.error(f"Error loading pre-built index: {str(e)}")
                logger.info("Falling back to building index...")

        # Fallback: Build index if pre-built index not found or force rebuild
        if os.path.exists("transcripts") and any(os.scandir("transcripts")):
            logger.info("Building index from transcripts...")
            documents = SimpleDirectoryReader("transcripts").load_data()
            logger.info(f"Loaded {len(documents)} documents")
            storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            logger.info("Successfully built index")

            # Save the newly built index if we're in development
            if force_rebuild:
                logger.info(f"Saving newly built index to {index_path}...")
                index.storage_context.persist(persist_dir=index_path)
                logger.info("Index saved successfully")
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
        query_engine = index.as_query_engine(
            response_mode="tree_summarize",
            retrieve_source_nodes=True,
            similarity_top_k=3  # Retrieve more source nodes for better context
        )
        response = query_engine.query(message.message)
        logger.info("Successfully generated response")
        
        # Format response with source information
        sources = []
        for node in response.source_nodes:
            sources.append({
                "text": node.node.text,  # Changed from node.source_text to node.node.text
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
