from .schemas import TokenResponse
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
import redis
import logging

from .config import settings
from .database import get_db, get_redis
from . import models

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)

def create_tokens(data: dict) -> dict:
    """Создание access и refresh токенов"""
    to_encode = data.copy()
    
    # Access token (короткоживущий)
    access_expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": access_expire, "type": "access"})
    access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Refresh token (долгоживущий)
    refresh_expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": refresh_expire, "type": "refresh"})
    refresh_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def verify_token(token: str) -> dict:
    """Верификация токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Ошибка верификации токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )

def verify_refresh_token(token: str) -> dict:
    """Верификация refresh токена"""
    payload = verify_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена"
        )
    return payload

async def get_current_user(
    token: str = Depends(security),
    db = Depends(get_db),
    redis_client = Depends(get_redis)
) -> models.User:
    """Получение текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные"
    )
    
    try:
        payload = verify_token(token.credentials)
        
        # Проверка отозванного токена
        if is_token_revoked(token.credentials, redis_client):
            raise credentials_exception
            
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user

def revoke_token(token: str, redis_client: redis.Redis) -> None:
    """Добавление токена в черный список"""
    try:
        payload = verify_token(token)
        expire_timestamp = payload.get("exp")
        if expire_timestamp:
            ttl = expire_timestamp - int(datetime.utcnow().timestamp())
            if ttl > 0:
                redis_client.setex(f"revoked:{token}", ttl, "revoked")
    except Exception as e:
        logger.error(f"Ошибка отзыва токена: {str(e)}")

def is_token_revoked(token: str, redis_client: redis.Redis) -> bool:
    """Проверка отозванного токена"""
    return redis_client.exists(f"revoked:{token}") > 0