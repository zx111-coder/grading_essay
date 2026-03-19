# app/schemas/comments.py
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class CommentBase(BaseModel):
    essay_id: int
    comment_details: Optional[str] = None  # 对应 comment_details 字段
    scores: Optional[dict[str, Any]] = None  # 对应 scores 字段（JSON）
    sum: Optional[str] = None  # 对应 sum 字段


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
