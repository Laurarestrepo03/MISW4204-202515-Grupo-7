from fastapi import FastAPI, UploadFile, Form, status
from fastapi.responses import JSONResponse
from datetime import datetime
from moviepy import *
from typing import Annotated
from pathlib import Path
import shutil
import asyncio

app = FastAPI()

@app.get("/")
def root():
    return {"Hello":"World"}


# 1. Carga de video 
@app.post("/api/videos/upload")
async def upload_video(video_file: Annotated[UploadFile, Form()], title: Annotated[str, Form()]):

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
        task = asyncio.create_task(process_video(filename, title))
        return JSONResponse(status_code = status.HTTP_201_CREATED, 
                            content = {"message": "Video subido correctamente. Procesamiento en curso",
                              "task_id": "TODO"}) #TODO: Agregar task_id
    except Exception as e:
        return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content = {"message": f"Hubo un error subiendo el archivo, por favor intentar de nuevo. Error: {e}"})
    finally:
        video_file.file.close()
        
async def process_video(filename:str, title: str):
    video = VideoFileClip("original_videos/"+filename)
    # 1. Quitar audio
    video = video.with_volume_scaled(0.0)

    # 2. Recortar a 30s
    video_length = video.duration
    if video_length > 30:
        video = video.subclipped(0,30)

    # 3. Ajustar ratio a 16:9
    video = video.resized(height=900)
    image = ImageClip("assets/resize_image.png")
    image = image.with_duration(video.duration)
    video = video.with_position("center")
    video = CompositeVideoClip([image, video])

    # 4. Agregar logo ANB
    anb_logo = VideoFileClip("assets/anb_logo.mp4")
    videos = [anb_logo, video, anb_logo]
    final_video = concatenate_videoclips(videos, method='compose')
    final_video.write_videofile("processed_videos/"+title+".mp4") 

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