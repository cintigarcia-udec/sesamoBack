from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate

class SchoolRepository:
    """
    Repository class for performing database operations on the School model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[School]:
        return db.query(School).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, school_id: int) -> Optional[School]:
        return db.query(School).filter(School.id == school_id).first()

    @staticmethod
    def create(db: Session, school_in: SchoolCreate) -> School:
        db_school = School(**school_in.model_dump())
        db.add(db_school)
        db.commit()
        db.refresh(db_school)
        return db_school

    @staticmethod
    def update(db: Session, school_id: int, school_in: SchoolUpdate) -> Optional[School]:
        db_school = SchoolRepository.get_by_id(db, school_id)
        if not db_school:
            return None
        
        update_data = school_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_school, field, value)

        db.commit()
        db.refresh(db_school)
        return db_school

    @staticmethod
    def delete(db: Session, school_id: int) -> bool:
        db_school = SchoolRepository.get_by_id(db, school_id)
        if not db_school:
            return False
            
        db.delete(db_school)
        db.commit()
        return True
