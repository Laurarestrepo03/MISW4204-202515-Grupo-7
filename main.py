from fastapi import FastAPI, UploadFile, Form, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
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
def upload_video(video_file: Annotated[UploadFile, Form()], title: Annotated[str, Form()], db: db_dependency):
    
    four_hundred_error = JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, 
                            content = {"message": "Error en el archivo (tipo o tamaño inválido)."})

    if video_file.content_type != "video/mp4":
        return four_hundred_error

    # Se guarda el video original para procesarlo
    upload_dir = Path("original_videos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = video_file.filename.replace(" ", "_")
    file_location = upload_dir / filename

    # TODO: Error 401

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
        video_id = add_uploaded_video(title, datetime.now(), db)
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

def add_uploaded_video(title: str, uploaded_at: datetime, db: db_dependency):
    original_url = "https://anb.com/uploads/"+title.replace(" ", "_")+".mp4"
    db_video = models.Video(title=title, status=models.VideoStatus.UPLOADED, uploaded_at=uploaded_at, 
                            processed_at=None, original_url=original_url, processed_url=None)
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
def get_videos_uploaded():
    videos = []
    return None

# 3. Consultar detalle de un video especifico
@app.get("/api/videos/{video_id}")
def get_video(video_id: int):
    return None

# 4. Eliminar video subido
@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int):
    return None

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