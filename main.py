from fastapi import FastAPI, UploadFile, Form, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from moviepy import *
from typing import Annotated
from pathlib import Path
from database import engine, SessionLocal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from tasks import process_video
import models
import shutil
import os
import auth

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"Hello":"World"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# 1. Carga de video 
@app.post("/api/videos/upload")
def upload_video(
    video_file: Annotated[UploadFile, Form()], 
    title: Annotated[str, Form()], 
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user)
):
    
    four_hundred_error = JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, 
                            content = {"message": "Error en el archivo (tipo o tamaño inválido)."})

    if video_file.content_type != "video/mp4":
        return four_hundred_error

    # Se guarda el video original para procesarlo
    upload_dir = Path("original_videos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = video_file.filename.replace(" ", "_")
    file_location = upload_dir / filename

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        video_path = "original_videos/"+filename
        video = VideoFileClip(video_path)
        duration = video.duration
        file_size = os.path.getsize(video_path) / (1024*1024)
        if duration < 20 or duration > 60 or file_size > 100:
            video.close()
            os.remove(video_path)
            return four_hundred_error
        video_id = add_uploaded_video(title, datetime.now(), current_user.user_id, db)
        result = process_video.delay(video_path, title, video_id)
        add_task_id(video_id, result.id, db)
        return JSONResponse(status_code = status.HTTP_201_CREATED, 
                            content = {"message": "Video subido correctamente. Procesamiento en curso",
                            "task_id": result.id}) 
    except Exception as e:
        return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content = {"message": f"Hubo un error subiendo el archivo, por favor intentar de nuevo. Error: {e}"})
    finally:
        video_file.file.close()

def add_uploaded_video(title: str, uploaded_at: datetime, user_id: int, db: db_dependency):
    original_url = "https://anb.com/uploads/"+title.replace(" ", "_")+".mp4"
    db_video = models.Video(title=title, status=models.VideoStatus.UPLOADED, uploaded_at=uploaded_at, 
                            processed_at=None, original_url=original_url, processed_url=None, user_id=user_id)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    video_id = db_video.video_id
    return video_id

def add_task_id(video_id: int, task_id: int, db: db_dependency):
    video = db.get(models.Video, video_id)
    if not video:
        pass
    else:
        video.task_id = task_id
    db.commit()

# TODO: Añadir autenticacion para solo ver videos propios

# 2. Consultar mis videos
@app.get("/api/videos")
def get_videos_uploaded(
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Lista todos los videos del usuario autenticado
    Requiere autenticación mediante token JWT
    """
    videos = db.query(models.Video).filter(models.Video.user_id == current_user.user_id).all()
    
    videos_response = []
    for video in videos:
        videos_response.append({
            "video_id": video.video_id,
            "title": video.title,
            "status": video.status.value,
            "uploaded_at": video.uploaded_at.isoformat() if video.uploaded_at else None,
            "processed_at": video.processed_at.isoformat() if video.processed_at else None,
            "original_url": video.original_url,
            "processed_url": video.processed_url,
            "votes": video.votes
        })
    
    return {
        "videos": videos_response,
        "total": len(videos_response)
    }

# 3. Consultar detalle de un video especifico
@app.get("/api/videos/{video_id}")
def get_video(
    video_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Obtiene el detalle de un video específico
    Solo permite ver videos del usuario autenticado
    """
    # Primero verificar si el video existe
    video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video no encontrado"
        )
    
    # Luego verificar si pertenece al usuario actual
    if video.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este video"
        )
    
    return {
        "video_id": video.video_id,
        "title": video.title,
        "status": video.status.value,
        "uploaded_at": video.uploaded_at.isoformat() if video.uploaded_at else None,
        "processed_at": video.processed_at.isoformat() if video.processed_at else None,
        "original_url": video.original_url,
        "processed_url": video.processed_url,
        "votes": video.votes,
        "user": {
            "email": current_user.email,
            "name": f"{current_user.first_name} {current_user.last_name}"
        }
    }
def get_video(video_id: int):
    return None

# 4. Eliminar video subido
@app.delete("/api/videos/{video_id}")
def delete_video(
    video_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Elimina un video del usuario autenticado
    Solo permite eliminar videos propios
    """
    # Primero verificar si el video existe
    video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video no encontrado"
        )
    
    # Luego verificar si pertenece al usuario actual
    if video.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este video"
        )
    
    # Eliminar archivos físicos si existen
    try:
        # Eliminar video original
        original_path = f"original_videos/{video.title}.mp4"
        if os.path.exists(original_path):
            os.remove(original_path)
        
        # Eliminar video procesado
        processed_path = f"processed_videos/{video.title}.mp4"
        if os.path.exists(processed_path):
            os.remove(processed_path)
    except Exception as e:
        # Continuar aunque falle la eliminación de archivos
        pass
    
    # Eliminar registro de la BD
    db.delete(video)
    db.commit()
    
    return {
        "message": "Video eliminado exitosamente",
        "video_id": video_id
    }

# Obtener el ranking de jugadores por votos
@app.get("/api/public/ranking")
def get_ranking(db: db_dependency, page: int = 0, page_size: int = 10, name: str = None, city: str = None):
    conditions = []
    if name:
        conditions.append(or_(models.Player.first_name.ilike(f"%{name}%"), models.Player.last_name.ilike(f"%{name}%")))
    if city:
        conditions.append(models.Player.city.ilike(f"%{city}%"))

    query = (
        db.query(models.Player.player_id,
            models.Player.first_name,
            models.Player.last_name,
            models.Player.city,
            func.coalesce(func.sum(models.Video.votes), 0).label("total_votes"))
        .join(models.Video)
        .filter(*conditions)
        .group_by(models.Player.player_id)
        .order_by(func.sum(models.Video.votes).desc())
        .offset(page * page_size).limit(page_size).all())

    players = []
    position = 0
    for p in query:
        players.append({
            "position": position + 1 + page * page_size,
            "username": p.first_name + " " + p.last_name,
            "city": p.city,
            "votes": p.total_votes})
        position += 1

    return JSONResponse(status_code = status.HTTP_200_OK, content = players)

# Votar por un video
@app.post("/api/public/videos/{video_id}/vote")
def vote_video(db: db_dependency, video_id: int):
    return None


# ============= ENDPOINTS DE AUTENTICACIÓN =============

@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def register_user(user: auth.UserRegister, db: db_dependency):
    """
    Registro de nuevos usuarios en la plataforma
    
    Códigos de respuesta:
    - 201: Usuario creado exitosamente
    - 400: Error de validación (email duplicado, contraseñas no coinciden)
    """
    # Verificar si el email ya existe
    existing_user = auth.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de validación (email duplicado, contraseñas no coinciden)."
        )
    
    # Validación de contraseñas (ya se hace en el modelo, pero por seguridad)
    if user.password1 != user.password2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de validación (email duplicado, contraseñas no coinciden)."
        )
    
    # Hash de la contraseña
    hashed_password = auth.hash_password(user.password1)
    
    # Crear usuario en la base de datos
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=hashed_password,
        city=user.city,
        country=user.country,
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "message": "Usuario creado exitosamente.",
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "city": user.city,
            "country": user.country
        }
    }


@app.post("/api/auth/login", response_model=auth.Token, status_code=status.HTTP_200_OK)
def login(user_credentials: auth.UserLogin, db: db_dependency):
    """
    Autenticación de usuarios y generación de token JWT
    
    Códigos de respuesta:
    - 200: Autenticación exitosa, retorna token
    - 401: Credenciales inválidas
    """
    # Autenticar usuario
    user = auth.authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    access_token_expires = timedelta(seconds=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "name": f"{user.first_name} {user.last_name}"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES
    }


@app.get("/api/verify-token")
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth.security),
    db: db_dependency = None
):
    """
    Endpoint para verificar si un token es válido
    Útil para probar la autenticación
    """
    # Obtener sesión de BD manualmente
    if db is None:
        db = SessionLocal()
    
    try:
        import jwt
        token = credentials.credentials
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        user = auth.get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        return {
            "valid": True,
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    finally:
        if db:
            db.close()