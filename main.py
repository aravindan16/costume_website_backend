import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "nilla_sarres")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nillasarres.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "NillaAdmin@123")
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Nilavalayam API")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN,
        "http://127.0.0.1:5173",
        "https://nilavalayam.onrender.com",
        "https://costume-website-frontend.onrender.com",
        "https://nilavalayam.rf.gd",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: Optional[AsyncIOMotorClient] = None
db = None

SAMPLE_PRODUCTS = [
    {
        "id": "silk-peacock-blue",
        "name": "Peacock Blue Silk Saree",
        "category": "Silk",
        "price": 4299,
        "color": "Peacock Blue",
        "stock": 8,
        "image": "/nilla-sarres-hero.png",
        "description": "Rich silk finish with a woven border for weddings and festive evenings.",
    },
    {
        "id": "rose-gold-party",
        "name": "Rose Gold Party Saree",
        "category": "Party Wear",
        "price": 2899,
        "color": "Rose Gold",
        "stock": 12,
        "image": "/nilla-sarres-hero.png",
        "description": "Soft drape, light shimmer, and a comfortable blouse-ready fall.",
    },
    {
        "id": "ivory-cotton",
        "name": "Ivory Cotton Saree",
        "category": "Cotton",
        "price": 1499,
        "color": "Ivory",
        "stock": 15,
        "image": "/nilla-sarres-hero.png",
        "description": "Everyday elegance with breathable cotton and a crisp woven texture.",
    },
    {
        "id": "emerald-bridal",
        "name": "Emerald Bridal Saree",
        "category": "Bridal",
        "price": 6999,
        "color": "Emerald",
        "stock": 4,
        "image": "/nilla-sarres-hero.png",
        "description": "Statement saree with a grand border and jewel-tone festive finish.",
    },
]

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: int = Field(gt=0)
    color: str
    stock: int = Field(ge=0)
    image: str = "/nilla-sarres-hero.png"
    images: List[str] = []
    description: str


class Customer(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    address: str = Field(min_length=5)


class OrderItem(BaseModel):
    id: str
    name: str
    price: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Order(BaseModel):
    customer: Customer
    items: List[OrderItem]
    total: int = Field(gt=0)


class SignupRequest(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)


def serialize_product(document):
    document["id"] = document.get("id") or str(document.pop("_id"))
    document.pop("_id", None)
    return document


def slugify(value: str):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"saree-{uuid4().hex[:8]}"


def public_account(account):
    return {
        "name": account["name"],
        "email": account["email"],
        "phone": account.get("phone", ""),
        "role": account["role"],
    }


def verify_admin(email: Optional[str], password: Optional[str]):
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password.")


@app.on_event("startup")
async def startup():
    global client, db

    print("Using DB:", MONGODB_DB)
    print("Mongo URI exists:", bool(MONGODB_URI))

    if not MONGODB_URI:
        print("MongoDB URI not found. Using memory mode.")
        return

    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB]

        await client.admin.command("ping")
        print("MongoDB connected successfully")

        if await db.products.count_documents({}) == 0:
            await db.products.insert_many(SAMPLE_PRODUCTS)

    except Exception as e:
        print("MongoDB connection failed:", str(e))
        db = None

@app.on_event("shutdown")
async def shutdown():
    if client:
        client.close()


@app.get("/api/health")
async def health():
    return {"ok": True, "database": "mongodb"}


@app.get("/api/products", response_model=List[Product])
async def get_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    documents = await db.products.find({}).sort("name", 1).to_list(length=100)

    print("Products found:", len(documents))

    return [serialize_product(document) for document in documents]


@app.post("/api/auth/signup")
async def signup(account: SignupRequest):
    user = {
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


@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    email = credentials.email.lower()

    user = await db.users.find_one({"email": email, "password": credentials.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return public_account(user)


@app.post("/api/products", response_model=Product)
async def create_product(product: Product):
    if db is None:
        raise HTTPException(status_code=503, detail="Connect MongoDB to add products.")

    await db.products.update_one(
        {"id": product.id},
        {"$set": product.model_dump()},
        upsert=True,
    )
    return product


@app.post("/api/admin/products", response_model=Product)
async def create_product_with_image(
    name: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    color: str = Form(...),
    stock: int = Form(...),
    description: str = Form(...),
    images: List[UploadFile] = File(...),
    x_admin_email: Optional[str] = Header(default=None),
    x_admin_password: Optional[str] = Header(default=None),
):
    verify_admin(x_admin_email, x_admin_password)

    valid_images = [img for img in images if img.filename]
    if not valid_images:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")

    product_id = f"{slugify(name)}-{uuid4().hex[:6]}"
    saved_images = []

    for idx, img in enumerate(valid_images):
        extension = Path(img.filename or "").suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(status_code=400, detail="Upload only JPG, PNG, or WebP images.")
        
        image_name = f"{product_id}-{idx}{extension}"
        image_path = UPLOAD_DIR / image_name
        image_path.write_bytes(await img.read())
        saved_images.append(f"/uploads/{image_name}")

    cover_image = saved_images[0] if saved_images else "/nilla-sarres-hero.png"

    product = Product(
        id=product_id,
        name=name,
        category=category,
        price=price,
        color=color,
        stock=stock,
        image=cover_image,
        images=saved_images,
        description=description,
    )

    await db.products.insert_one(product.model_dump())
    return product


@app.put("/api/admin/products/{product_id}", response_model=Product)
async def update_product_with_image(
    product_id: str,
    name: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    color: str = Form(...),
    stock: int = Form(...),
    description: str = Form(...),
    existing_images: List[str] = Form(default=[]),
    images: Optional[List[UploadFile]] = File(default=None),
    x_admin_email: Optional[str] = Header(default=None),
    x_admin_password: Optional[str] = Header(default=None),
):
    verify_admin(x_admin_email, x_admin_password)

    existing = await db.products.find_one({"id": product_id})

    if not existing:
        raise HTTPException(status_code=404, detail="Saree not found.")

    image_list = existing_images
    valid_images = [img for img in (images or []) if img.filename]

    if valid_images:
        saved_images = []
        for idx, img in enumerate(valid_images):
            extension = Path(img.filename).suffix.lower()
            if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise HTTPException(status_code=400, detail="Upload only JPG, PNG, or WebP images.")
            image_name = f"{product_id}-{idx}-{uuid4().hex[:4]}{extension}"
            image_path = UPLOAD_DIR / image_name
            image_path.write_bytes(await img.read())
            saved_images.append(f"/uploads/{image_name}")
        image_list = image_list + saved_images

    if not image_list:
        image_list = [existing.get("image", "/nilla-sarres-hero.png")]

    image_url = image_list[0]

    product = Product(
        id=product_id,
        name=name,
        category=category,
        price=price,
        color=color,
        stock=stock,
        image=image_url,
        images=image_list,
        description=description,
    )

    await db.products.update_one({"id": product_id}, {"$set": product.model_dump()})
    return product
@app.delete("/api/admin/products/{product_id}")
async def delete_product(
    product_id: str,
    x_admin_email: Optional[str] = Header(default=None),
    x_admin_password: Optional[str] = Header(default=None),
):
    verify_admin(x_admin_email, x_admin_password)

    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saree not found.")
    return {"ok": True, "message": "Saree deleted successfully."}


@app.post("/api/orders")
async def create_order(order: Order):
    order_data = order.model_dump()
    order_data["created_at"] = datetime.now(timezone.utc)
    order_data["status"] = "new"

    result = await db.orders.insert_one(order_data)
    return {"ok": True, "order_id": str(result.inserted_id)}

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
