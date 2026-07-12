import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.core.config import settings

# SRS SEC-AU-002: Using bcrypt directly (bypasses broken passlib)
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    # bcrypt requires bytes, so we encode the string
    salt = bcrypt.gensalt() # Default cost factor is 12 (matches SRS SEC-AU-002)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)