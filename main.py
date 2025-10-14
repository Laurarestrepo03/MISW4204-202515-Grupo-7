from fastapi import FastAPI, UploadFile, Form, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from moviepy import *
from typing import Annotated, List
from pathlib import Path
from pydantic import BaseModel
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from tasks import process_video
import models
import shutil

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

    # Se guarda el video original para procesarlo
    upload_dir = Path("original_videos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = video_file.filename
    file_location = upload_dir / filename

    # TODO: Error 400, 401

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        # TODO: Ajustar con broker
        video_id = add_uploaded_video(title, datetime.now(), db)
        result = process_video.delay(filename, title, video_id)
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

# TODO: Añadir autenticacion para solo ver videos propios

# 2. Consultar mis videos
@app.get("/api/videos")
def get_videos_uploaded():
    videos = []
    return None

# 3. Consultar detalle de un video especifico
@app.get("/api/videos/{video_id}")
def get_video(id_video: int):
    return None

# 4. Eliminar video subido
@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int):
    return None