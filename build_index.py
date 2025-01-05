import logging
import sys
import os
import nltk
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Download required NLTK data
nltk.download('punkt', quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_index():
    """Build and persist the vector index from transcripts."""
    try:
        # Check for transcripts
        if not os.path.exists("transcripts") or not os.listdir("transcripts"):
            logger.error("No transcripts found in transcripts/ directory")
            sys.exit(1)

        # Initialize embedding model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Load documents
        logger.info("Loading transcripts...")
        documents = SimpleDirectoryReader("transcripts").load_data()
        logger.info(f"Loaded {len(documents)} documents")

        # Create and persist index
        logger.info("Creating index...")
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
        )

        # Save to disk
        persist_dir = "storage"
        os.makedirs(persist_dir, exist_ok=True)
        index.storage_context.persist(persist_dir)
        logger.info(f"Index built and saved to '{persist_dir}/'")

        # Verify index files exist
        expected_files = ["docstore.json", "default__vector_store.json", "index_store.json"]
        missing_files = [f for f in expected_files if not os.path.exists(f"{persist_dir}/{f}")]
        if missing_files:
            logger.error(f"Missing expected index files: {missing_files}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error building index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    build_index() 