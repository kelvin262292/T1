from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Database instance
db_instance = Database()

async def connect_to_mongo():
    """Create database connection"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    logger.info(f"Connecting to MongoDB: {mongo_url}")
    db_instance.client = AsyncIOMotorClient(mongo_url)
    db_instance.database = db_instance.client[db_name]
    
    # Test connection
    try:
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed")

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if db_instance.database is None:
        raise Exception("Database not initialized")
    return db_instance.database

async def create_indexes():
    """Create database indexes for performance"""
    db = await get_database()
    
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("created_at")
    await db.users.create_index("role")
    
    # Status checks collection indexes
    await db.status_checks.create_index("timestamp")
    await db.status_checks.create_index("client_name")
    
    logger.info("Database indexes created successfully")
