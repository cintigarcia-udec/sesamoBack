from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    """
    Schema for login request.
    """
    email: str = Field(..., description="User email") # Use EmailStr if available
    password: str = Field(..., description="User password")

class Token(BaseModel):
    """
    Schema for JWT token response.
    """
    access_token: str
    token_type: str
