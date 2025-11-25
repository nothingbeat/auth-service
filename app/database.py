from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from .config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Redis setup
def get_redis_client():
    """Get Redis client connection"""
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Dependency for database session
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for Redis
def get_redis():
    """Redis client dependency"""
    redis_client = get_redis_client()
    try:
        yield redis_client
    finally:
        redis_client.close()