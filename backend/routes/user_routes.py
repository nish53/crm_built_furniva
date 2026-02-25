from fastapi import APIRouter, Depends
from models import User, UserRole
from auth import get_current_active_user
from database import get_database
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def get_users(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(100)
    return users

@router.get("/team", response_model=List[User])
async def get_team_members(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    users = await db.users.find(
        {"is_active": True},
        {"_id": 0, "hashed_password": 0}
    ).to_list(100)
    return users
