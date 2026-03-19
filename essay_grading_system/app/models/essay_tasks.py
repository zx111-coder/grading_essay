# app/models/essay_tasks.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class EssayTask(Base):
    __tablename__ = "essay_tasks"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requirement = Column(Text, comment="作文要求")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    class_ = relationship("Class", back_populates="essay_tasks")
    teacher = relationship("User", back_populates="essay_tasks")
    essays = relationship("Essay", back_populates="task")
