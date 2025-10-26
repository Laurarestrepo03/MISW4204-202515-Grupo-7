from celery import Celery
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips
from datetime import datetime, timezone
from pathlib import Path
import models
from database import SessionLocal
import time
import os
from celery.signals import worker_ready

celery_app = Celery("tasks", broker="redis://localhost:6379", backend="redis://localhost:6379")
ruta_original = os.getcwd()

@worker_ready.connect
def at_start(sender, **kwargs):
    check_unprocessed_videos.delay(True)

@celery_app.task()
def check_unprocessed_videos(first_time: bool = False):
    os.chdir('..')
    db = SessionLocal()
    try:
        unprocessed_videos = db.query(models.Video).filter(models.Video.task_id == None).all()
        for video in unprocessed_videos:
            video_path = "remote-folder/original_videos/" + video.original_filename.replace(" ", "_")
            result = process_video.delay(video_path, video.title, video.video_id)   
            add_task_id(video.video_id, result.id)
    finally:
        db.close()
        os.chdir(ruta_original)
        if not first_time:
            time.sleep(300)
        check_unprocessed_videos.delay()


@celery_app.task(default_retry_delay=5, max_retries=3)
def process_video(video_path: str, title: str, video_id: int):
    os.chdir('..')
    try:
        #raise TypeError("Forced error") # -> Descomentar esta linea para forzar un error
        # Crear carpeta processed_videos si no existe
        processed_dir = Path("remote-folder/processed_videos")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        video = VideoFileClip(video_path)

        # 1. Quitar audio
        video = video.with_volume_scaled(0.0)

        # 2. Recortar a 30s
        video_length = video.duration
        if video_length > 30:
            video = video.subclipped(0,30)

        # 3. Ajustar ratio a 16:9 (calidad 720p)
        resolution = 720
        background = ColorClip(size=(1280, 720), color=(0, 0, 0))
        background = background.with_duration(video.duration)
        video = video.resized(height=resolution)
        video = video.with_position("center")
        video = CompositeVideoClip([background, video])

        # 4. Agregar logo ANB
        try:
            anb_logo = VideoFileClip("remote-folder/assets/anb_logo.mp4").resized(height=resolution)
        except:
            anb_logo = VideoFileClip(ruta_original+"/assets/anb_logo.mp4").resized(height=resolution)
        videos = [anb_logo, video, anb_logo]
        final_video = concatenate_videoclips(videos, method='compose')
        final_video.write_videofile("remote-folder/processed_videos/"+title.replace(" ", "_")+".mp4")

        processed_url = "https://anb.com/videos/processed/"+title.replace(" ", "_")+".mp4"

        update_uploaded_info(video_id, datetime.now(timezone.utc), processed_url)
    except Exception:
        process_video.retry()
    finally:
        os.chdir(ruta_original)

def update_uploaded_info(video_id: int, processed_at: datetime, processed_url: str):
    db = SessionLocal()
    try:
        video = db.get(models.Video, video_id)
        if not video:
            return
        
        video.status = models.VideoStatus.PROCESSED
        video.processed_at = processed_at
        video.processed_url = processed_url
        db.commit()    
    finally:
        db.close()

def add_task_id(video_id: int, task_id: int):
    db = SessionLocal()
    try:
        video = db.get(models.Video, video_id)
        if video:
            video.task_id = task_id
            db.commit()
    finally:
        db.close()