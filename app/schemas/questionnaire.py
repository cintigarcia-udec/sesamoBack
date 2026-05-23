from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class QuestionnaireBase(BaseModel):
    questionnaire_number: int = Field(..., description="The number of the questionnaire")
    category_id: int = Field(..., description="The ID of the category associated with the questionnaire")
    estimated_duration_minutes: Optional[int] = Field(None, ge=0, description="Duración estimada (minutos)")
    difficulty: Optional[str] = Field(None, max_length=50, description="Dificultad (ej: Fácil, Media, Difícil)")
    teacher_id: Optional[int] = Field(None, description="ID del docente asignado (role_id=3)")

class QuestionnaireCreate(QuestionnaireBase):
    pass

class QuestionnaireUpdate(BaseModel):
    questionnaire_number: Optional[int] = Field(None, description="The number of the questionnaire")
    category_id: Optional[int] = Field(None, description="The ID of the category associated with the questionnaire")
    estimated_duration_minutes: Optional[int] = Field(None, ge=0, description="Duración estimada (minutos)")
    difficulty: Optional[str] = Field(None, max_length=50, description="Dificultad (ej: Fácil, Media, Difícil)")
    teacher_id: Optional[int] = Field(None, description="ID del docente asignado (role_id=3)")

class QuestionnaireResponse(QuestionnaireBase):
    id: int
    category_name: Optional[str] = Field(None, description="The name of the category")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
