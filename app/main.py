from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from . import models, schemas, auth, database
from .database import get_db, get_redis
from .auth import get_current_user, create_tokens, revoke_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="1.0.0")
security = HTTPBearer()

@app.post("/register", response_model=schemas.UserResponse)
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    try:
        existing_user = db.query(models.User).filter(
            models.User.email == user_data.email
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован"
            )
        
        hashed_password = auth.get_password_hash(user_data.password)
        user = models.User(
            email=user_data.email,
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Зарегистрирован новый пользователь: {user.email}")
        return {"id": user.id, "email": user.email}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка регистрации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )

@app.post("/login", response_model=schemas.TokenResponse)
async def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Авторизация пользователя"""
    user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()
    
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Запись в историю входов
    login_history = models.LoginHistory(
        user_id=user.id,
        user_agent=login_data.user_agent or "Unknown",
        login_time=datetime.utcnow()
    )
    db.add(login_history)
    db.commit()
    
    tokens = create_tokens({"sub": user.email})
    
    logger.info(f"Успешный вход пользователя: {user.email}")
    return tokens

@app.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    refresh_data: schemas.RefreshTokenRequest,
    redis=Depends(get_redis)
):
    """Обновление access токена"""
    try:
        payload = auth.verify_refresh_token(refresh_data.refresh_token)
        if auth.is_token_revoked(refresh_data.refresh_token, redis):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен отозван"
            )
        
        new_tokens = create_tokens({"sub": payload["sub"]})
        
        # Отзываем старый refresh токен
        revoke_token(refresh_data.refresh_token, redis)
        
        return new_tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )

@app.put("/user/update", response_model=schemas.UserResponse)
async def update_user(
    update_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление данных пользователя"""
    try:
        if update_data.email:
            # Проверка уникальности email
            existing_user = db.query(models.User).filter(
                models.User.email == update_data.email,
                models.User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется"
                )
            current_user.email = update_data.email
        
        if update_data.password:
            current_user.hashed_password = auth.get_password_hash(update_data.password)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Обновлены данные пользователя: {current_user.email}")
        return {"id": current_user.id, "email": current_user.email}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления пользователя: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении данных"
        )

@app.get("/user/history", response_model=schemas.LoginHistoryList)
async def get_login_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение истории входов"""
    history = db.query(models.LoginHistory).filter(
        models.LoginHistory.user_id == current_user.id
    ).order_by(models.LoginHistory.login_time.desc()).all()
    
    return {"history": history}

@app.post("/logout")
async def logout(
    token: str = Depends(security),
    redis=Depends(get_redis)
):
    """Выход из системы"""
    try:
        payload = auth.verify_token(token.credentials)
        revoke_token(token.credentials, redis)
        
        logger.info(f"Пользователь вышел из системы: {payload['sub']}")
        return {"message": "Успешный выход из системы"}
        
    except Exception as e:
        logger.error(f"Ошибка выхода: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен"
        )