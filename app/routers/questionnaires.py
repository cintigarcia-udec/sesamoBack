from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse
from app.repositories.questionnaire_repository import QuestionnaireRepository
from app.utilities.jwt import get_current_user, get_current_admin

router = APIRouter(
    prefix="/questionnaires",
    tags=["questionnaires"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[QuestionnaireResponse])
def read_questionnaires(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve questionnaires.
    """
    questionnaires = QuestionnaireRepository.get_all(db, skip=skip, limit=limit)
    return questionnaires

@router.post("/", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
def create_questionnaire(questionnaire: QuestionnaireCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Create a new questionnaire.
    """
    try:
        return QuestionnaireRepository.create(db=db, questionnaire_in=questionnaire)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "category_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La categoría especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear el cuestionario."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the questionnaire: {str(e)}"
        )

@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
def read_questionnaire(questionnaire_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get questionnaire by ID.
    """
    db_questionnaire = QuestionnaireRepository.get_by_id(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return db_questionnaire

@router.patch("/{questionnaire_id}", response_model=QuestionnaireResponse)
def update_questionnaire(questionnaire_id: int, questionnaire: QuestionnaireUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Update a questionnaire.
    """
    try:
        db_questionnaire = QuestionnaireRepository.update(db=db, questionnaire_id=questionnaire_id, questionnaire_in=questionnaire)
        if db_questionnaire is None:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        return db_questionnaire
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "category_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La categoría especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar el cuestionario."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the questionnaire: {str(e)}"
        )

@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Delete a questionnaire.
    """
    success = QuestionnaireRepository.delete(db=db, questionnaire_id=questionnaire_id)
    if not success:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return None
