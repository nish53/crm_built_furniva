from fastapi import APIRouter, Depends, HTTPException, status
from models import User, UserCreate, UserLogin, Token, UserRole
from auth import get_password_hash, verify_password, create_access_token, get_current_active_user
from database import get_database
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db = Depends(get_database)):
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["id"] = str(uuid.uuid4())
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.insert_one(user_dict)
    
    access_token = create_access_token(data={"sub": user_dict["id"]})
    user = User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})
    
    return Token(access_token=access_token, user=user)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db = Depends(get_database)):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(data={"sub": user["id"]})
    user_obj = User(**{k: v for k, v in user.items() if k != "hashed_password"})
    
    return Token(access_token=access_token, user=user_obj)

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
