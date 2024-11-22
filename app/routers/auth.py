from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.user import UserCreate, UserResponse
from app.services.supabase import get_supabase_client
from datetime import timedelta
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate):
    supabase = get_supabase_client()
    
    # Check if user exists
    existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = {
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name
    }
    
    result = supabase.table("users").insert(new_user).execute()
    
    return UserResponse(**result.data[0])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    supabase = get_supabase_client()
    
    # Verify user credentials
    user = supabase.table("users").select("*").eq("email", form_data.username).execute()
    if not user.data or not verify_password(form_data.password, user.data[0]["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.data[0]["id"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    } 