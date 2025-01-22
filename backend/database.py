import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import settings
from typing import Optional
import backoff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    users_collection = None
    projects_collection = None
    agents_collection = None
    
    @classmethod
    @backoff.on_exception(backoff.expo, ConnectionFailure, max_tries=3)
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=50000,
                waitQueueTimeoutMS=5000
            )
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
            cls.db = cls.client[settings.DATABASE_NAME]
            cls.users_collection = cls.db.users
            cls.projects_collection = cls.db.projects
            cls.agents_collection = cls.db.agents
            
            await cls.users_collection.create_indexes([
                [("email", 1)],
                [("created_at", -1)]
            ])
            await cls.projects_collection.create_indexes([
                [("user_id", 1)],
                [("created_at", -1)],
                [("status", 1)],
                [("last_activity", -1)],
                [("model_provider", 1)]
            ])
            await cls.agents_collection.create_indexes([
                [("project_id", 1)],
                [("type", 1)],
                [("status", 1)],
                [("project_id", 1), ("type", 1)],
                [("project_id", 1), ("is_default", 1)]
            ])
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
    
    @classmethod 
    def get_projects_collection(cls):
        if cls.projects_collection is None:
            raise Exception("Database not initialized. Make sure to call connect_db first.")
        return cls.projects_collection

    @classmethod
    def get_agents_collection(cls):
        if cls.agents_collection is None:
            raise Exception("Database not initialized. Make sure to call connect_db first.")
        return cls.agents_collection

    @classmethod
    async def get_collection(cls, collection_name: str):
        if not cls.client:
            await cls.connect_db()
        return cls.db[collection_name]

    @classmethod
    @backoff.on_exception(backoff.expo, OperationFailure, max_tries=3)
    async def execute_with_retry(cls, collection, operation, *args, **kwargs):
        try:
            return await getattr(collection, operation)(*args, **kwargs)
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            raise