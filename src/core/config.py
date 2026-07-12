import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    SUPPORTED_FORMATS: list = [".pdf", ".docx", ".txt", ".md"]
    CHROMA_PERSIST_DIR: str = "data/vector_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # SRS 11.4: JWT Config
    JWT_SECRET: str = "change-me-in-production"

    class Config:
        env_file = ".env"

settings = Settings()