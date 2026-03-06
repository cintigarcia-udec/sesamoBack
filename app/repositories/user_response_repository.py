from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user_response import UserResponse
from app.schemas.user_response import UserResponseCreate, UserResponseUpdate

class UserResponseRepository:
    """
    Repository class for performing database operations on the UserResponse model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        return db.query(UserResponse).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, user_response_id: int) -> Optional[UserResponse]:
        return db.query(UserResponse).filter(UserResponse.id == user_response_id).first()

    @staticmethod
    def create(db: Session, user_response_in: UserResponseCreate) -> UserResponse:
        db_user_response = UserResponse(**user_response_in.model_dump())
        db.add(db_user_response)
        db.commit()
        db.refresh(db_user_response)
        return db_user_response

    @staticmethod
    def update(db: Session, user_response_id: int, user_response_in: UserResponseUpdate) -> Optional[UserResponse]:
        db_user_response = UserResponseRepository.get_by_id(db, user_response_id)
        if not db_user_response:
            return None
        
        update_data = user_response_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user_response, field, value)

        db.commit()
        db.refresh(db_user_response)
        return db_user_response

    @staticmethod
    def delete(db: Session, user_response_id: int) -> bool:
        db_user_response = UserResponseRepository.get_by_id(db, user_response_id)
        if not db_user_response:
            return False
            
        db.delete(db_user_response)
        db.commit()
        return True
