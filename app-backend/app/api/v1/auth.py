
from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core import security
from app.core import config
from app.models.user import User, Token, TokenWithUser
from app.core.db import get_session

router = APIRouter()
settings = config.get_settings()

class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    # session: Session = Depends(get_session) # Uncomment when DB is ready
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    if form_data.username == "test@example.com" and form_data.password == "password123":
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=form_data.username, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    
    raise HTTPException(status_code=400, detail="Incorrect email or password")

@router.post("/login/google", response_model=TokenWithUser)
async def login_google(
    request_data: GoogleLoginRequest,
    session: Session = Depends(get_session)
) -> Any:
    """
    Verify Google Token (ID Token or Access Token) and return access token
    """
    try:
        email = None
        name = None
        
        # 1. Try to verify as Google ID Token (JWT)
        try:
            idinfo = id_token.verify_oauth2_token(
                request_data.id_token, 
                requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            email = idinfo['email']
            name = idinfo.get('name')
        except ValueError as e:
            # 2. Fallback: Try to verify as Access Token by calling Google UserInfo API
            import requests as py_requests
            response = py_requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                params={"access_token": request_data.id_token}
            )
            
            if response.status_code == 200:
                user_info = response.json()
                email = user_info.get('email')
                name = user_info.get('name')
            else:
                # Both failed
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid Google token (tried ID & Access): {str(e)}",
                )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve email from Google token",
            )

        # 3. User Handling: Check DB and create if not exists
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalars().first()
        
        if not user:
            user = User(
                email=email, 
                full_name=name or email.split('@')[0], 
                hashed_password="SOCIAL_AUTH" # Using social auth indicator
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # 4. Create internal JWT
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=email, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.post("/login/social/{provider}", response_model=Token)
async def login_social(
    provider: str
) -> Any:
    """
    Mock Social Login for Google/Kakao (Legacy/Fallback)
    """
    if provider not in ["google", "kakao"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=f"social_{provider}_user@example.com", expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
