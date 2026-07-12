from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.core.config import settings

def get_embedding_model():
    """Initializes and returns the FREE local HuggingFace Embedding model"""
    print(f"Loading local embedding model: {settings.EMBEDDING_MODEL}...")
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

def store_embeddings_in_chroma(chunks: list[dict], document_name: str, collection_name: str = "default_collection"):
    """
    Generates embeddings and stores chunks in ChromaDB.
    SRS FR-TP-003 & FR-TP-004
    """
    # Extract just the text for embedding
    texts = [chunk["text"] for chunk in chunks]
    
    # Extract metadata (SRS FR-TP-004 requires doc ID, chunk index, etc.)
    metadatas = [
        {
            "document_name": document_name,
            "chunk_index": chunk["chunk_index"]
        } 
        for chunk in chunks
    ]
    
    # Initialize embedding model
    embeddings = get_embedding_model()
    
    # Store in ChromaDB
    vector_db = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_name=collection_name
    )
    
    return vector_db