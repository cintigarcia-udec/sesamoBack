from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.answer_option import AnswerOptionCreate, AnswerOptionUpdate, AnswerOptionResponse, AnswerOptionAdminResponse
from app.repositories.answer_option_repository import AnswerOptionRepository
from app.utilities.jwt import get_current_user, get_current_admin

router = APIRouter(
    prefix="/answer-options",
    tags=["answer-options"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[AnswerOptionAdminResponse], response_model_exclude_none=True)
def read_answer_options(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve answer options.
    """
    answer_options = AnswerOptionRepository.get_all(db, skip=skip, limit=limit)
    
    # Convert SQLAlchemy objects to Pydantic models
    result = [AnswerOptionAdminResponse.model_validate(option) for option in answer_options]
    
    # Hide is_correct for non-admins
    if current_user.role_id != 1:
        for option in result:
            option.is_correct = None
            
    return result

@router.post("/", response_model=AnswerOptionAdminResponse, status_code=status.HTTP_201_CREATED)
def create_answer_option(answer_option: AnswerOptionCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Create a new answer option.
    """
    try:
        return AnswerOptionRepository.create(db=db, answer_option_in=answer_option)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "question_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pregunta especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear la opción de respuesta."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the answer option: {str(e)}"
        )

@router.get("/{answer_option_id}", response_model=AnswerOptionAdminResponse, response_model_exclude_none=True)
def read_answer_option(answer_option_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get answer option by ID.
    """
    db_answer_option = AnswerOptionRepository.get_by_id(db, answer_option_id=answer_option_id)
    if db_answer_option is None:
        raise HTTPException(status_code=404, detail="Answer option not found")
    
    # Convert SQLAlchemy object to Pydantic model
    result = AnswerOptionAdminResponse.model_validate(db_answer_option)
    
    # Hide is_correct for non-admins
    if current_user.role_id != 1:
        result.is_correct = None
        
    return result

@router.patch("/{answer_option_id}", response_model=AnswerOptionAdminResponse)
def update_answer_option(answer_option_id: int, answer_option: AnswerOptionUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Update an answer option.
    """
    try:
        db_answer_option = AnswerOptionRepository.update(db=db, answer_option_id=answer_option_id, answer_option_in=answer_option)
        if db_answer_option is None:
            raise HTTPException(status_code=404, detail="Answer option not found")
        return db_answer_option
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "question_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pregunta especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar la opción de respuesta."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the answer option: {str(e)}"
        )

@router.delete("/{answer_option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_answer_option(answer_option_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Delete an answer option.
    """
    success = AnswerOptionRepository.delete(db=db, answer_option_id=answer_option_id)
    if not success:
        raise HTTPException(status_code=404, detail="Answer option not found")
    return None
