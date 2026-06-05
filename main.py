from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGODB_URI, MONGODB_DB, FRONTEND_ORIGIN, UPLOAD_DIR
from app.core.database import db_instance
from app.routes import auth, admin, public, favorites

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

app.include_router(auth.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")

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

@app.on_event("startup")
async def startup():
    print("Using DB:", MONGODB_DB)
    print("Mongo URI exists:", bool(MONGODB_URI))

    if not MONGODB_URI:
        print("MongoDB URI not found. Using memory mode.")
        return

    try:
        db_instance.client = AsyncIOMotorClient(MONGODB_URI)
        db_instance.db = db_instance.client[MONGODB_DB]

        await db_instance.client.admin.command("ping")
        print("MongoDB connected successfully")

        if await db_instance.db.products.count_documents({}) == 0:
            await db_instance.db.products.insert_many(SAMPLE_PRODUCTS)

    except Exception as e:
        print("MongoDB connection failed:", str(e))
        db_instance.db = None

@app.on_event("shutdown")
async def shutdown():
    if db_instance.client:
        db_instance.client.close()

@app.get("/api/health")
async def health():
    return {"ok": True, "database": "mongodb"}

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
