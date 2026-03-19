# app/models/users.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # 存加密后的密码
    role = Column(String(50), nullable=False, default="student", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    classes = relationship("Class", back_populates="teacher", foreign_keys="[Class.teacher_id]")
    joined_classes = relationship("ClassStudent", back_populates="student")
    essays = relationship("Essay", back_populates="user")
    essay_tasks = relationship("EssayTask", back_populates="teacher")
