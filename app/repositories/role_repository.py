from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate

class RoleRepository:
    """
    Repository class for performing database operations on the Role model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        return db.query(Role).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, role_id: int) -> Optional[Role]:
        return db.query(Role).filter(Role.id == role_id).first()

    @staticmethod
    def create(db: Session, role_in: RoleCreate) -> Role:
        db_role = Role(**role_in.model_dump())
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role

    @staticmethod
    def update(db: Session, role_id: int, role_in: RoleUpdate) -> Optional[Role]:
        db_role = RoleRepository.get_by_id(db, role_id)
        if not db_role:
            return None
        
        update_data = role_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)

        db.commit()
        db.refresh(db_role)
        return db_role

    @staticmethod
    def delete(db: Session, role_id: int) -> bool:
        db_role = RoleRepository.get_by_id(db, role_id)
        if not db_role:
            return False
            
        db.delete(db_role)
        db.commit()
        return True
