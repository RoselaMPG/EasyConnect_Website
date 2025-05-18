from fastapi import FastAPI, Form, Response, status, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
import os
from fastapi.staticfiles import StaticFiles
#import logging
#import httpx
#from mysql.connector import Error
#from fastapi import FastAPI, HTTPException, Query
#from fastapi.staticfiles import StaticFiles
#from fastapi.responses import FileResponse
from pydantic import BaseModel
#import mysql.connector
from datetime import datetime
#import dotenv
#from contextlib import asynccontextmanager
#from typing import Optional, List, Dict, Any
import uvicorn
import json
#import bcrypt


# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# I commented the database part out for right now
"""
from .database import (
    get_db_connection,
    get_user_by_email,
    create_user,
    create_session,
    get_session,
    delete_session,
    register_device,
    get_user_by_id,
    get_user_devices,
    delete_device,
    get_sensor_data
)
"""

class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None
    mac_address: str  # Add this field

class SensorResponse(BaseModel):
    id: int
    value: float
    unit: str
    timestamp: str

# Initialize FastAPI app
app = FastAPI()
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Set to store active devices
active_devices = set()

def is_authenticated(request: Request) -> bool:
    session_id = request.cookies.get("session_id")
    if not session_id:
        return False
    # session = get_session(session_id)
    # return session is not None
    return True  # temporarily allow all for running without DB

def validate_sensor_type(sensor_type: str):
    valid_sensor_types = ["temperature", "humidity", "pressure"]  # Example, adjust accordingly
    if sensor_type not in valid_sensor_types:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid sensor type")

# Public routes
@app.get("/", response_class=FileResponse)
async def index():
    return FileResponse("app/static/index.html")

@app.get("/signup", response_class=FileResponse)
async def signup_page():
    return FileResponse("app/static/signup.html")

@app.post("/signup")
async def signup(response: Response, email: str = Form(...), password: str = Form(...), location: str = Form(...)):
    # existing_user = get_user_by_email(email)
    # if existing_user:
    #     return RedirectResponse(url="/signup?error=Email+already+registered", status_code=status.HTTP_303_SEE_OTHER)
    
    # user_id = create_user(email, password, location)  # Pass location here
    # if not user_id:
    #     return RedirectResponse(url="/signup?error=Error+creating+user", status_code=status.HTTP_303_SEE_OTHER)
    
    # Create a new session with the UUID user_id
    # session_id = create_session(user_id)
    # if not session_id:
    #     return RedirectResponse(url="/signup?error=Error+creating+session", status_code=status.HTTP_303_SEE_OTHER)
    
    # response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    # response.set_cookie(key="session_id", value=session_id, httponly=True)
    # logger.info(f"User created and logged in: {user_id}, session: {session_id}")

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login", response_class=FileResponse)
async def login_page():
    return FileResponse("app/static/login.html")

@app.post("/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    # user = get_user_by_email(email)
    # if not user:
    #     return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=status.HTTP_303_SEE_OTHER)
    
    # Verify the password
    # if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
    #     # Create a session with the user's UUID
    #     session_id = create_session(user["id"])
    #     if not session_id:
    #         return RedirectResponse(url="/login?error=Error+creating+session", status_code=status.HTTP_303_SEE_OTHER)
        
    #     response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    #     response.set_cookie(key="session_id", value=session_id, httponly=True)
    #     logger.info(f"User logged in: {user['id']}, session: {session_id}")
    #     return response
    # else:
    #     return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(response: Response, request: Request):
    # session_id = request.cookies.get("session_id")
    # if session_id:
    #     delete_session(session_id)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_id")
    response.headers.append("Cache-Control", "no-cache, no-store, must-revalidate")
    response.headers.append("Pragma", "no-cache")
    response.headers.append("Expires", "0")
    return response

# Protected routes
@app.get("/dashboard_host")
async def dashboard_host(request: Request):
    logger.info(f"Session ID: {request.cookies.get('session_id')}")
    
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # session = get_session(request.cookies.get("session_id"))
    # logger.info(f"Session in DB: {session}")
    
    response = FileResponse("app/static/dashboard_host.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.get("/dashboard_user")
async def dashboard_user(request: Request):
    logger.info(f"Session ID: {request.cookies.get('session_id')}")
    
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # session = get_session(request.cookies.get("session_id"))
    # logger.info(f"Session in DB: {session}")
    
    response = FileResponse("app/static/dashboard_user.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.get("/profile")
async def profile(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response = FileResponse("app/static/profile.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.get("/api/user/profile")
async def get_user_profile(request: Request):
    if not is_authenticated(request):
        return {"error": "Not authenticated"}, 401
    
    # session_id = request.cookies.get("session_id")
    # session = get_session(session_id)
    # if not session:
    #     return {"error": "Invalid session"}, 401
    
    # # Get user details using UUID
    # user_id = session['user_id']
    # user = get_user_by_id(user_id)
    
    # if not user:
    #     return {"error": "User not found"}, 404
    
    # # Get user devices
    # devices = get_user_devices(user_id)
    
    # Return user profile data
    return {
        "name": "Demo User",
        "email": "demo@example.com",
    }

from fastapi import HTTPException

@app.post("/register-device")
async def register_device_route(
    request: Request,
    device_name: str = Form(...),
    device_type: str = Form(...),
    mac_address: str = Form(...)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # session_id = request.cookies.get("session_id")
    # session = get_session(session_id)
    # if not session:
    #     return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Check if the MAC address is in the active_devices set
    if mac_address not in active_devices:
        logger.error(f"Device with MAC address {mac_address} is not active")
        return RedirectResponse(url="/profile?error=Device+not+active", status_code=status.HTTP_303_SEE_OTHER)

    # Register the device
    # device_id = register_device(session["user_id"], device_name, device_type, mac_address)
    # if device_id:
    #     logger.info(f"Device registered successfully: {device_id}")
    #     return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
    # else:
    #     logger.error("Failed to register device")
    #     return RedirectResponse(url="/profile?error=Failed+to+register+device", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/remove-device/{device_id}")
async def remove_device(request: Request, device_id: str):
    if not is_authenticated(request):
        return {"error": "Not authenticated"}, 401
    
    # session_id = request.cookies.get("session_id")
    # session = get_session(session_id)
    # if not session:
    #     return {"error": "Invalid session"}, 401
    
    # user_id
