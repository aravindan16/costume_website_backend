from fastapi import APIRouter, HTTPException, File, Form, Header, UploadFile
from typing import Optional, List
from pathlib import Path
from uuid import uuid4
import re
from app.core.database import get_db
from app.core.config import ADMIN_EMAIL, ADMIN_PASSWORD, UPLOAD_DIR
from app.models.domain import Product

router = APIRouter()

def verify_admin(email: Optional[str], password: Optional[str]):
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password.")

def slugify(value: str):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"saree-{uuid4().hex[:8]}"

@router.post("/admin/products", response_model=Product)
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
    db = get_db()

    valid_images = [img for img in images if img.filename]
    if not valid_images:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")

    product_id = f"{slugify(name)}-{uuid4().hex[:6]}"
    saved_images = []

    for idx, img in enumerate(valid_images):
        if not (img.content_type.startswith("image/") or img.content_type == "application/octet-stream"):
            raise HTTPException(status_code=400, detail="Upload only image files.")
        
        extension = Path(img.filename or "").suffix.lower()
        if not extension:
            # Try to guess extension from content type
            if "png" in img.content_type: extension = ".png"
            elif "webp" in img.content_type: extension = ".webp"
            else: extension = ".jpg" # Default to jpg for octet-stream or jpeg
        
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


@router.put("/admin/products/{product_id}", response_model=Product)
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
    db = get_db()

    existing = await db.products.find_one({"id": product_id})

    if not existing:
        raise HTTPException(status_code=404, detail="Saree not found.")

    image_list = existing_images
    valid_images = [img for img in (images or []) if img.filename]

    if valid_images:
        saved_images = []
        for idx, img in enumerate(valid_images):
            if not (img.content_type.startswith("image/") or img.content_type == "application/octet-stream"):
                raise HTTPException(status_code=400, detail="Upload only image files.")
                
            extension = Path(img.filename or "").suffix.lower()
            if not extension:
                if "png" in img.content_type: extension = ".png"
                elif "webp" in img.content_type: extension = ".webp"
                else: extension = ".jpg"
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

@router.delete("/admin/products/{product_id}")
async def delete_product(
    product_id: str,
    x_admin_email: Optional[str] = Header(default=None),
    x_admin_password: Optional[str] = Header(default=None),
):
    verify_admin(x_admin_email, x_admin_password)
    db = get_db()

    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saree not found.")
    return {"ok": True, "message": "Saree deleted successfully."}
