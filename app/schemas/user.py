from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import TypeDocumentIdentity

class UserBase(BaseModel):
    """
    Base schema for User with common fields.
    """
    name: str = Field(..., description="The user's first name")
    last_name: str = Field(..., description="The user's last name")
    email: str = Field(..., description="The user's email address") # Use EmailStr if email-validator is installed
    residential_address: Optional[str] = Field(None, description="The user's residential address")
    type_document_identity: TypeDocumentIdentity = Field(..., description="The type of identity document")
    document_identity: str = Field(..., description="The identity document number")
    school_id: int = Field(..., description="The ID of the school associated with the user")

class UserCreate(UserBase):
    """
    Schema for creating a new User.
    Password is required for creation.
    """
    password: str = Field(..., min_length=6, description="The user's password")

class UserUpdate(BaseModel):
    """
    Schema for updating an existing User.
    All fields are optional.
    """
    name: Optional[str] = Field(None, description="The user's first name")
    last_name: Optional[str] = Field(None, description="The user's last name")
    email: Optional[str] = Field(None, description="The user's email address") # Use EmailStr if email-validator is installed
    residential_address: Optional[str] = Field(None, description="The user's residential address")
    type_document_identity: Optional[TypeDocumentIdentity] = Field(None, description="The type of identity document")
    document_identity: Optional[str] = Field(None, description="The identity document number")
    school_id: Optional[int] = Field(None, description="The ID of the school associated with the user")
    password: Optional[str] = Field(None, min_length=6, description="The user's new password")

class UserResponse(UserBase):
    """
    Schema for User response.
    Includes ID and creation timestamp.
    """
    id: int
    normalized_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeacherPublicResponse(BaseModel):
    name: str
    last_name: str
    school_name: Optional[str] = None
