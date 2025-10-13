from celery import Celery
from moviepy import *
from datetime import datetime
import models
from database import SessionLocal

celery_app = Celery("tasks", broker="redis://localhost:6379")

@celery_app.task
def process_video(filename:str, title: str, video_id: int):
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
    anb_logo = VideoFileClip("assets/anb_logo.mp4").resized(height=900)
    videos = [anb_logo, video, anb_logo]
    final_video = concatenate_videoclips(videos, method='compose')
    final_video.write_videofile("processed_videos/"+title+".mp4")

    processed_url = "https://anb.com/videos/processed/"+title+".mp4"

    update_uploaded_info(video_id, datetime.now(), processed_url)

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


