from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from database import Base
import enum

class VideoStatus(enum.Enum):
    UPLOADED = 'uploaded'
    PROCESSED = 'processed'

class Video(Base):
    __tablename__ = 'videos'
    video_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(Enum(VideoStatus), index=True)
    uploaded_at = Column(DateTime)
    processed_at = Column(DateTime, nullable=True)
    original_url = Column(String)
    processed_url = Column(String, nullable=True)
    votes = Column(Integer, default=0)
    task_id = Column(String, nullable=True)