import enum
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.db import Base

class QuestionnaireDifficulty(str, enum.Enum):
  EASY = "easy"
  MEDIUM = "medium"
  HARD = "hard"

class Questionnaire(Base):
  """Class representing the Questionnarie entity."""
  __tablename__ = 'questionnaires'

  id = Column("id", Integer, primary_key=True, index=True)
  questionnaire_number = Column("questionnaire_number", Integer, nullable=False)
  category_id = Column("category_id", Integer, ForeignKey('categories.id'))
  estimated_duration_minutes = Column("estimated_duration_minutes", Integer, nullable=True)
  difficulty = Column(Enum(QuestionnaireDifficulty), nullable=True)
  teacher_id = Column("teacher_id", Integer, ForeignKey('users.id'), nullable=True)
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  category = relationship("Category", lazy='select')
  teacher = relationship("User", foreign_keys=[teacher_id], lazy='select')

  @property
  def category_name(self):
    return self.category.name if self.category else None

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "questionnaire_number": self.questionnaire_number,
      "category_id": self.category_id,
      "category_name": self.category.name if self.category else None,
      "estimated_duration_minutes": self.estimated_duration_minutes,
      "difficulty": self.difficulty.value if self.difficulty is not None else None,
      "teacher_id": self.teacher_id,
      "created_at": self.created_at.isoformat() if self.created_at is not None else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
      "category": self.category.to_dict() if self.category and hasattr(self.category, "to_dict") else None,
    }
