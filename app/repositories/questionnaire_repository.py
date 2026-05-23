from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.questionnaire import Questionnaire
from app.models.user import User
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
        payload = questionnaire_in.model_dump()
        teacher_id = payload.get("teacher_id")
        if teacher_id is not None:
            teacher = db.query(User).filter(User.id == teacher_id).first()
            if teacher is None:
                raise ValueError("El docente asignado no existe.")
            if getattr(teacher, "role_id", None) != 3:
                raise ValueError("El usuario asignado no es docente (role_id=3).")

        estimated_duration_minutes = payload.get("estimated_duration_minutes")
        if estimated_duration_minutes is not None and int(estimated_duration_minutes) < 0:
            raise ValueError("La duración estimada no puede ser negativa.")

        db_questionnaire = Questionnaire(**payload)
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
        if "teacher_id" in update_data and update_data["teacher_id"] is not None:
            teacher = db.query(User).filter(User.id == update_data["teacher_id"]).first()
            if teacher is None:
                raise ValueError("El docente asignado no existe.")
            if getattr(teacher, "role_id", None) != 3:
                raise ValueError("El usuario asignado no es docente (role_id=3).")

        if "estimated_duration_minutes" in update_data and update_data["estimated_duration_minutes"] is not None:
            if int(update_data["estimated_duration_minutes"]) < 0:
                raise ValueError("La duración estimada no puede ser negativa.")

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
