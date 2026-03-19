# app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import EssayTask
from app.schemas.essays import Essay as EssaySchema
from app.services.task_service import TaskService
from app.services.auth_service import get_current_user
from app.schemas.essay_tasks import TaskCreate, TaskUpdate, TaskResponse
from app.database import get_db
from app.models.users import User
from app.models.classes import Class, ClassStudent
from app.models.essays import Essay

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task_data: TaskCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    创建作文题目（仅老师可用）
    """
    # 检查用户角色
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="只有老师可以创建题目")

    # 检查班级是否存在且属于该老师
    class_item = db.query(Class).filter(Class.id == task_data.class_id).first()
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    if class_item.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权在此班级创建题目")

    # 创建题目
    task = TaskService.create_task(db, task_data, current_user.id)

    # 获取作文数量（新创建的题目应该是0）
    essay_count = TaskService.get_task_essay_count(db, task.id)
    # 获取班级学生人数
    student_count = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_item.id
    ).count()

    return TaskResponse(
        id=task.id,
        class_id=task.class_id,
        teacher_id=task.teacher_id,
        requirement=task.requirement,
        created_at=task.created_at,
        essay_count=essay_count,
        class_name=class_item.class_name,
        student_count=student_count
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_detail(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取单个题目详情
    """
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="题目不存在")

    essay_count = TaskService.get_task_essay_count(db, task_id)
    class_item = db.query(Class).filter(Class.id == task.class_id).first()
    student_count = db.query(ClassStudent).filter(ClassStudent.class_id == task.class_id).count() if class_item else 0

    return TaskResponse(
        id=task.id,
        class_id=task.class_id,
        teacher_id=task.teacher_id,
        requirement=task.requirement,
        created_at=task.created_at,
        essay_count=essay_count,
        class_name=class_item.class_name if class_item else "",
        student_count=student_count
    )


@router.get("/tasks/{task_id}/essays", response_model=List[EssaySchema])
async def get_task_essays(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取题目的所有学生作文（包含学生姓名）
    仅老师可访问
    """
    # 检查用户角色
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="只有老师可以查看作文列表")

    # 检查题目是否存在且属于该老师
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="题目不存在")

    if task.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此题目的作文")

        # 获取作文列表（带学生姓名）
    essays = TaskService.get_task_essays(db, task_id)

    return essays


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    删除题目（仅老师可用）
    """
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="只有老师可以删除题目")

    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="题目不存在")

    if task.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此题目")

    TaskService.delete_task(db, task)


@router.post("/essays/{essay_id}/reject")
async def reject_essay(
        essay_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    打回单篇作文（仅老师可操作）
    将 essays 表中该条数据的 task_id 设置为 NULL
    """
    # 权限检查
    if current_user.role != 'teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以打回作文"
        )

    # 检查作文是否存在
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    # 检查老师是否有权限（该作文所属题目的班级是否是该老师的）
    if essay.task_id:
        task = db.query(EssayTask).filter(EssayTask.id == essay.task_id).first()
        if task and task.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此作文"
            )

    # 调用 service 中的方法打回作文
    success = TaskService.reject_essay(db, essay_id)
    if not success:
        raise HTTPException(status_code=400, detail="打回失败")

    return {
        "message": "打回成功",
        "essay_id": essay_id
    }