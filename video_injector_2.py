from database import SessionLocal
import models
from datetime import datetime, timezone
import time

def escenario_2_db_injector():
    db = SessionLocal()
    delay_between_videos = 30
    number_petitions = 20
    try:
        for _ in range(number_petitions):
            title = "video-50mb"
            original_url = "https://anb.com/uploads/" + title.replace(" ", "_")
            db_video = models.Video(original_filename=title + ".mp4", title=title,
                                    status=models.VideoStatus.UPLOADED,
                                    uploaded_at=datetime.now(timezone.utc),
                                    processed_at=None, original_url=original_url, processed_url=None, user_id=179)
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            time.sleep(delay_between_videos)
    finally:
        db.close()
        time.sleep(30)

escenario_2_db_injector()

def escenario_2_celery_injector():
    from tasks import process_video
    delay_between_videos = 1
    number_petitions = 1
    db = SessionLocal()
    try:
        for _ in range(number_petitions):
            title = "video-50mb"
            original_url = "https://anb.com/uploads/" + title.replace(" ", "_")
            db_video = models.Video(original_filename=title + ".mp4", title=title,
                                    status=models.VideoStatus.UPLOADED,
                                    uploaded_at=datetime.now(timezone.utc),
                                    processed_at=None, original_url=original_url, processed_url=None, user_id=179)
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            process_video.delay(video_id=db_video.video_id, video_name=db_video.original_filename, title=db_video.title)
            time.sleep(delay_between_videos)
    finally:
        db.close()