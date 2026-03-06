from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate

class QuestionRepository:
    """
    Repository class for performing database operations on the Question model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Question]:
        return db.query(Question).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, question_id: int) -> Optional[Question]:
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def create(db: Session, question_in: QuestionCreate) -> Question:
        db_question = Question(**question_in.model_dump())
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question

    @staticmethod
    def update(db: Session, question_id: int, question_in: QuestionUpdate) -> Optional[Question]:
        db_question = QuestionRepository.get_by_id(db, question_id)
        if not db_question:
            return None
        
        update_data = question_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_question, field, value)

        db.commit()
        db.refresh(db_question)
        return db_question

    @staticmethod
    def delete(db: Session, question_id: int) -> bool:
        db_question = QuestionRepository.get_by_id(db, question_id)
        if not db_question:
            return False
            
        db.delete(db_question)
        db.commit()
        return True
