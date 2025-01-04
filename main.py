from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Load environment variables
load_dotenv()

# Initialize settings
Settings.llm = Anthropic(model="claude-3-5-sonnet-20241022")
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
        if os.path.exists("transcripts") and any(os.scandir("transcripts")):
            print("Loading transcripts...")
            documents = SimpleDirectoryReader("transcripts").load_data()
            print("Creating index...")
            storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            print("Successfully loaded and indexed transcripts")
        else:
            print("No transcripts found in /transcripts directory")
    except Exception as e:
        print(f"Error initializing index: {str(e)}")
        import traceback
        print(traceback.format_exc())

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Transcript Chat API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "index_loaded": index is not None}

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat with the loaded transcripts"""
    global index
    
    if not index:
        raise HTTPException(
            status_code=400, 
            detail="No transcripts loaded. Please add transcript files to the /transcripts directory and restart the application."
        )
    
    try:
        query_engine = index.as_query_engine()
        response = query_engine.query(message.message)
        return {"response": str(response)}
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
