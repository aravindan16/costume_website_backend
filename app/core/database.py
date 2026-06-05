from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGODB_URI, MONGODB_DB

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

db_instance = Database()

def get_db():
    return db_instance.db
