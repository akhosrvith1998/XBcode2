from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base(cls=AsyncAttrs)

class Whisper(Base):
    __tablename__ = "whispers"
    id = Column(Integer, primary_key=True)
    sender_id = Column(BigInteger, nullable=False)
    receiver_id = Column(BigInteger, nullable=True)
    receiver_username = Column(String, nullable=True)
    message = Column(String, nullable=False)
    photo_file_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())