from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse
from app.repositories.question_repository import QuestionRepository
from app.utilities.jwt import get_current_user, get_current_admin

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
    questions = QuestionRepository.get_all(db, skip=skip, limit=limit)
    return questions

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(question: QuestionCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Create a new question.
    """
    try:
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
    return db_question

@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Update a question.
    """
    try:
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
def delete_question(question_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Delete a question.
    """
    success = QuestionRepository.delete(db=db, question_id=question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return None
