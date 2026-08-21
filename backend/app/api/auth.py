from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.api import deps
from app.schemas.auth import Token, UserResponse, UserCreate
from app.db.models.user import User
from app.db.models.audit import AuditLog

router = APIRouter()
settings = get_settings()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Audit log for login
    audit = AuditLog(
        actor_id=user.id,
        actor_role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        action_type="USER_LOGIN",
        entity_type="User",
        entity_id=str(user.id),
        description=f"Successful login for {user.email}",
    )
    db.add(audit)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get a new access token using a refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            request.refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception
        
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user

# Setup initial admin route for ease of testing during hackathon
@router.post("/setup", response_model=UserResponse)
def create_initial_admin(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Create an initial user if none exists (Hackathon only utility)
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        team_id=user_in.team_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
