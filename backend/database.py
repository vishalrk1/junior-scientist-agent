import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    users_collection = None
    
    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
            cls.db = cls.client[settings.DATABASE_NAME]
            cls.users_collection = cls.db.users
            
            await cls.users_collection.create_index("email", unique=True)
            logger.info("Database indexes ensured.")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            logger.info("MongoDB connection closed.")

    @classmethod
    async def check_connection(cls) -> bool:
        try:
            await cls.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False

    @classmethod
    def get_users_collection(cls):
        if cls.users_collection is None:
            raise Exception("Database not initialized. Make sure to call connect_db first.")
        return cls.users_collection