# app/schemas/essay_tasks.py
from dataclasses import Field
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    class_id: int
    requirement: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    requirement: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    class_id: int
    teacher_id: int
    requirement: Optional[str]
    created_at: datetime
    essay_count: int
    class_name: Optional[str]
    student_count: int

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }


class TaskForTeacherResponse(TaskResponse):
    """老师视角的任务响应"""
    submitted_count: int = 0  # 直接给默认值


class TaskForStudentResponse(TaskResponse):
    """学生视角的任务响应"""
    user_submitted: bool = False  # 直接给默认值
    essay_id: Optional[int] = None
