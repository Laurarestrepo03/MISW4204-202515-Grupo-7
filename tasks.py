from celery import Celery
from moviepy import *
from datetime import datetime, timezone
from pathlib import Path
import models
from database import SessionLocal

celery_app = Celery("tasks", broker="redis://localhost:6379")

@celery_app.task
def process_video(video_path: str, title: str, video_id: int):
    # Crear carpeta processed_videos si no existe
    processed_dir = Path("processed_videos")
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
    anb_logo = VideoFileClip("assets/anb_logo.mp4").resized(height=resolution)
    videos = [anb_logo, video, anb_logo]
    final_video = concatenate_videoclips(videos, method='compose')
    final_video.write_videofile("processed_videos/"+title.replace(" ", "_")+".mp4")

    processed_url = "https://anb.com/videos/processed/"+title.replace(" ", "_")+".mp4"

    update_uploaded_info(video_id, datetime.now(timezone.utc), processed_url)

def update_uploaded_info(video_id: int, processed_at: datetime, processed_url: str):
    db = SessionLocal()
    try:
        video = db.get(models.Video, video_id)
        if not video:
            pass
        else:
            video.status = models.VideoStatus.PROCESSED
            video.processed_at = processed_at
            video.processed_url = processed_url
            db.commit()    
    finally:
        db.close()
