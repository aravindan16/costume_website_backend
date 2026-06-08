from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from uuid import uuid4
from app.core.database import get_db
from app.core.config import ADMIN_EMAIL
from app.models.requests import SignupRequest, LoginRequest

router = APIRouter()

def public_account(account):
    return {
        "id": account.get("id"),
        "name": account["name"],
        "email": account["email"],
        "phone": account.get("phone", ""),
        "address": account.get("address", ""),
        "role": account["role"],
    }

@router.post("/auth/signup")
async def signup(account: SignupRequest):
    db = get_db()
    user_id = str(uuid4())
    user = {
        "id": user_id,
        "name": account.name,
        "phone": account.phone,
        "email": account.email.lower(),
        "password": account.password,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }

    if user["email"] == ADMIN_EMAIL.lower():
        raise HTTPException(status_code=400, detail="This email is reserved for admin.")

    if await db.users.find_one({"email": user["email"]}):
        raise HTTPException(status_code=400, detail="Account already exists.")
    
    await db.users.insert_one(user)
    return public_account(user)

@router.post("/auth/login")
async def login(credentials: LoginRequest):
    db = get_db()
    email = credentials.email.lower()
    
    user = await db.users.find_one({"email": email, "password": credentials.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    # Backward compatibility for old users without id
    if "id" not in user:
        user_id = str(uuid4())
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"id": user_id}})
        user["id"] = user_id
        
    return public_account(user)

@router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import GOOGLE_CLIENT_ID
from app.models.requests import GoogleAuthRequest

@router.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    db = get_db()
    try:
        idinfo = id_token.verify_oauth2_token(
            request.token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        email = idinfo["email"].lower()
        name = idinfo.get("name", email.split("@")[0])
        
        user = await db.users.find_one({"email": email})
        
        if not user:
            user_id = str(uuid4())
            user = {
                "id": user_id,
                "name": name,
                "phone": "",
                "email": email,
                "password": "", 
                "role": "user",
                "created_at": datetime.now(timezone.utc),
                "google_id": idinfo["sub"]
            }
            await db.users.insert_one(user)
        else:
            if "id" not in user:
                user_id = str(uuid4())
                await db.users.update_one({"_id": user["_id"]}, {"$set": {"id": user_id}})
                user["id"] = user_id
                
        return public_account(user)
        
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")

from fastapi import Header
from app.models.requests import UpdateProfileRequest
from typing import Optional

@router.put("/auth/profile")
async def update_profile(
    profile: UpdateProfileRequest,
    x_user_id: Optional[str] = Header(default=None)
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID is required.")
        
    db = get_db()
    result = await db.users.find_one_and_update(
        {"id": x_user_id},
        {"$set": {
            "name": profile.name,
            "phone": profile.phone,
            "address": profile.address
        }},
        return_document=True
    )
    
    if not result:
        # Fallback for older accounts
        result = await db.users.find_one_and_update(
            {"email": x_user_id},
            {"$set": {
                "name": profile.name,
                "phone": profile.phone,
                "address": profile.address
            }},
            return_document=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="User not found.")
            
    return public_account(result)
