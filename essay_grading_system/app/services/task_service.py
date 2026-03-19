# app/services/task_service.py
from pydantic import json
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.essay_tasks import EssayTask
from app.models.essays import Essay
from app.schemas.essay_tasks import TaskCreate, TaskUpdate
from app.models.users import User
from app.models.comments import Comment


class TaskService:
    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, teacher_id: int) -> EssayTask:
        """创建作文任务"""
        task = EssayTask(
            class_id=task_data.class_id,
            teacher_id=teacher_id,
            requirement=task_data.requirement
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_class_tasks(db: Session, class_id: int) -> List[EssayTask]:
        """获取班级的所有任务"""
        return db.query(EssayTask).filter(
            EssayTask.class_id == class_id
        ).order_by(EssayTask.created_at.desc()).all()

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[EssayTask]:
        """通过ID获取任务"""
        return db.query(EssayTask).filter(EssayTask.id == task_id).first()

    @staticmethod
    def update_task(db: Session, task: EssayTask, task_data: TaskUpdate) -> EssayTask:
        """更新任务"""
        if task_data.requirement:
            task.requirement = task_data.requirement
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task: EssayTask) -> None:
        """删除任务"""
        db.delete(task)
        db.commit()

    @staticmethod
    def get_task_essays(db: Session, task_id: int) -> List[Dict[str, Any]]:
        """获取任务的所有作文，包含学生姓名和评分"""
        # 联表查询：Essay 关联 User 表获取学生姓名，左连接 Comment 表获取评分
        results = db.query(
            Essay,
            User.username.label('student_name'),
            Comment
        ).join(
            User, Essay.user_id == User.id
        ).outerjoin(  # 使用左连接，因为可能没有评论
            Comment, Essay.id == Comment.essay_id
        ).filter(
            Essay.task_id == task_id
        ).order_by(desc(Essay.upload_date)).all()

        essays = []
        for row in results:
            essay = row[0]  # Essay 对象
            student_name = row.student_name
            comment = row[2]  # Comment 对象，可能为 None

            # 从 comment 的 scores JSON 中提取 score
            score = None
            if comment and comment.scores:
                if isinstance(comment.scores, dict):
                    score = comment.scores.get("score")
                elif isinstance(comment.scores, str):
                    try:
                        scores_dict = json.loads(comment.scores)
                        score = scores_dict.get("score")
                    except:
                        pass

            essay_dict = {
                'id': essay.id,
                'task_id': essay.task_id,
                'user_id': essay.user_id,
                'student_name': student_name,
                'title': essay.title,
                'requirement': essay.requirement,
                'paragraphs': essay.paragraphs,
                'word_count': essay.word_count,
                'upload_date': essay.upload_date,
                'grade': essay.grade,
                'score': score  # 直接从 comment.scores 中提取的 score
            }
            essays.append(essay_dict)

        return essays

    @staticmethod
    def get_task_essay_count(db: Session, task_id: int) -> int:
        """获取任务已提交作文数量"""
        return db.query(Essay).filter(Essay.task_id == task_id).count()

    @staticmethod
    def reject_essay(db: Session, essay_id: int) -> bool:
        """打回单篇作文：将作文的 task_id 设置为 NULL"""
        essay = db.query(Essay).filter(Essay.id == essay_id).first()
        if essay:
            essay.task_id = None
            db.commit()
            return True
        return False