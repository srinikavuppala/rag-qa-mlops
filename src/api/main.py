import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

# App & RAG imports
from src.services.rag_pipeline import run_rag_pipeline
from src.services.ingestion import ingest_document, DocumentIngestionError
from src.services.chunking import chunk_text
from src.services.embeddings import store_embeddings_in_chroma
from src.core.config import settings

# Auth & DB imports
from src.models.database import get_db, User
from src.utils.auth import hash_password, verify_password, create_access_token

# Initialize FastAPI App
app = FastAPI(
    title="RAG-Based Document Q&A API",
    description="Secure API for uploading documents and querying them using RAG.",
    version="1.0.0"
)

# Ensure directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# OAuth2 setup for Swagger UI "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- Pydantic Models ---

class Citation(BaseModel):
    document_name: str
    chunk_index: int
    relevance_score: float

class QueryRequest(BaseModel):
    query: str
    collection_name: str = "ai_knowledge"

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Auth Dependency ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decodes JWT token and fetches user from DB. Protects endpoints."""
    from jose import JWTError, jwt
    from src.core.config import settings # Fixed import!
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"]) # Fixed variable!
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
# --- System Endpoints ---

@app.get("/", tags=["System"])
def health_check():
    return {"status": "RAG API is running successfully!"}

# --- Auth Endpoints (SRS FR-UM-001) ---

@app.post("/auth/register", tags=["Authentication"])
@app.post("/auth/register", tags=["Authentication"])
def register_user(username: str, password: str, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_pwd = hash_password(password)
        new_user = User(username=username, hashed_password=hashed_pwd)
        db.add(new_user)
        db.commit()
        return {"message": f"User '{username}' registered successfully!"}
        
    except HTTPException:
        raise
    except Exception as e:
        # This will print the exact error in the Swagger UI!
        raise HTTPException(status_code=500, detail=f"Debug Error: {str(e)}")
@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and receive a JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Document Endpoints (Now Protected!) ---

@app.post("/documents/upload", tags=["Document Management"])
def upload_document(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user) # SEC-AU-001: Requires Auth
):
    if file_ext := os.path.splitext(file.filename)[1].lower():
        if file_ext not in settings.SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_ext}")

    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()

    try:
        text = ingest_document(temp_file_path)
        chunks = chunk_text(text)
        collection_name = os.path.splitext(file.filename)[0].replace(" ", "_").lower()
        vector_db = store_embeddings_in_chroma(chunks, document_name=file.filename, collection_name=collection_name)
        
        return {"status": "success", "message": f"Document processed.", "collection_name": collection_name, "chunks_created": len(chunks)}
    except DocumentIngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- RAG Query Endpoint (Now Protected!) ---

@app.post("/query", response_model=QueryResponse, tags=["RAG Query"])
@app.post("/query", response_model=QueryResponse, tags=["RAG Query"])
def query_documents(
    request: QueryRequest, 
    current_user: User = Depends(get_current_user)
):
    try:
        result = run_rag_pipeline(request.query, request.collection_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Pipeline Error: {str(e)}")