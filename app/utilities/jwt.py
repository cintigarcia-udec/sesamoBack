from datetime import datetime, timedelta, timezone
import hashlib
from typing import Optional
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.utilities.db import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.token_blacklist_repository import TokenBlacklistRepository

# OAuth2 scheme
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify the JWT token and return the payload.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def exp_to_datetime(exp_value) -> Optional[datetime]:
    if exp_value is None:
        return None
    if isinstance(exp_value, datetime):
        if exp_value.tzinfo is None:
            return exp_value.replace(tzinfo=timezone.utc)
        return exp_value.astimezone(timezone.utc)
    if isinstance(exp_value, (int, float)):
        return datetime.fromtimestamp(exp_value, tz=timezone.utc)
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user from the token.
    """
    token = credentials.credentials
    payload = verify_token(token)
    token_hash = get_token_hash(token)
    if TokenBlacklistRepository.is_blacklisted(db, token_hash=token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_email = payload.get("sub")
    
    if not isinstance(user_email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = UserRepository.get_by_email(db, email=user_email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

def get_current_admin(user = Depends(get_current_user)):
    """
    Dependency to check if the current user is an admin (role_id=1).
    """
    if user.role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción (Solo Administradores)",
        )
    return user

def get_current_admin_or_teacher(user = Depends(get_current_user)):
    """
    Dependency to check if the current user is an admin (role_id=1) or teacher (role_id=3).
    """
    if user.role_id not in (1, 3):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción (Solo Administradores o Docentes)",
        )
    return user
