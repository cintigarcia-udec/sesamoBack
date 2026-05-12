from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from app.repositories.user_repository import UserRepository
from app.utilities.jwt import create_access_token, exp_to_datetime, get_current_user, get_token_hash, security, verify_token
from app.repositories.token_blacklist_repository import TokenBlacklistRepository

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (Student).
    """
    try:
        # Force role_id to 2 (Student) is already handled in UserRepository.create default
        # But we can enforce it here or let the repository handle it.
        # The schema doesn't require role_id, and repository defaults to 2.
        
        return UserRepository.create(db=db, user_in=user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "users.email" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado."
            )
        if "school_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La escuela especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while registering the user: {str(e)}"
        )

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user with email and password and return JWT token.
    """
    try:
        user = UserRepository.get_by_email(db, email=login_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas (Usuario o Contraseña incorrecta)"
            )
        
        if not user.check_password(login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas (Usuario o Contraseña incorrecta)"
            )
        
        # Create JWT token with user info
        user_data = {
            "sub": user.email,
            "id": user.id,
            "name": user.name,
            "last_name": user.last_name,
            "role_id": user.role_id,
            "school_id": user.school_id,
            "school_name": user.school.name if getattr(user, "school", None) else None
        }
        access_token = create_access_token(data=user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except ValueError as e:
        # Handle bcrypt limitation (password longer than 72 bytes)
        if "password cannot be longer than 72 bytes" in str(e):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas (Usuario o Contraseña incorrecta)"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    credentials=Depends(security),
):
    token = credentials.credentials
    payload = verify_token(token)
    token_hash = get_token_hash(token)
    expires_at = exp_to_datetime(payload.get("exp"))
    TokenBlacklistRepository.add(db, token_hash=token_hash, user_id=getattr(user, "id", None), expires_at=expires_at)
    return {"message": "Logout exitoso"}
