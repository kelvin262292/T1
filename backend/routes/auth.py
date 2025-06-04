from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta, datetime
from ..models import UserCreate, UserLogin, Token, User, UserUpdate
from ..auth import AuthManager, ACCESS_TOKEN_EXPIRE_MINUTES
from ..database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await AuthManager.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = AuthManager.get_password_hash(user_data.password)
    
    # Create user object
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        role=user_data.role
    )
    
    # Prepare user document for database
    user_dict = user.dict()
    user_dict["password_hash"] = password_hash
    
    # Insert user into database
    try:
        result = await db.users.insert_one(user_dict)
        logger.info(f"User created with ID: {result.inserted_id}")
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Authenticate user and return JWT token"""
    # Get user from database
    user_doc = await db.users.find_one({"email": user_credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create user object (without password_hash for response)
    user_data = {k: v for k, v in user_doc.items() if k != "password_hash"}
    user = User(**user_data)
    
    # Verify password
    if not AuthManager.verify_password(user_credentials.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthManager.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # Update last login time
    await db.users.update_one(
        {"email": user.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    logger.info(f"User {user.email} logged in successfully")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        user=user
    )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(AuthManager.get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(AuthManager.get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update current user information"""
    # Prepare update data
    update_data = {}
    if user_update.email is not None:
        # Check if new email already exists
        existing_user = await AuthManager.get_user_by_email(db, user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_data["email"] = user_update.email
    
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    if user_update.role is not None:
        update_data["role"] = user_update.role
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user in database
        await db.users.update_one(
            {"email": current_user.email},
            {"$set": update_data}
        )
        
        # Return updated user
        updated_user_doc = await db.users.find_one({"email": current_user.email})
        user_data = {k: v for k, v in updated_user_doc.items() if k != "password_hash"}
        return User(**user_data)
    
    return current_user

@router.post("/logout")
async def logout_user():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}
