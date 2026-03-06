from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class SchoolBase(BaseModel):
    name: str = Field(..., description="The name of the school")

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the school")

class SchoolResponse(SchoolBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
