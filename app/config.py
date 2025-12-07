from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Database 
    DATABASE_URL: str = "postgresql+psycopg2://user:password@db:5432/auth_db"
    REDIS_URL: str = "redis://redis:6379"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Application
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()