from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RoleBase(BaseModel):
    name: str = Field(..., description="The name of the role", max_length=50)

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the role", max_length=50)

class RoleResponse(RoleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
