# app/models/comments.py
from sqlalchemy import Column, Integer, Text, JSON, DateTime, ForeignKey
from app.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    essay_id = Column(Integer, ForeignKey("essays.id"), nullable=False)
    comment_details = Column(Text, nullable=True)
    scores = Column(JSON, nullable=True)
    sum = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 关系
    essay = relationship("Essay", back_populates="comments")
