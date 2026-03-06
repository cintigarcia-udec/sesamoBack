from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.db import Base

class Questionnaire(Base):
  """Class representing the Questionnarie entity."""
  __tablename__ = 'questionnaires'

  id = Column("id", Integer, primary_key=True, index=True)
  questionnaire_number = Column("questionnaire_number", Integer, nullable=False)
  category_id = Column("category_id", Integer, ForeignKey('categories.id'))
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  category = relationship("Category", lazy='select')

  @property
  def category_name(self):
    return self.category.name if self.category else None

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "questionnaire_number": self.questionnaire_number,
      "category_id": self.category_id,
      "category_name": self.category.name if self.category else None,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "category": self.category.to_dict() if self.category and hasattr(self.category, "to_dict") else None,
    }