import enum
import bcrypt
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.encription import verify_password
from app.utilities.db import Base

class TypeDocumentIdentity(str, enum.Enum):
  CC = "cc"
  CE = "ce"
  TI = "ti"
  PASSPORT = "passport"

class User(Base):
  """Class representing the User entity."""
  __tablename__ = 'users'

  id = Column("id", Integer, primary_key=True, index=True)
  name = Column("name", String(255))
  last_name = Column("last_name", String(255))
  email = Column("email", String(255), unique=True, index=True)
  normalized_email = Column("normalized_email", String(255), unique=True, index=True)
  residential_address = Column("residential_address", String(255))
  type_document_identity = Column(Enum(TypeDocumentIdentity), nullable=False)
  document_identity = Column("document_identity", String(50))
  password = Column("password", String(255), nullable=True)
  role_id = Column("role_id", Integer, ForeignKey('roles.id'), default=2)
  school_id = Column("school_id", Integer, ForeignKey('schools.id'))
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())


  role = relationship("Role", lazy='select')
  school = relationship("School", lazy='select')

  def set_password(self, password: str):
    """
    Encrypts the password before saving it.

    Args:
      password (str): The password to be encrypted.

    Returns:
      None
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(
      password.encode('utf-8'),
      salt
    )
    self.password = hashed.decode('utf-8')

  def check_password(self, password: str) -> bool:
    """
    Verifies if the provided password is correct.

    Args:
      password (str): The password to be verified.

    Returns:
      bool: True if the password is correct, False otherwise.
    """
    return verify_password(password, self.password)
  
  @staticmethod
  def validate_unique_fields(db, email: str = None, user_id: int = None):
    """Valida que email sea único si no es None"""
    if email:
      query = db.query(User).filter(User.email == email)
      
      if user_id:
        query = query.filter(User.id != user_id)
      
      if query.first():
        raise ValueError("El email ya está en uso")
      
  def to_dict(self) -> dict:
    """
    Returns a dictionary representation of the User instance,
    excluding sensitive information like password and password_history.
    """
    return {
      "id": self.id,
      "name": self.name,
      "email": self.email,
      "normalized_email": self.normalized_email,
      "residential_address": self.residential_address,
      "type_document_identity": self.type_document_identity,
      "document_identity": self.document_identity,
      "role_id": self.role_id,
      "school_id": self.school_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "role": self.role.to_dict() if self.role and hasattr(self.role, "to_dict") else None,
      "school": self.school.to_dict() if self.school and hasattr(self.school, "to_dict") else None
    }
