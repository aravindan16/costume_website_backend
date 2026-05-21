import re

with open("main.py", "r") as f:
    content = f.read()

# 1. Remove memory lists
content = re.sub(r'memory_products = \[product\.copy\(\) for product in SAMPLE_PRODUCTS\]\nmemory_users = \[\]\n*', '', content)

# 2. Update startup
new_startup = """@app.on_event("startup")
async def startup():
    global client, db
    if not MONGODB_URI:
        raise Exception("MONGODB_URI is not set in environment variables.")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    if await db.products.count_documents({}) == 0:
        await db.products.insert_many(SAMPLE_PRODUCTS)
        
    admin_email_lower = ADMIN_EMAIL.lower()
    admin_user = await db.users.find_one({"email": admin_email_lower})
    if not admin_user:
        await db.users.insert_one({
            "name": "Nilla Sarres Admin",
            "email": admin_email_lower,
            "phone": "",
            "password": ADMIN_PASSWORD,
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        })
    else:
        await db.users.update_one({"email": admin_email_lower}, {"$set": {"password": ADMIN_PASSWORD, "role": "admin"}})"""
content = re.sub(r'@app\.on_event\("startup"\)\nasync def startup\(\):[\s\S]*?(?=@app\.on_event\("shutdown"\))', new_startup + "\n\n\n", content)

# 3. Update health
content = re.sub(r'"mongodb" if db is not None else "memory"', '"mongodb"', content)

# 4. get_products
new_get_products = """@app.get("/api/products", response_model=List[Product])
async def get_products():
    documents = await db.products.find({}).sort("name", 1).to_list(length=100)
    return [serialize_product(document) for document in documents]"""
content = re.sub(r'@app\.get\("/api/products", response_model=List\[Product\]\)\nasync def get_products\(\):[\s\S]*?(?=@app\.post\("/api/auth/signup"\))', new_get_products + "\n\n\n", content)

# 5. signup
content = re.sub(r'    if db is None:\n        if any\(existing\["email"\] == user\["email"\] for existing in memory_users\):\n            raise HTTPException\(status_code=400, detail="Account already exists\."\)\n        memory_users\.append\(user\)\n        return public_account\(user\)\n\n', '', content)

# 6. login
new_login = """@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    email = credentials.email.lower()

    user = await db.users.find_one({"email": email, "password": credentials.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return public_account(user)"""
content = re.sub(r'@app\.post\("/api/auth/login"\)\nasync def login\(credentials: LoginRequest\):[\s\S]*?(?=@app\.post\("/api/products", response_model=Product\))', new_login + "\n\n\n", content)

# 7. create_product_with_image
content = re.sub(r'    if db is None:\n        memory_products\.insert\(0, product\.model_dump\(\)\)\n        return product\n\n', '', content)

# 8. update_product_with_image
content = re.sub(r'    existing = None\n    if db is None:\n        existing = next\(\(product for product in memory_products if product\["id"\] == product_id\), None\)\n    else:\n        existing = await db\.products\.find_one\(\{"id": product_id\}\)', '    existing = await db.products.find_one({"id": product_id})', content)
content = re.sub(r'    if db is None:\n        for index, item in enumerate\(memory_products\):\n            if item\["id"\] == product_id:\n                memory_products\[index\] = product\.model_dump\(\)\n                break\n        return product\n\n', '', content)

# 9. delete_product
content = re.sub(r'    if db is None:\n        global memory_products\n        initial_len = len\(memory_products\)\n        memory_products = \[product for product in memory_products if product\["id"\] != product_id\]\n        if len\(memory_products\) == initial_len:\n            raise HTTPException\(status_code=404, detail="Saree not found\."\)\n        return \{"ok": True, "message": "Saree deleted successfully\."\}\n\n', '', content)

# 10. orders
content = re.sub(r'    if db is None:\n        return \{"ok": True, "mode": "memory", "message": "Order accepted locally for demo\."\}\n\n', '', content)

# Write back
with open("main.py", "w") as f:
    f.write(content)
