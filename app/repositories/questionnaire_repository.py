from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.questionnaire import Questionnaire
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate

class QuestionnaireRepository:
    """
    Repository class for performing database operations on the Questionnaire model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Questionnaire]:
        return db.query(Questionnaire).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, questionnaire_id: int) -> Optional[Questionnaire]:
        return db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()

    @staticmethod
    def create(db: Session, questionnaire_in: QuestionnaireCreate) -> Questionnaire:
        db_questionnaire = Questionnaire(**questionnaire_in.model_dump())
        db.add(db_questionnaire)
        db.commit()
        db.refresh(db_questionnaire)
        return db_questionnaire

    @staticmethod
    def update(db: Session, questionnaire_id: int, questionnaire_in: QuestionnaireUpdate) -> Optional[Questionnaire]:
        db_questionnaire = QuestionnaireRepository.get_by_id(db, questionnaire_id)
        if not db_questionnaire:
            return None
        
        update_data = questionnaire_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_questionnaire, field, value)

        db.commit()
        db.refresh(db_questionnaire)
        return db_questionnaire

    @staticmethod
    def delete(db: Session, questionnaire_id: int) -> bool:
        db_questionnaire = QuestionnaireRepository.get_by_id(db, questionnaire_id)
        if not db_questionnaire:
            return False
            
        db.delete(db_questionnaire)
        db.commit()
        return True
