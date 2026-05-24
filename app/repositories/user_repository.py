from typing import Any, List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from app.models.school import School
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserRepository:
    """
    Repository class for performing database operations on the User model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Retrieve all users with pagination.
        
        Args:
            db (Session): Database session.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            
        Returns:
            List[User]: List of users.
        """
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            db (Session): Database session.
            user_id (int): The ID of the user.
            
        Returns:
            Optional[User]: The user if found, else None.
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user by their email.
        
        Args:
            db (Session): Database session.
            email (str): The email of the user.
            
        Returns:
            Optional[User]: The user if found, else None.
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db (Session): Database session.
            user_in (UserCreate): The user data to create.
            
        Returns:
            User: The created user.
        """
        # Validate unique email
        User.validate_unique_fields(db, email=user_in.email)
        
        # Create new user instance
        db_user = User(
            name=user_in.name,
            last_name=user_in.last_name,
            email=user_in.email,
            normalized_email=user_in.email.upper(),
            residential_address=user_in.residential_address,
            type_document_identity=user_in.type_document_identity,
            document_identity=user_in.document_identity,
            role_id=2,
            school_id=user_in.school_id
        )
        
        # Set password (hashing is handled by the model method)
        db_user.set_password(user_in.password)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """
        Update an existing user.
        
        Args:
            db (Session): Database session.
            user_id (int): The ID of the user to update.
            user_in (UserUpdate): The user data to update.
            
        Returns:
            Optional[User]: The updated user if found, else None.
        """
        db_user = UserRepository.get_by_id(db, user_id)
        if not db_user:
            return None
            
        # Validate unique email if it's being updated
        if user_in.email and user_in.email != db_user.email:
            User.validate_unique_fields(db, email=user_in.email, user_id=user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        
        # Handle password update separately if present
        if "password" in update_data:
            password = update_data.pop("password")
            db_user.set_password(password)
            
        # Handle normalized_email if email is updated
        if "email" in update_data:
            update_data["normalized_email"] = update_data["email"].upper()

        # Update other fields
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            db (Session): Database session.
            user_id (int): The ID of the user to delete.
            
        Returns:
            bool: True if the user was deleted, False if not found.
        """
        db_user = UserRepository.get_by_id(db, user_id)
        if not db_user:
            return False
            
        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def get_teachers_public(
        db: Session,
        school_id: Optional[int] = None,
        teacher_user_id: Optional[int] = None,
    ) -> List[Tuple[str, str, Optional[str]]]:
        query = (
            db.query(User.name, User.last_name, School.name)
            .outerjoin(School, School.id == User.school_id)
            .filter(User.role_id == 3)
        )
        if teacher_user_id is not None:
            query = query.filter(User.id == teacher_user_id)
        if school_id is not None:
            query = query.filter(User.school_id == school_id)
        rows = query.order_by(User.last_name.asc(), User.name.asc()).all()
        return [
            (cast(str, r[0]), cast(str, r[1]), cast(Optional[str], r[2]))
            for r in cast(List[Any], rows)
        ]

    @staticmethod
    def get_students_by_school_id(db: Session, school_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            db.query(User)
            .filter(User.school_id == school_id, User.role_id == 2)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_student_by_id_and_school_id(db: Session, user_id: int, school_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.school_id == school_id, User.role_id == 2).first()
