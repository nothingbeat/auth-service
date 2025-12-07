from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    login_history = relationship("LoginHistory", back_populates="user")

class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_agent = Column(Text)
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="login_history")