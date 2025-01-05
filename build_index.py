import logging
import sys
import os
import nltk
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tqdm import tqdm

# Download required NLTK data
nltk.download('punkt', quiet=True)

# Configure logging with a format that includes timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def count_files_and_size(directory):
    """Count number of files and total size to track progress."""
    total_files = 0
    total_size = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                total_files += 1
                total_size += os.path.getsize(os.path.join(root, file))
    return total_files, total_size

def build_index():
    """Build and persist the vector index from transcripts."""
    try:
        # Check for transcripts
        if not os.path.exists("transcripts") or not os.listdir("transcripts"):
            logger.error("No transcripts found in transcripts/ directory")
            sys.exit(1)

        # Count total files and size for progress tracking
        total_files, total_size = count_files_and_size("transcripts")
        logger.info(f"Found {total_files} transcript files to process")

        # Initialize embedding model
        logger.info("Initializing embedding model...")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("Embedding model initialized successfully")

        # Load documents with progress bar
        logger.info("Loading transcripts...")
        documents = []
        processed_size = 0
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Loading documents") as pbar:
            for root, _, files in os.walk("transcripts"):
                for file in sorted(files):
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
                        documents.extend(doc)
                        processed_size += file_size
                        pbar.update(file_size)
                        logger.info(f"Processed {file} ({len(documents)} documents so far)")

        logger.info(f"Successfully loaded {len(documents)} documents")

        # Create and persist index with progress logging
        logger.info("Creating index...")
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
        
        # Log start of indexing
        logger.info("Starting document indexing process...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True  # Enable built-in progress bar
        )

        # Save to disk
        persist_dir = "storage"
        os.makedirs(persist_dir, exist_ok=True)
        
        logger.info("Persisting index to disk...")
        index.storage_context.persist(persist_dir)
        logger.info(f"Index built and saved to '{persist_dir}/'")

        # Verify index files exist
        expected_files = ["docstore.json", "default__vector_store.json", "index_store.json"]
        missing_files = [f for f in expected_files if not os.path.exists(f"{persist_dir}/{f}")]
        if missing_files:
            logger.error(f"Missing expected index files: {missing_files}")
            sys.exit(1)
        
        logger.info("Index build completed successfully!")

    except Exception as e:
        logger.error(f"Error building index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    build_index() 