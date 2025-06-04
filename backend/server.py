from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import our modules
from models import StatusCheck, StatusCheckCreate
from auth import AuthManager
from database import connect_to_mongo, close_mongo_connection, get_database, create_indexes
from routes.auth import router as auth_router
from routes.users import router as users_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Create the main app
app = FastAPI(
    title="E-commerce API",
    description="A comprehensive e-commerce platform API",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Include authentication and user management routes
api_router.include_router(auth_router)
api_router.include_router(users_router)

# Health check endpoint
@api_router.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "1.0.0"
    }

# Hello World endpoint (keeping for compatibility)
@api_router.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {"message": "Hello World"}

# Status check endpoints (keeping existing functionality)
@api_router.post("/status", response_model=StatusCheck)
@limiter.limit("20/minute")
async def create_status_check(
    request: Request,
    input: StatusCheckCreate,
    db = Depends(get_database)
):
    """Create a status check (rate limited)"""
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
@limiter.limit("60/minute")
async def get_status_checks(
    request: Request,
    db = Depends(get_database)
):
    """Get status checks (rate limited)"""
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Protected status endpoint example
@api_router.get("/status/protected", response_model=List[StatusCheck])
async def get_protected_status_checks(
    current_user = Depends(AuthManager.get_current_active_user),
    db = Depends(get_database)
):
    """Get status checks (authentication required)"""
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# CORS middleware with tighter security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://localhost:3000",
        os.environ.get("REACT_APP_BACKEND_URL", "").replace("/api", "").replace("https://", "https://").replace("http://", "http://")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection and create indexes"""
    await connect_to_mongo()
    await create_indexes()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection"""
    await close_mongo_connection()
    logger.info("Application shutdown complete")
