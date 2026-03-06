from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AnswerOptionBase(BaseModel):
    answer: str = Field(..., description="The text of the answer option")
    option_key: str = Field(..., description="The key of the option (e.g., A, B, C)", max_length=1)
    question_id: int = Field(..., description="The ID of the question this option belongs to")

class AnswerOptionCreate(AnswerOptionBase):
    is_correct: bool = Field(..., description="Whether this is the correct answer")

class AnswerOptionUpdate(BaseModel):
    answer: Optional[str] = Field(None, description="The text of the answer option")
    option_key: Optional[str] = Field(None, description="The key of the option (e.g., A, B, C)", max_length=1)
    is_correct: Optional[bool] = Field(None, description="Whether this is the correct answer")
    question_id: Optional[int] = Field(None, description="The ID of the question this option belongs to")

class AnswerOptionResponse(AnswerOptionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AnswerOptionAdminResponse(AnswerOptionResponse):
    """
    Schema for Answer Option response including sensitive fields (is_correct).
    Only for Admins.
    """
    is_correct: Optional[bool] = None
