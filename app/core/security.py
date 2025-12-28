# app/core/security.py - ARGON2 VERSION
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import settings
import uuid

# Use Argon2 instead of bcrypt - no 72-byte limit and more secure
pwd_context = CryptContext(
    schemes=["argon2"],  # Changed from "bcrypt" to "argon2"
    deprecated="auto",
    # Optional: Customize Argon2 parameters (good defaults already)
    argon2__time_cost=2,      # Number of iterations
    argon2__memory_cost=65536,  # 64MB memory usage
    argon2__parallelism=2,    # Number of parallel threads
    argon2__hash_len=32,      # Hash length in bytes
    argon2__salt_len=16,      # Salt length in bytes
)


def get_password_hash(password: str) -> str:
    """
    Hash password using Argon2.
    Argon2 doesn't have the 72-byte limit that bcrypt has.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its Argon2 hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid.uuid4()),
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        if payload.get("type") != token_type:
            return None
            
        return payload
    except JWTError:
        return None