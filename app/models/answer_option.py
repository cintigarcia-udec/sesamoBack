from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, TEXT, CHAR, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utilities.db import Base

class AnswerOption(Base):
  """Class representing the Answer Option entity."""
  __tablename__ = 'answer_options'

  id = Column("id", Integer, primary_key=True, index=True)
  answer = Column("answer", TEXT)
  option_key = Column("option_key", CHAR)
  is_correct = Column("is_correct", Boolean)
  question_id = Column("question_id", Integer, ForeignKey('questions.id'))
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  question = relationship("Question", lazy='select')

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "answer": self.answer,
      "option_key": self.option_key,
      "is_correct": self.is_correct,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "question": self.question.to_dict() if self.question and hasattr(self.question, "to_dict") else None,
    }
