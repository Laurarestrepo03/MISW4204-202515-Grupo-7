from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum

class VideoStatus(enum.Enum):
    UPLOADED = 'uploaded'
    PROCESSED = 'processed'

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Relación con videos
    videos = relationship("Video", back_populates="user")

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
    
    # Relación con usuario
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    user = relationship("User", back_populates="videos")


class Vote(Base):
    __tablename__ = 'votes'
    vote_id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.video_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    video = relationship('Video')
    user = relationship('User')