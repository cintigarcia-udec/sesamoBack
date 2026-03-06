from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class QuestionBase(BaseModel):
    question_text: str = Field(..., description="The text of the question")
    questionnaire_id: int = Field(..., description="The ID of the questionnaire this question belongs to")

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, description="The text of the question")
    questionnaire_id: Optional[int] = Field(None, description="The ID of the questionnaire this question belongs to")

class QuestionResponse(QuestionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
