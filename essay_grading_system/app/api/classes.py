# app/api/classes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.essay_tasks import TaskForTeacherResponse, TaskForStudentResponse
from app.services.class_service import ClassService
from app.services.auth_service import get_current_user
from app.schemas.classes import ClassCreate, ClassListResponse, ClassUpdate, ClassDetailResponse
from app.database import get_db
from app.models.users import User
from app.models.classes import Class, ClassStudent

router = APIRouter()


@router.post("/classes", response_model=ClassListResponse)
async def create_class(
        class_data: ClassCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="只有老师可以创建班级")

    new_class = ClassService.create_class(db, class_data, current_user.id)
    student_count = ClassService.get_student_count(db, new_class.id)

    return ClassListResponse(
        id=new_class.id,
        className=new_class.class_name,
        classCode=new_class.class_code,
        studentCount=student_count,
        createTime=new_class.created_at
    )


@router.get("/classes", response_model=List[ClassListResponse])
async def get_classes(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    classes = []
    if current_user.role == 'teacher':
        classes = ClassService.get_teacher_classes(db, current_user.id)

    result = []
    for c in classes:
        student_count = ClassService.get_student_count(db, c.id)
        result.append(ClassListResponse(
            id=c.id,
            className=c.class_name,
            classCode=c.class_code,
            studentCount=student_count,
            createTime=c.created_at
        ))

    return result


# 修改班级信息
@router.put("/classes/{class_id}", response_model=ClassListResponse)
async def update_class(
        class_id: int,
        class_data: ClassUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    class_item = ClassService.get_class_by_id(db, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    if class_item.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    updated_class = ClassService.update_class(db, class_item, class_data)
    student_count = ClassService.get_student_count(db, updated_class.id)

    return ClassListResponse(
        id=updated_class.id,
        className=updated_class.class_name,
        classCode=updated_class.class_code,
        studentCount=student_count,
        createTime=updated_class.created_at
    )


@router.delete("/classes/{class_id}", status_code=204)
async def delete_class(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    class_item = ClassService.get_class_by_id(db, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    if class_item.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除")

    ClassService.delete_class(db, class_item)


@router.get("/classes/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取班级详情
    - 老师：可以查看自己创建的班级详情
    - 学生：可以查看自己加入的班级详情
    """
    # 获取班级信息
    class_item = ClassService.get_class_by_id(db, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 权限检查
    if current_user.role == 'teacher':
        # 老师只能查看自己创建的班级
        if class_item.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权查看此班级")
    else:  # 学生
        # 检查学生是否在该班级中
        is_member = db.query(ClassStudent).filter(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == current_user.id
        ).first()
        if not is_member:
            raise HTTPException(status_code=403, detail="你不是该班级的成员")

    # 获取统计数据
    student_count = ClassService.get_student_count(db, class_id)
    teacher_name = ClassService.get_teacher_name(db, class_item.teacher_id)
    # 获取原始任务数据
    raw_tasks = ClassService.get_class_tasks(db, class_id, current_user)

    # 转换为 TaskResponse 类型
    tasks = []
    for task in raw_tasks:
        if current_user.role == 'teacher':
            # 老师视角：使用 TaskForTeacherResponse
            tasks.append(TaskForTeacherResponse(
                id=task["id"],
                class_id=task["class_id"],
                teacher_id=task.get("teacher_id", 0),
                requirement=task["requirement"],
                created_at=task["created_at"],
                essay_count=task.get("essay_count", 0),
                class_name=class_item.class_name,
                student_count=student_count,
                submitted_count=task.get("essay_count", 0)  # 老师需要这个字段
            ))
        else:
            # 学生视角：使用 TaskForStudentResponse
            tasks.append(TaskForStudentResponse(
                id=task["id"],
                class_id=task["class_id"],
                teacher_id=task.get("teacher_id", 0),
                requirement=task["requirement"],
                created_at=task["created_at"],
                essay_count=0,  # 学生不需要 essay_count，给个默认值
                class_name=class_item.class_name,
                student_count=student_count,
                user_submitted=task.get("user_submitted", False),  # 学生需要这个字段
                essay_id=task.get("essay_id", None)
            ))

    return ClassDetailResponse(
        id=class_item.id,
        className=class_item.class_name,
        classCode=class_item.class_code,
        studentCount=student_count,
        createTime=class_item.created_at,
        teacherName=teacher_name,
        teacherId=class_item.teacher_id,
        tasks=tasks
    )


@router.get("/classes/{class_id}/students")
async def get_class_students(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取班级的所有学生信息
    - 老师：可以查看自己创建的班级的学生
    - 学生：可以查看自己所在班级的同学
    """
    # 获取班级信息
    class_item = ClassService.get_class_by_id(db, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 权限检查
    if current_user.role == 'teacher':
        # 老师只能查看自己创建的班级的学生
        if class_item.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权查看此班级的学生")
    else:  # 学生
        # 检查学生是否在该班级中
        is_member = db.query(ClassStudent).filter(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == current_user.id
        ).first()
        if not is_member:
            raise HTTPException(status_code=403, detail="你不是该班级的成员")

    # 直接使用修改后的 get_student_list 方法，传入 include_id=True
    class_members = ClassService.get_class_members(db, class_id)
    print("class_members:",class_members)
    if class_members["teacher"]:
        class_members["teacher"]["avatar"] = "https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png"
    # 添加统一头像
    for student in class_members["students"]:
        student["avatar"] = "https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png"

    return {
        "code": 200,
        "data": class_members,
        "total": class_members["total"]
    }