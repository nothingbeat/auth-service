from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    user_agent: Optional[str] = None

class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str

class LoginHistoryResponse(BaseModel):
    """Schema for login history item"""
    id: int
    user_agent: Optional[str]
    login_time: datetime

    class Config:
        from_attributes = True

class LoginHistoryList(BaseModel):
    """Schema for login history list"""
    history: List[LoginHistoryResponse]