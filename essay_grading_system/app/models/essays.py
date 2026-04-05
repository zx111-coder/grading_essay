# app/models/essays.py
from sqlalchemy import Column, Integer, Text, JSON, DateTime, VARCHAR, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("essay_tasks.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_count = Column(Integer, nullable=True)
    upload_date = Column(DateTime, nullable=True)
    grade = Column(Integer, nullable=True)
    requirement = Column(Text, nullable=True)
    title = Column(VARCHAR(200), nullable=True)
    paragraphs = Column(JSON, nullable=True)

    # 关系
    task = relationship("EssayTask", back_populates="essays")
    user = relationship("User", back_populates="essays")
    comments = relationship("Comment", back_populates="essay")
