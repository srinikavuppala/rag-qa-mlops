from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.core.config import settings

def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[dict]:
    """
    Splits text into chunks based on SRS FR-TP-001 and FR-TP-002.
    Uses recursive splitting which best preserves semantic meaning.
    """
    size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""] # Tries paragraphs first, then lines, then words
    )
    
    chunks = text_splitter.split_text(text)
    
    # Format chunks to include metadata index (helps with citations later)
    chunk_data = [
        {"chunk_index": i, "text": chunk}
        for i, chunk in enumerate(chunks)
    ]
    
    return chunk_data