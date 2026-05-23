from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse
from app.repositories.questionnaire_repository import QuestionnaireRepository
from app.models.questionnaire import Questionnaire
from app.models.user import User
from app.utilities.jwt import get_current_user, get_current_admin, get_current_admin_or_teacher

router = APIRouter(
    prefix="/questionnaires",
    tags=["questionnaires"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[QuestionnaireResponse])
def read_questionnaires(category_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve questionnaires.
    """
    if getattr(current_user, "role_id", None) == 2:
        user_school_id = getattr(current_user, "school_id", None)
        if user_school_id is None:
            return []
        query = (
            db.query(Questionnaire)
            .join(User, User.id == Questionnaire.teacher_id)
            .filter(Questionnaire.teacher_id.is_not(None), User.school_id == user_school_id)
        )
        if category_id is not None:
            query = query.filter(Questionnaire.category_id == category_id)
        questionnaires = query.offset(skip).limit(limit).all()
    elif getattr(current_user, "role_id", None) == 3:
        query = db.query(Questionnaire).filter(Questionnaire.teacher_id == getattr(current_user, "id", None))
        if category_id is not None:
            query = query.filter(Questionnaire.category_id == category_id)
        questionnaires = query.offset(skip).limit(limit).all()
    else:
        if category_id is None:
            questionnaires = QuestionnaireRepository.get_all(db, skip=skip, limit=limit)
        else:
            questionnaires = (
                db.query(Questionnaire)
                .filter(Questionnaire.category_id == category_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
    return questionnaires

@router.post("/", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
def create_questionnaire(questionnaire: QuestionnaireCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Create a new questionnaire.
    """
    try:
        if getattr(current_user, "role_id", None) == 3:
            if questionnaire.teacher_id is not None and questionnaire.teacher_id != getattr(current_user, "id", None):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para asignar otro docente al cuestionario",
                )
            questionnaire = questionnaire.model_copy(update={"teacher_id": getattr(current_user, "id", None)})
        return QuestionnaireRepository.create(db=db, questionnaire_in=questionnaire)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
    if getattr(current_user, "role_id", None) == 3 and getattr(db_questionnaire, "teacher_id", None) != getattr(current_user, "id", None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver este cuestionario")
    return db_questionnaire

@router.patch("/{questionnaire_id}", response_model=QuestionnaireResponse)
def update_questionnaire(questionnaire_id: int, questionnaire: QuestionnaireUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Update a questionnaire.
    """
    try:
        if getattr(current_user, "role_id", None) == 3:
            existing = QuestionnaireRepository.get_by_id(db, questionnaire_id=questionnaire_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Questionnaire not found")
            if getattr(existing, "teacher_id", None) != getattr(current_user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para editar este cuestionario")
            if questionnaire.teacher_id is not None and questionnaire.teacher_id != getattr(current_user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para asignar otro docente al cuestionario")
            questionnaire = questionnaire.model_copy(update={"teacher_id": getattr(current_user, "id", None)})

        db_questionnaire = QuestionnaireRepository.update(db=db, questionnaire_id=questionnaire_id, questionnaire_in=questionnaire)
        if db_questionnaire is None:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        return db_questionnaire
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Delete a questionnaire.
    """
    if getattr(current_user, "role_id", None) == 3:
        existing = QuestionnaireRepository.get_by_id(db, questionnaire_id=questionnaire_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        if getattr(existing, "teacher_id", None) != getattr(current_user, "id", None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para eliminar este cuestionario")
    success = QuestionnaireRepository.delete(db=db, questionnaire_id=questionnaire_id)
    if not success:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return None
