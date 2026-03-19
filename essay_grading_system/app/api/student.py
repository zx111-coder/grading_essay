# app/api/student.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.class_service import ClassService
from app.services.auth_service import get_current_user
from app.database import get_db
from app.models.users import User
from app.models.classes import ClassStudent, Class
# from app.schemas.classes import JoinClassRequest, JoinClassResponse
router = APIRouter()


@router.get("/my-class")
async def get_my_class(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取学生已加入的班级ID和邀请码
    """
    # 验证用户角色
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以访问此接口"
        )

    # 查询学生是否已加入班级
    class_student = db.query(ClassStudent).filter(
        ClassStudent.student_id == current_user.id
    ).first()

    if not class_student:
        return None

    # 获取班级详细信息（只需要id和class_code）
    class_info = db.query(Class).filter(
        Class.id == class_student.class_id
    ).first()

    # 只返回需要的字段
    return {
        "class_id": class_info.id,
        "class_code": class_info.class_code
    }


# 加入班级
@router.post("/join/{class_code}")
async def join_class(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 校验班级是否存在
    class_item = ClassService.get_class_by_code(db, class_code)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    success = ClassService.join_class(db, class_item, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="已经加入该班级")

    return {
        "message": "成功加入班级",
        "class_id": class_item.id,
        "class_code": class_item.class_code,
        "class_name": class_item.class_name
    }


# 成员离开班级
@router.post("/leave/{class_id}")
async def leave_class(
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    class_item = ClassService.get_class_by_id(db, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 班级创建老师不允许离开自己的班级
    if class_item.teacher_id == current_user.id:
        raise HTTPException(status_code=403, detail="班级创建者不允许离开班级")
    success = ClassService.leave_class(db, class_item, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="你不在该班级中")

    return {"message": "成功离开班级"}
