import os
import bcrypt
from fastapi import FastAPI, Form, Response, status, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
import httpx
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import mysql.connector
import os
from datetime import datetime
import dotenv
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import uvicorn
import paho.mqtt.client as mqtt
import json


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: Optional[str] = None
    mac_address: str  # Add this field


class SensorResponse(BaseModel):
    id: int
    value: float
    unit: str
    timestamp: str

# Initialize FastAPI app
app = FastAPI()
static_path = os.path.abspath("app/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Set to store active devices
active_devices = set()


# Public routes
@app.get("/", response_class=FileResponse)
async def index():
    return FileResponse("app/static/index.html")

@app.get("/signup", response_class=FileResponse)
async def signup_page():
    return FileResponse("app/static/signup.html")

@app.post("/signup")
async def signup(response: Response, email: str = Form(...), password: str = Form(...), location: str = Form(...)):
    existing_user = get_user_by_email(email)
    if existing_user:
        return RedirectResponse(url="/signup?error=Email+already+registered", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = create_user(email, password, location)  # Pass location here
    if not user_id:
        return RedirectResponse(url="/signup?error=Error+creating+user", status_code=status.HTTP_303_SEE_OTHER)
    
    # Create a new session with the UUID user_id
    session_id = create_session(user_id)
    if not session_id:
        return RedirectResponse(url="/signup?error=Error+creating+session", status_code=status.HTTP_303_SEE_OTHER)
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    logger.info(f"User created and logged in: {user_id}, session: {session_id}")
    return response


@app.get("/login", response_class=FileResponse)
async def login_page():
    return FileResponse("app/static/login.html")

@app.post("/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=status.HTTP_303_SEE_OTHER)
    
    # Verify the password
    if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        # Create a session with the user's UUID
        session_id = create_session(user["id"])
        if not session_id:
            return RedirectResponse(url="/login?error=Error+creating+session", status_code=status.HTTP_303_SEE_OTHER)
        
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        logger.info(f"User logged in: {user['id']}, session: {session_id}")
        return response
    else:
        return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(response: Response, request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_id")
    response.headers.append("Cache-Control", "no-cache, no-store, must-revalidate")
    response.headers.append("Pragma", "no-cache")
    response.headers.append("Expires", "0")
    return response

# Protected routes
@app.get("/dashboard_host")
async def dashboard(request: Request):
    logger.info(f"Session ID: {request.cookies.get('session_id')}")
    
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    session = get_session(request.cookies.get("session_id"))
    logger.info(f"Session in DB: {session}")
    
    response = FileResponse("app/static/dashboard_host.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.get("/dashboard_user")
async def dashboard(request: Request):
    logger.info(f"Session ID: {request.cookies.get('session_id')}")
    
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    session = get_session(request.cookies.get("session_id"))
    logger.info(f"Session in DB: {session}")
    
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
    
    session_id = request.cookies.get("session_id")
    session = get_session(session_id)
    if not session:
        return {"error": "Invalid session"}, 401
    
    # Get user details using UUID
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if not user:
        return {"error": "User not found"}, 404
    
    # Get user devices
    devices = get_user_devices(user_id)
    
    # Return user profile data
    return {
        "name": user["username"],
        "email": user["username"],
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

    session_id = request.cookies.get("session_id")
    session = get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Check if the MAC address is in the active_devices set
    if mac_address not in active_devices:
        logger.error(f"Device with MAC address {mac_address} is not active")
        return RedirectResponse(url="/profile?error=Device+not+active", status_code=status.HTTP_303_SEE_OTHER)

    # Register the device
    device_id = register_device(session["user_id"], device_name, device_type, mac_address)
    if device_id:
        logger.info(f"Device registered successfully: {device_id}")
        return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
    else:
        logger.error("Failed to register device")
        return RedirectResponse(url="/profile?error=Failed+to+register+device", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/remove-device/{device_id}")
async def remove_device(request: Request, device_id: str):
    if not is_authenticated(request):
        return {"error": "Not authenticated"}, 401
    
    session_id = request.cookies.get("session_id")
    session = get_session(session_id)
    if not session:
        return {"error": "Invalid session"}, 401
    
    user_id = session['user_id']
    success = delete_device(user_id, device_id)
    
    if success:
        return {"message": "Device removed successfully"}
    else:
        return {"error": "Failed to remove device"}, 500



@app.get("/api/{sensor_type}", response_model=List[SensorResponse])
def get_sensor_data_cookies(
    request: Request,  # FastAPI request object
    sensor_type: str,
    order_by: str = Query(None, alias="order-by"),
    start_date: str = Query(None, alias="start-date"),
    end_date: str = Query(None, alias="end-date"),
):
    validate_sensor_type(sensor_type)  # Validate sensor_type

    # Extract session_id from the request cookies
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the session from the database
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Get the user_id from the session
    user_id = session['user_id']

    # Call the get_sensor_data function from database.py
    sensor_data = get_sensor_data(sensor_type, user_id, order_by, start_date, end_date)
    
    return sensor_data

@app.post("/api/{sensor_type}", response_model=Dict[str, int])
def insert_sensor_data(sensor_type: str, data: SensorData):
    """Insert new sensor data"""
    validate_sensor_type(sensor_type)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = data.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        f"INSERT INTO {sensor_type} (mac_address, timestamp, value, unit) VALUES (%s, %s, %s, %s)",
        (data.mac_address, timestamp, data.value, data.unit)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return {"id": new_id}

@app.get("/api/{sensor_type}/count")
def get_sensor_count(sensor_type: str) -> int:
    """Get count of readings for a sensor type"""
    validate_sensor_type(sensor_type)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {sensor_type}")
        result = cursor.fetchone()
        
        if result is None or not isinstance(result, (tuple, list)) or len(result) == 0:
            raise HTTPException(status_code=404, detail="Sensor type not found in database")
        
        count = result[0]
        if not isinstance(count, int):
            raise HTTPException(status_code=500, detail="Invalid count value returned from database")
        
        return count
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/{sensor_type}/{id}", response_model=SensorResponse)
def get_sensor_by_id(sensor_type: str, id: int):
    """Get specific sensor reading by ID"""
    validate_sensor_type(sensor_type)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {sensor_type} WHERE id = %s", (id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Data not found")
    return result

@app.put("/api/{sensor_type}/{id}")
def update_sensor_data(sensor_type: str, id: int, data: SensorData):
    """Update existing sensor reading"""
    validate_sensor_type(sensor_type)
    
    updates = []
    params = []
    if data.value is not None:
        updates.append("value = %s")
        params.append(data.value)
    if data.unit is not None:
        updates.append("unit = %s")
        params.append(data.unit)
    if data.timestamp:
        updates.append("timestamp = %s")
        params.append(data.timestamp)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    params.append(id)
    query = f"UPDATE {sensor_type} SET {', '.join(updates)} WHERE id = %s"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": "Update successful"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run("main:app", host="0.0.0.0", port=port)