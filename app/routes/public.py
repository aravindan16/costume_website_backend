from fastapi import APIRouter, HTTPException
from typing import List
from app.core.database import get_db
from app.models.domain import Product, Order
from datetime import datetime, timezone

router = APIRouter()

def serialize_product(document):
    document["id"] = document.get("id") or str(document.pop("_id"))
    document.pop("_id", None)
    return document

@router.get("/products", response_model=List[Product])
async def get_products():
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    documents = await db.products.find({}).sort("name", 1).to_list(length=100)
    return [serialize_product(document) for document in documents]

@router.post("/products", response_model=Product)
async def create_product(product: Product):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Connect MongoDB to add products.")

    await db.products.update_one(
        {"id": product.id},
        {"$set": product.model_dump()},
        upsert=True,
    )
    return product

@router.post("/orders")
async def create_order(order: Order):
    db = get_db()
    order_data = order.model_dump()
    order_data["created_at"] = datetime.now(timezone.utc)
    order_data["status"] = "new"

    result = await db.orders.insert_one(order_data)
    return {"ok": True, "order_id": str(result.inserted_id)}
