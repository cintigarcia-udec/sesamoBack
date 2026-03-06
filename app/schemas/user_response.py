from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class UserResponseBase(BaseModel):
    user_id: int = Field(..., description="The ID of the user who submitted the response")
    questionnaire_id: int = Field(..., description="The ID of the questionnaire")
    score: float = Field(..., description="The score obtained")
    answers: str = Field(..., description="The answers provided by the user (stored as text/JSON)")

class UserResponseCreate(UserResponseBase):
    pass

class UserResponseUpdate(BaseModel):
    user_id: Optional[int] = Field(None, description="The ID of the user who submitted the response")
    questionnaire_id: Optional[int] = Field(None, description="The ID of the questionnaire")
    score: Optional[float] = Field(None, description="The score obtained")
    answers: Optional[str] = Field(None, description="The answers provided by the user (stored as text/JSON)")

class UserResponseResponse(UserResponseBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
