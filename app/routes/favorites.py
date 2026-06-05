from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from app.core.database import get_db
from app.models.requests import FavoriteRequest

router = APIRouter()

def verify_user(user_id: Optional[str]):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID is required.")

@router.get("/favorites", response_model=List[str])
async def get_favorites(x_user_id: Optional[str] = Header(default=None)):
    verify_user(x_user_id)
    db = get_db()
    if db is None:
        return []
    
    docs = await db.favorites.find({"user_id": x_user_id}).to_list(length=1000)
    return [doc["product_id"] for doc in docs]

@router.post("/favorites")
async def add_favorite(
    req: FavoriteRequest,
    x_user_id: Optional[str] = Header(default=None)
):
    verify_user(x_user_id)
    if req.user_id != x_user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch.")
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    await db.favorites.update_one(
        {"user_id": req.user_id, "product_id": req.product_id},
        {"$set": {"user_id": req.user_id, "product_id": req.product_id}},
        upsert=True
    )
    return {"ok": True}

@router.delete("/favorites/{product_id}")
async def remove_favorite(
    product_id: str,
    x_user_id: Optional[str] = Header(default=None)
):
    verify_user(x_user_id)
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    await db.favorites.delete_one({"user_id": x_user_id, "product_id": product_id})
    return {"ok": True}
