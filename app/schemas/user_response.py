from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, ConfigDict, Field, Json

class UserResponseBase(BaseModel):
    user_id: int = Field(..., description="The ID of the user who submitted the response")
    questionnaire_id: int = Field(..., description="The ID of the questionnaire")
    score: float = Field(..., description="The score obtained")
    answers: str = Field(..., description="The answers provided by the user (stored as text/JSON)")
    duration_seconds: Optional[int] = Field(None, description="Tiempo total (en segundos) invertido en el cuestionario")

class UserResponseCreate(BaseModel):
    user_id: int = Field(..., description="The ID of the user who submitted the response")
    questionnaire_id: int = Field(..., description="The ID of the questionnaire")
    answers: Union[
        Dict[str, Any],
        List[Any],
        Json[Dict[str, Any]],
        Json[List[Any]],
    ] = Field(..., description="The answers provided by the user")
    duration_seconds: Optional[int] = Field(None, description="Tiempo total (en segundos) invertido en el cuestionario")

class UserResponseUpdate(BaseModel):
    user_id: Optional[int] = Field(None, description="The ID of the user who submitted the response")
    questionnaire_id: Optional[int] = Field(None, description="The ID of the questionnaire")
    answers: Optional[Union[
        Dict[str, Any],
        List[Any],
        Json[Dict[str, Any]],
        Json[List[Any]],
    ]] = Field(None, description="The answers provided by the user")
    duration_seconds: Optional[int] = Field(None, description="Tiempo total (en segundos) invertido en el cuestionario")

class UserResponseResponse(UserResponseBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
