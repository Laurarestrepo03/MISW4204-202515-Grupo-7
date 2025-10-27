from database import SessionLocal
import models
from datetime import datetime, timezone
import time

def check_unprocessed_videos():
    db = SessionLocal()
    delay_between_videos = 1
    number_petitions = 100
    try:
        for _ in range(number_petitions):
            title = "Michael Jordan"
            original_url = "https://anb.com/uploads/" + title.replace(" ", "_") + ".mp4"
            db_video = models.Video(original_filename="MichaelJordan.mp4", title=title,
                                    status=models.VideoStatus.UPLOADED,
                                    uploaded_at=datetime.now(timezone.utc),
                                    processed_at=None, original_url=original_url, processed_url=None, user_id=1)
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            time.sleep(delay_between_videos)
    finally:
        db.close()
        time.sleep(30)