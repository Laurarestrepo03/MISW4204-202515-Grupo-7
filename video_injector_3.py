from database import SessionLocal
import models
from datetime import datetime, timezone
import time

from producer_sqs import send_message

def escenario_3_sqs_injector():
    delay_between_videos = 30
    number_petitions = 20
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
            send_message(db_video.video_id)
            time.sleep(delay_between_videos)
    finally:
        db.close()

escenario_3_sqs_injector()