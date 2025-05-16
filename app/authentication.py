from fastapi import FastAPI, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from mysql.connector import pooling
import os
from datetime import datetime, timedelta
import hashlib
import uuid
from typing import Optional, Dict, Any
import dotenv
from contextlib import asynccontextmanager

# Load environment variables
dotenv.load_dotenv()

# Database connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="auth_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "auth_db")
)

# Session store (in-memory for demo)
sessions = {}
session_expiry = {}
SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRY = timedelta(minutes=30)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    location: str = Field(default="")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    location: Optional[str] = None
    created_at: datetime

# Password hashing (simple sha256)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Database initialization
def init_db():
    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Session management
def create_session(user_id: int, user_data: Dict[str, Any]) -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "user_id": user_id,
        **user_data
    }
    session_expiry[session_id] = datetime.now() + SESSION_EXPIRY
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    if session_id not in sessions:
        return None
    if datetime.now() > session_expiry[session_id]:
        del sessions[session_id]
        del session_expiry[session_id]
        return None
    # Refresh expiry on activity
    session_expiry[session_id] = datetime.now() + SESSION_EXPIRY
    return sessions[session_id]

def delete_session(session_id: str) -> None:
    sessions.pop(session_id, None)
    session_expiry.pop(session_id, None)

# Auth dependencies
async def get_current_user(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    return get_session(session_id)

async def auth_required(current_user: Optional[Dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# FastAPI lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # Shutdown cleanup if needed
