import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_and_save_index(transcripts_dir: str = "transcripts", output_path: str = "index.json"):
    """Build the index and save it to a file"""
    try:
        logger.info("Starting index build process...")
        
        # Initialize settings
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        Settings.embed_model = embed_model
        Settings.llm = Anthropic(model="claude-3-5-sonnet-20241022")
        
        # Verify transcripts directory exists and has files
        if not os.path.exists(transcripts_dir):
            raise FileNotFoundError(f"Directory not found: {transcripts_dir}")
        
        if not any(os.scandir(transcripts_dir)):
            raise ValueError(f"No files found in {transcripts_dir}")
        
        # Load documents
        logger.info("Loading transcripts...")
        documents = SimpleDirectoryReader(transcripts_dir).load_data()
        logger.info(f"Loaded {len(documents)} documents")
        
        # Create and save index
        logger.info("Creating index...")
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        # Save index
        logger.info(f"Saving index to {output_path}...")
        index.storage_context.persist(persist_dir=output_path)
        
        # Verify index was saved
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Failed to save index to {output_path}")
        
        index_size = sum(f.stat().st_size for f in Path(output_path).rglob('*') if f.is_file())
        logger.info(f"Index saved successfully. Size: {index_size / 1024 / 1024:.2f} MB")
        
        # Test load index without regenerating embeddings
        logger.info("Testing index load...")
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore(), persist_dir=output_path)
        test_load = VectorStoreIndex.init_from_vector_store(
            vector_store=storage_context.vector_store,
            embed_model=embed_model
        )
        logger.info("Index load test successful")
        
        return True
        
    except Exception as e:
        logger.error(f"Error building index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    load_dotenv()
    build_and_save_index() 