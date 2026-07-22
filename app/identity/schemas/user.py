import re
import uuid
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str

    model_config = ConfigDict(from_attributes=True)

class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
