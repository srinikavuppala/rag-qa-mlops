🤖 RAG-Based Document Q&A System with MLOps Pipeline
A production-grade, fully containerized Retrieval-Augmented Generation (RAG) system that allows users to upload documents (PDF, TXT, DOCX) and chat with them using a local, privacy-first AI.

Built following IEEE 830 SRS standards.

✨ Key Features
Dynamic Document Ingestion: Upload and parse PDF, DOCX, TXT, and Markdown files.
Semantic Search: Converts text to vector embeddings and retrieves context using Cosine Similarity.
Zero-Hallucination AI: Strict prompting ensures the LLM only answers based on provided documents.
100% Local & Private: Uses local HuggingFace embeddings and Ollama LLM (gemma2:2b). No data sent to external APIs.
Enterprise Security: JWT Authentication, Bcrypt password hashing, and protected API endpoints.
Modern UI: Interactive chat interface built with Streamlit, complete with citation tracking and relevance scores.
Dockerized: Fully containerized microservices architecture (FastAPI Backend + Streamlit Frontend).

🏗️ System Architecture

Frontend: Streamlit (Port 8501)
Backend: FastAPI with auto-generated Swagger docs (Port 8000)
Vector Database: ChromaDB
Relational DB: SQLite (Easily upgradable to PostgreSQL)
AI Engine: Ollama (gemma2:2b) running on the host machine
Embeddings: HuggingFace all-MiniLM-L6-v2

🐳 Quick Start (Docker)

Prerequisites:

Install Docker Desktop.
Install Ollama and pull the model: ollama run gemma2:2b

Run the application:

# Clone the repositorygit clone https://github.com/yourusername/rag-qa-mlops.gitcd rag-qa-mlops# Start the containersdocker-compose up --build
Access the application at http://localhost:8501. Register a new user and start chatting with your documents!

🛠️ Tech Stack
Python
FastAPI
LangChain
ChromaDB
Docker
Streamlit