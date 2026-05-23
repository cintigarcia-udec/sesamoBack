from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.answer_option import AnswerOption
from app.schemas.answer_option import AnswerOptionCreate, AnswerOptionUpdate

class AnswerOptionRepository:
    """
    Repository class for performing database operations on the AnswerOption model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[AnswerOption]:
        return db.query(AnswerOption).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_by_question_id(db: Session, question_id: int, skip: int = 0, limit: int = 100) -> List[AnswerOption]:
        return (
            db.query(AnswerOption)
            .filter(AnswerOption.question_id == question_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, answer_option_id: int) -> Optional[AnswerOption]:
        return db.query(AnswerOption).filter(AnswerOption.id == answer_option_id).first()

    @staticmethod
    def create(db: Session, answer_option_in: AnswerOptionCreate) -> AnswerOption:
        db_answer_option = AnswerOption(**answer_option_in.model_dump())
        db.add(db_answer_option)
        db.commit()
        db.refresh(db_answer_option)
        return db_answer_option

    @staticmethod
    def update(db: Session, answer_option_id: int, answer_option_in: AnswerOptionUpdate) -> Optional[AnswerOption]:
        db_answer_option = AnswerOptionRepository.get_by_id(db, answer_option_id)
        if not db_answer_option:
            return None
        
        update_data = answer_option_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_answer_option, field, value)

        db.commit()
        db.refresh(db_answer_option)
        return db_answer_option

    @staticmethod
    def delete(db: Session, answer_option_id: int) -> bool:
        db_answer_option = AnswerOptionRepository.get_by_id(db, answer_option_id)
        if not db_answer_option:
            return False
            
        db.delete(db_answer_option)
        db.commit()
        return True
