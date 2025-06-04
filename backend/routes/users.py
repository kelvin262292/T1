from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, UserCreate, UserUpdate, UserRole
from auth import AuthManager
from database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["user management"])

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    current_user: User = Depends(AuthManager.get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all users (admin only)"""
    # Build query
    query = {}
    if role:
        query["role"] = role
    
    # Get users from database
    users_cursor = db.users.find(query).skip(skip).limit(limit)
    users_docs = await users_cursor.to_list(length=limit)
    
    # Convert to User objects (exclude password_hash)
    users = []
    for user_doc in users_docs:
        user_data = {k: v for k, v in user_doc.items() if k != "password_hash"}
        users.append(User(**user_data))
    
    return users

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(AuthManager.get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user by ID (admin only)"""
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert to User object (exclude password_hash)
    user_data = {k: v for k, v in user_doc.items() if k != "password_hash"}
    return User(**user_data)

@router.put("/{user_id}", response_model=User)
async def update_user_by_id(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(AuthManager.get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update user by ID (admin only)"""
    # Check if user exists
    existing_user_doc = await db.users.find_one({"id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = {}
    if user_update.email is not None:
        # Check if new email already exists
        email_user = await db.users.find_one({"email": user_update.email})
        if email_user and email_user["id"] != user_id:
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
        from datetime import datetime
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user in database
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user_doc = await db.users.find_one({"id": user_id})
    user_data = {k: v for k, v in updated_user_doc.items() if k != "password_hash"}
    return User(**user_data)

@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: User = Depends(AuthManager.get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete user by ID (admin only)"""
    # Don't allow deletion of self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    existing_user_doc = await db.users.find_one({"id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    logger.info(f"User {user_id} deleted by admin {current_user.email}")
    return {"message": "User deleted successfully"}
