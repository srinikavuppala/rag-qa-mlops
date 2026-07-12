import os
import ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.core.config import settings

def get_embedding_model():
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

def retrieve_context(query: str, collection_name: str = "ai_knowledge", top_k: int = 5):
    """
    SRS FR-QA-002 & FR-QA-003: Embeds query and retrieves top-k chunks
    """
    embeddings = get_embedding_model()
    vector_db = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    
    # Similarity search with score
    results = vector_db.similarity_search_with_score(query, k=top_k)
    
    # Format results
    context_chunks = []
    for doc, score in results:
        similarity = 1 - score 
        context_chunks.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
            "relevance_score": round(similarity * 100, 2)
        })
        
    return context_chunks

def generate_answer(query: str, context_chunks: list[dict]):
    """
    SRS FR-QA-004 & FR-QA-007: Generates answer using local Ollama LLM
    """
    # Build context string
    context_text = "\n\n".join([f"Chunk {i+1}:\n{c['text']}" for i, c in enumerate(context_chunks)])
    
    # SRS FR-QA-007: Strict prompt to prevent hallucination
    prompt = f"""
    You are a helpful assistant. Answer the question based ONLY on the provided context.
    If the context does not contain the answer, you MUST respond exactly with: 
    "I don't have enough information in the documents to answer this question."
    
    Context:
    {context_text}
    
    Question: {query}
    
    Answer:
    """
    
     # Call Ollama directly (Uses host.docker.internal if in Docker, else localhost)
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama.Client(host=ollama_host)
    response = client.chat(model='gemma2:2b', messages=[{'role': 'user', 'content': prompt}])
    
    return response['message']['content']

def run_rag_pipeline(query: str, collection_name: str = "ai_knowledge"):
    """Main function to run the complete RAG pipeline"""
    # 1. Retrieve
    context = retrieve_context(query, collection_name)
    
    if not context:
        return {
            "answer": "I don't have enough information in the documents to answer this question.",
            "citations": []
        }
        
    # 2. Generate
    answer = generate_answer(query, context)
    
    # 3. Format Citations (SRS FR-QA-005)
    citations = [
        {
            "document_name": c["metadata"]["document_name"],
            "chunk_index": c["metadata"]["chunk_index"],
            "relevance_score": c["relevance_score"]
        }
        for c in context
    ]
    
    return {
        "answer": answer.strip(),
        "citations": citations
    }