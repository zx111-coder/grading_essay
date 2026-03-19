# app/schemas/essays.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class EssayBase(BaseModel):
    task_id: Optional[int] = None
    word_count: Optional[int] = None
    grade: int
    requirement: Optional[str] = None
    title: Optional[str] = None
    paragraphs: Optional[List[str]] = None  # 列表


class EssayCreate(EssayBase):
    user_id: int
    upload_date: Optional[datetime] = None


class Essay(EssayBase):
    id: int
    user_id: int
    upload_date: Optional[datetime] = None
    score: Optional[int] = None
    student_name: Optional[str] = None

    class Config:
        from_attributes = True
