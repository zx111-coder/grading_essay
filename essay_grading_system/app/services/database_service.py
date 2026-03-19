# app/services/database_service.py
from sqlalchemy.orm import Session
from app.models import User, Essay, Comment
from app.schemas.essays import EssayCreate
from app.schemas.comments import CommentCreate


class DataService:

    @staticmethod
    def save_essay(db: Session, essay_data: EssayCreate):
        """保存作文到数据库"""
        try:
            print("开始保存 Essay")
            # 检查必要字段
            essay_dict = essay_data.dict()
            db_essay = Essay(**essay_dict)  # 核心：Pydantic模型转ORM模型
            db.add(db_essay)  # 将ORM对象加入会话（待提交）
            db.flush()  # 仅刷入内存，生成ID，事务未提交
            db.refresh(db_essay)   # 从数据库刷新对象，获取自动生成的字段（如id）
            return db_essay
        except Exception as e:
            print(f"❌ save_essay 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    @staticmethod
    def save_comment(db: Session, comment_data: CommentCreate):
        """保存批改结果到数据库"""
        try:
            db_correction = Comment(**comment_data.dict())
            db.add(db_correction)
            db.flush()  # 仅刷入内存，生成ID，事务未提交
            db.refresh(db_correction)
            return db_correction
        except Exception as e:
            print(f"❌ save_comment 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    @staticmethod
    def get_essay(db: Session, essay_id: int):
        """获取作文"""
        return db.query(Essay).filter(Essay.id == essay_id).first()

    @staticmethod
    def get_comment(db: Session, essay_id: int):
        """获取批改结果"""
        return db.query(Comment).filter(Comment.essay_id == essay_id).first()