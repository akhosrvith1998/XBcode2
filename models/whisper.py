from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Whisper(Base):
    __tablename__ = "whispers"
    id = Column(Integer, primary_key=True)
    sender_id = Column(BigInteger, nullable=False)
    receiver_id = Column(BigInteger, nullable=True)
    receiver_username = Column(String, nullable=True)
    message = Column(String, nullable=False)
    photo_file_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
