from celery import Celery
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips
from datetime import datetime, timezone
from pathlib import Path
from database import SessionLocal
from celery.signals import worker_ready
from s3 import retrieve_file_from_bucket, upload_file_to_bucket
import models
import time
import os

celery_app = Celery("tasks", broker="redis://localhost:6379", backend="redis://localhost:6379")

@worker_ready.connect
def at_start(sender, **kwargs):
    check_unprocessed_videos.delay(True)

@celery_app.task()
def check_unprocessed_videos(first_time: bool = False):
    db = SessionLocal()
    try:
        unprocessed_videos = db.query(models.Video).filter(models.Video.task_id == None).all()
        for video in unprocessed_videos:
            video_name = video.original_filename.replace(" ", "_")
            result = process_video.delay(video_name, video.title, video.video_id)   
            add_task_id(video.video_id, result.id)
    finally:
        db.close()
        if not first_time:
            time.sleep(300)
        check_unprocessed_videos.delay()


@celery_app.task(default_retry_delay=5, max_retries=3)
def process_video(video_name: str, title: str, video_id: int):
    try:
        #raise TypeError("Forced error") # -> Descomentar esta linea para forzar un error
        # Crear carpeta processed si no existe
        temp_dir_original = Path("temp_files/original")
        temp_dir_original.mkdir(parents=True, exist_ok=True)
        temp_dir_processed = Path("temp_files/processed")
        temp_dir_processed.mkdir(parents=True, exist_ok=True)

        s3_path="original_videos/"+video_name
        local_path = "temp_files/original/"+video_name
        retrieve_file_from_bucket(s3_path, local_path)

        video = VideoFileClip(local_path)

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
        anb_logo = VideoFileClip("assets/anb_logo.mp4").resized(height=resolution)
        videos = [anb_logo, video, anb_logo]
        final_video = concatenate_videoclips(videos, method='compose')
        no_spaces_title = title.replace(" ", "_")+".mp4"
        temp_video_path = "temp_files/processed/"+no_spaces_title
        final_video.write_videofile(temp_video_path)

        processed_url = "https://anb.com/videos/processed/"+no_spaces_title

        upload_file_to_bucket(temp_video_path, "processed_videos/"+no_spaces_title)
        os.remove(local_path)
        os.remove(temp_video_path)
        
        update_uploaded_info(video_id, datetime.now(timezone.utc), processed_url)
    except Exception:
        process_video.retry()
        

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