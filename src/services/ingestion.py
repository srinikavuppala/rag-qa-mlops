import os
import pdfplumber
import docx
from src.core.config import settings

class DocumentIngestionError(Exception):
    """Custom exception for document ingestion errors"""
    pass

def validate_file(file_path: str) -> bool:
    """Validates file format and size (SRS FR-DM-003)"""
    if not os.path.exists(file_path):
        raise DocumentIngestionError(f"File not found: {file_path}")
    
    # Check file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in settings.SUPPORTED_FORMATS:
        raise DocumentIngestionError(f"Unsupported file format: {file_ext}. Supported: {settings.SUPPORTED_FORMATS}")
    
    # Check file size (50MB limit from SRS)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise DocumentIngestionError(f"File size ({file_size_mb:.2f}MB) exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB")
    
    return True

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise DocumentIngestionError(f"Error parsing PDF: {str(e)}")
    
    if not text.strip():
        raise DocumentIngestionError("Could not extract any text from the PDF. It might be image-based.")
        
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from DOCX using python-docx"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text
    except Exception as e:
        raise DocumentIngestionError(f"Error parsing DOCX: {str(e)}")

def extract_text_from_txt_md(file_path: str) -> str:
    """Extracts text from TXT or Markdown files"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback for older Windows encoded text files
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()

def ingest_document(file_path: str) -> str:
    """Main function to validate and extract text from a document"""
    validate_file(file_path)
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_ext == ".docx":
        return extract_text_from_docx(file_path)
    elif file_ext in [".txt", ".md"]:
        return extract_text_from_txt_md(file_path)