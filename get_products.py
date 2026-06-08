from app.core.database import get_db
import asyncio

async def main():
    db = get_db()
    if not db:
        print("no db")
        return
    docs = await db.products.find({}).to_list(length=100)
    for d in docs:
        print(d["id"], d.get("name"), d.get("image"))

if __name__ == "__main__":
    asyncio.run(main())
