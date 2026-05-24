from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.models.user import User
from app.models.user_response import UserResponse as UserResponseModel
from app.schemas.user_response import UserResponseCreate, UserResponseUpdate, UserResponseResponse
from app.repositories.user_response_repository import UserResponseRepository
from app.utilities.jwt import get_current_user, get_current_admin, get_current_admin_or_teacher

router = APIRouter(
    prefix="/user-responses",
    tags=["user-responses"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[UserResponseResponse])
def read_user_responses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Retrieve user responses.
    """
    if getattr(current_user, "role_id", None) == 3:
        school_id = getattr(current_user, "school_id", None)
        if school_id is None:
            return []
        user_responses = (
            db.query(UserResponseModel)
            .join(User, User.id == UserResponseModel.user_id)
            .filter(User.school_id == school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        user_responses = UserResponseRepository.get_all(db, skip=skip, limit=limit)
    return user_responses

@router.post("/", response_model=UserResponseResponse, status_code=status.HTTP_201_CREATED)
def create_user_response(user_response: UserResponseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a new user response.
    """
    try:
        return UserResponseRepository.create(db=db, user_response_in=user_response)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "user_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario especificado no existe."
            )
        if "questionnaire_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cuestionario especificado no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear la respuesta de usuario."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the user response: {str(e)}"
        )

@router.get("/{user_response_id}", response_model=UserResponseResponse)
def read_user_response(user_response_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get user response by ID.
    """
    db_user_response = UserResponseRepository.get_by_id(db, user_response_id=user_response_id)
    if db_user_response is None:
        raise HTTPException(status_code=404, detail="User response not found")
    return db_user_response

@router.patch("/{user_response_id}", response_model=UserResponseResponse)
def update_user_response(user_response_id: int, user_response: UserResponseUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Update a user response.
    """
    try:
        db_user_response = UserResponseRepository.update(db=db, user_response_id=user_response_id, user_response_in=user_response)
        if db_user_response is None:
            raise HTTPException(status_code=404, detail="User response not found")
        return db_user_response
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "user_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario especificado no existe."
            )
        if "questionnaire_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cuestionario especificado no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar la respuesta de usuario."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the user response: {str(e)}"
        )

@router.delete("/{user_response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_response(user_response_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Delete a user response.
    """
    success = UserResponseRepository.delete(db=db, user_response_id=user_response_id)
    if not success:
        raise HTTPException(status_code=404, detail="User response not found")
    return None
