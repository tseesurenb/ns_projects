"""
Pydantic schemas for authentication endpoints.
"""

import uuid
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    tenant_name: str  # creates a new tenant on registration


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tenant_id: uuid.UUID
    user_id: uuid.UUID


class RefreshRequest(BaseModel):
    refresh_token: str
