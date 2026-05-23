from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.models.question import Question
from app.models.questionnaire import Questionnaire
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse
from app.repositories.question_repository import QuestionRepository
from app.utilities.jwt import get_current_user, get_current_admin_or_teacher

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[QuestionResponse])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve questions.
    """
    if getattr(current_user, "role_id", None) == 2:
        user_school_id = getattr(current_user, "school_id", None)
        if user_school_id is None:
            return []
        questions = (
            db.query(Question)
            .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
            .join(User, User.id == Questionnaire.teacher_id)
            .filter(Questionnaire.teacher_id.is_not(None), User.school_id == user_school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    elif getattr(current_user, "role_id", None) == 3:
        questions = (
            db.query(Question)
            .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
            .filter(Questionnaire.teacher_id == getattr(current_user, "id", None))
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        questions = QuestionRepository.get_all(db, skip=skip, limit=limit)
    return questions

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(question: QuestionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Create a new question.
    """
    try:
        if getattr(current_user, "role_id", None) == 3:
            questionnaire = (
                db.query(Questionnaire)
                .filter(Questionnaire.id == question.questionnaire_id)
                .first()
            )
            if questionnaire is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cuestionario especificado no existe.")
            if getattr(questionnaire, "teacher_id", None) != getattr(current_user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para crear preguntas en este cuestionario")
        return QuestionRepository.create(db=db, question_in=question)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "questionnaire_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cuestionario especificado no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear la pregunta."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the question: {str(e)}"
        )

@router.get("/{question_id}", response_model=QuestionResponse)
def read_question(question_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get question by ID.
    """
    db_question = QuestionRepository.get_by_id(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    if getattr(current_user, "role_id", None) == 2:
        user_school_id = getattr(current_user, "school_id", None)
        if user_school_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver esta pregunta")
        allowed = (
            db.query(Question.id)
            .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
            .join(User, User.id == Questionnaire.teacher_id)
            .filter(Question.id == question_id, Questionnaire.teacher_id.is_not(None), User.school_id == user_school_id)
            .first()
        )
        if allowed is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver esta pregunta")
    elif getattr(current_user, "role_id", None) == 3:
        allowed = (
            db.query(Question.id)
            .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
            .filter(Question.id == question_id, Questionnaire.teacher_id == getattr(current_user, "id", None))
            .first()
        )
        if allowed is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver esta pregunta")
    return db_question

@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Update a question.
    """
    try:
        if getattr(current_user, "role_id", None) == 3:
            existing = QuestionRepository.get_by_id(db, question_id=question_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Question not found")
            existing_questionnaire = (
                db.query(Questionnaire)
                .filter(Questionnaire.id == getattr(existing, "questionnaire_id", None))
                .first()
            )
            if existing_questionnaire is None or getattr(existing_questionnaire, "teacher_id", None) != getattr(current_user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para editar esta pregunta")

            if question.questionnaire_id is not None:
                target_questionnaire = (
                    db.query(Questionnaire)
                    .filter(Questionnaire.id == question.questionnaire_id)
                    .first()
                )
                if target_questionnaire is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cuestionario especificado no existe.")
                if getattr(target_questionnaire, "teacher_id", None) != getattr(current_user, "id", None):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para mover esta pregunta a otro cuestionario")

        db_question = QuestionRepository.update(db=db, question_id=question_id, question_in=question)
        if db_question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        return db_question
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "questionnaire_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cuestionario especificado no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar la pregunta."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the question: {str(e)}"
        )

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_or_teacher)):
    """
    Delete a question.
    """
    if getattr(current_user, "role_id", None) == 3:
        allowed = (
            db.query(Question.id)
            .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
            .filter(Question.id == question_id, Questionnaire.teacher_id == getattr(current_user, "id", None))
            .first()
        )
        if allowed is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para eliminar esta pregunta")
    success = QuestionRepository.delete(db=db, question_id=question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return None
