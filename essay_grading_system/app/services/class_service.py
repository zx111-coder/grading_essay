# app/services/class_service.py
from sqlalchemy import desc
from sqlalchemy.orm import Session
import random
import string
from typing import List, Optional
from app.models.users import User
from app.models.classes import Class, ClassStudent
from app.schemas.classes import ClassCreate, ClassUpdate
from app.models.essay_tasks import EssayTask  # 导入作文题目模型
from app.models.essays import Essay  # 导入作文模型
from app.models.comments import Comment
from app.schemas.essay_tasks import TaskForStudentResponse, TaskForTeacherResponse


class ClassService:
    @staticmethod
    def generate_class_code():
        """生成唯一的班级代码"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=12))

    @staticmethod
    def create_class(db: Session, class_data: ClassCreate, teacher_id: int) -> Class:
        """创建班级"""
        while True:
            class_code = ClassService.generate_class_code()
            existing_class = db.query(Class).filter(Class.class_code == class_code).first()
            if not existing_class:
                break

        new_class = Class(
            class_name=class_data.class_name,
            class_code=class_code,
            teacher_id=teacher_id
        )

        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return new_class

    @staticmethod
    def get_teacher_classes(db: Session, teacher_id: int) -> List[Class]:
        """获取老师创建的班级列表"""
        return db.query(Class).filter(Class.teacher_id == teacher_id).order_by(Class.created_at.desc()).all()

    @staticmethod
    def get_student_count(db: Session, class_id: int) -> int:
        """获取班级学生人数"""
        return db.query(ClassStudent).filter(ClassStudent.class_id == class_id).count()

    @staticmethod
    def get_class_by_id(db: Session, class_id: int) -> Optional[Class]:
        """通过ID获取班级"""
        return db.query(Class).filter(Class.id == class_id).first()

    @staticmethod
    def get_class_by_code(db: Session, class_code: str) -> Optional[Class]:
        """通过班级代码获取班级"""
        return db.query(Class).filter(Class.class_code == class_code).first()

    @staticmethod
    def update_class(db: Session, class_item: Class, class_data: ClassUpdate) -> Class:
        """更新班级信息"""
        if class_data.class_name:
            class_item.class_name = class_data.class_name
        db.commit()
        db.refresh(class_item)
        return class_item

    @staticmethod
    def delete_class(db: Session, class_item: Class) -> None:
        """删除班级"""
        # 1. 先删除班级关联的作文题目
        db.query(EssayTask).filter(EssayTask.class_id == class_item.id).delete()

        # 2. 再删除班级关联的学生记录
        db.query(ClassStudent).filter(ClassStudent.class_id == class_item.id).delete()

        # 3. 最后删除班级
        db.delete(class_item)
        db.commit()

    @staticmethod
    def get_class_members(db: Session, class_id: int) -> dict:
        """
        获取班级所有成员（老师和学生），老师排在第一
        返回格式: {
            "teacher": {"id": 1, "name": "张老师", "role": "teacher"},
            "students": [{"id": 2, "name": "张三", "role": "student"}, ...]
        }
        """
        # 获取班级信息
        class_info = db.query(Class).filter(Class.id == class_id).first()
        if not class_info:
            return {"teacher": None, "students": []}

        # 获取老师信息
        teacher = db.query(User).filter(User.id == class_info.teacher_id).first()
        teacher_info = {
            "id": teacher.id,
            "name": teacher.username,
            "role": "teacher"
        } if teacher else None

        # 获取所有学生
        students = db.query(
            User.id,
            User.username.label('name')
        ).join(
            ClassStudent, User.id == ClassStudent.student_id
        ).filter(
            ClassStudent.class_id == class_id
        ).order_by(User.username).all()

        student_list = [
            {
                "id": s.id,
                "name": s.name,
                "role": "student"
            }
            for s in students
        ]

        return {
            "teacher": teacher_info,
            "students": student_list,
            "total": len(student_list) + (1 if teacher_info else 0)
        }

    @staticmethod
    def get_class_tasks(db: Session, class_id: int, current_user: User = None) -> List[dict]:
        """
        获取班级的所有作文题目
        根据用户角色返回不同的数据
        """
        tasks = db.query(EssayTask).filter(
            EssayTask.class_id == class_id
        ).order_by(desc(EssayTask.created_at)).all()

        result = []
        for task in tasks:
            # 基础题目信息 - 确保字段名和 TaskResponse 一致
            task_data = {
                "id": task.id,
                "class_id": task.class_id,
                "teacher_id": task.teacher_id,  # 加上 teacher_id
                "requirement": task.requirement,
                "created_at": task.created_at,
                "essay_count": 0  # 统一使用 essay_count
            }

            if current_user and current_user.role == 'teacher':
                # 老师需要知道提交人数
                essay_count = db.query(Essay).filter(
                    Essay.task_id == task.id
                ).count()
                task_data["essay_count"] = essay_count  # 使用 essay_count
            elif current_user and current_user.role == 'student':
                # 学生需要知道自己是否已提交
                essay = db.query(Essay).filter(
                    Essay.task_id == task.id,
                    Essay.user_id == current_user.id
                ).first()
                if essay:
                    task_data["user_submitted"] = True
                    task_data["essay_id"] = essay.id
                    comment = db.query(Comment).filter(
                        Comment.essay_id == essay.id
                    ).first()
                    task_data["task_finish"] = comment is not None
                else:
                    task_data["user_submitted"] = False
                    task_data["task_finish"] = False  # 学生未提交，task_finish 默认为 False
                    task_data["essay_id"] = None  # 或者不添加这个字段
                task_data["essay_count"] = 0  # 学生不需要 essay_count，但为了类型匹配给个默认值

            result.append(task_data)

        return result

    @staticmethod
    def get_teacher_name(db: Session, teacher_id: int) -> str:
        """获取老师名称"""
        teacher = db.query(User).filter(User.id == teacher_id).first()
        return teacher.username if teacher else ""

    @staticmethod
    def join_class(db: Session, class_item: Class, student_id: int) -> bool:
        """学生加入班级"""
        existing = db.query(ClassStudent).filter(
            ClassStudent.class_id == class_item.id,
            ClassStudent.student_id == student_id
        ).first()

        if existing:
            return False

        class_student = ClassStudent(
            class_id=class_item.id,
            student_id=student_id
        )

        db.add(class_student)
        db.commit()
        return True

    @staticmethod
    def leave_class(db: Session, class_item: Class, student_id: int) -> bool:
        """学生离开班级"""
        class_student = db.query(ClassStudent).filter(
            ClassStudent.class_id == class_item.id,
            ClassStudent.student_id == student_id
        ).first()

        if not class_student:
            return False

        db.delete(class_student)
        db.commit()
        return True