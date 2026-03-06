from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.db import Base

class Question(Base):
  """Class representing the Question entity."""
  __tablename__ = "questions"

  id = Column("id", Integer, primary_key=True, index=True)
  question_text = Column("question_text", TEXT)
  questionnaire_id = Column("questionnaire_id", Integer, ForeignKey('questionnaires.id'))
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  questionnaire = relationship("Questionnaire", lazy='select')

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "question_text": self.question_text,
      "questionnaire_id": self.questionnaire_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "questionnaire": self.questionnaire.to_dict() if self.questionnaire and hasattr(self.questionnaire, "to_dict") else None,
    }
