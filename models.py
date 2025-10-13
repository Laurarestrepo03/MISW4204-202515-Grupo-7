from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from database import Base

class ProcessedVideo(Base):
    __tablename__ = 'processed_videos'
    video_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    uploaded_at = Column(DateTime)
    processed_at = Column(DateTime, nullable=True)
    processed_url = Column(String, nullable=True)