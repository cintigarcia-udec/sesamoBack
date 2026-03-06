from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.db import Base

class UserResponse(Base):
  """Class representing the User Response entity."""
  __tablename__ = "user_responses"

  id = Column("id", Integer, primary_key=True, index=True)
  user_id = Column("user_id", Integer, ForeignKey('users.id'))
  questionnaire_id = Column("questionnaire_id", Integer, ForeignKey('questionnaires.id'))
  score = Column("score", Float)
  answers = Column("answers", Text)
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  user = relationship("User", lazy='select')
  questionnaire = relationship("Questionnaire", lazy='select')

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "user_id": self.user_id,
      "questionnaire_id": self.questionnaire_id,
      "score": self.score,
      "answers": self.answers,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "user": self.user.to_dict() if self.user and hasattr(self.user, "to_dict") else None,
      "questionnaire": self.questionnaire.to_dict() if self.questionnaire and hasattr(self.questionnaire, "to_dict") else None,
    }
