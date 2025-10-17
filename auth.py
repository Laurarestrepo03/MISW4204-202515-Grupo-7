from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
import jwt
import bcrypt
import models
from database import SessionLocal

# Configuración
SECRET_KEY = "tu_clave_secreta_super_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3600  # 60 minutos

# Security - auto_error=False para manejar nosotros el error 401
security = HTTPBearer(auto_error=False)


# ============= MODELOS PYDANTIC =============

class UserRegister(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "city": "Bogotá",
                "country": "Colombia"
            }
        }
    )
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=72)
    password2: str = Field(..., min_length=8, max_length=72)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)

    @field_validator('password2')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password1' in info.data and v != info.data['password1']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de validación (email duplicado, contraseñas no coinciden)."
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "StrongPass123"
            }
        }
    )


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    city: str
    country: str


# ============= FUNCIONES AUXILIARES =============

def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str):
    """Obtiene un usuario de la base de datos por email"""
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    """Autentica un usuario"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: next(get_db_for_auth()))
) -> models.User:
    """
    Dependencia para obtener el usuario actual desde el token JWT
    Uso: current_user: models.User = Depends(get_current_user)
    """
    # Si no hay credenciales (no se envió header Authorization)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_db_for_auth():
    """Helper para obtener sesión de BD en dependencias de autenticación"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
