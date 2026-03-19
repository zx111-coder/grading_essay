# app/schemas/classes.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Union
from app.schemas.essay_tasks import TaskResponse, TaskForTeacherResponse, TaskForStudentResponse


# -------------------------- 基础模型（抽离公共字段） --------------------------
class ClassBase(BaseModel):
    """班级基础模型（抽离入参/响应的公共字段）"""
    class_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="班级名称，非空，1-100个字符"
    )

    class Config:
        # 公共配置：支持从 ORM 对象解析
        from_attributes = True
        # 公共配置：datetime 序列化规则（抽离复用）
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }


# -------------------------- 入参模型（创建/修改） --------------------------
class ClassCreate(ClassBase):
    """创建班级入参模型（前端传入）"""
    # 校验：班级名称不能全是空格
    @validator('class_name')
    def validate_class_name_not_blank(cls, v):
        stripped_v = v.strip()
        if not stripped_v:
            raise ValueError('班级名称不能为空（不能全是空格）')
        return stripped_v


class ClassUpdate(BaseModel):
    """修改班级入参模型（前端传入，字段可选）"""
    class_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="班级名称，1-100个字符"
    )

    # 校验：如果传了班级名称，不能全是空格
    @validator('class_name')
    def validate_class_name_not_blank(cls, v):
        if v is None:
            return v  # 未传则跳过
        stripped_v = v.strip()
        if not stripped_v:
            raise ValueError('班级名称不能为空（不能全是空格）')
        return stripped_v


# -------------------------- 学生班级相关模型 --------------------------
# class JoinClassRequest(BaseModel):
#     """加入班级请求模型"""
#     class_code: str = Field(
#         ...,
#         min_length=6,
#         max_length=20,
#         description="班级邀请码，6-20个字符"
#     )
#
#     @validator('class_code')
#     def validate_class_code(cls, v):
#         """校验班级邀请码格式"""
#         if not v or not v.strip():
#             raise ValueError('班级邀请码不能为空')
#         # 可以添加更多校验，比如只允许字母和数字
#         import re
#         if not re.match(r'^[A-Za-z0-9]+$', v):
#             raise ValueError('班级邀请码只能包含字母和数字')
#         return v.upper()  # 统一转为大写


# -------------------------- 响应模型（返回给前端） --------------------------
class ClassListResponse(BaseModel):
    """班级列表响应模型（前端展示用，驼峰命名）"""
    id: int = Field(description="班级ID")
    className: str = Field(description="班级名称")
    classCode: str = Field(description="班级邀请码")
    studentCount: int = Field(description="班级学生数量")
    createTime: datetime = Field(description="班级创建时间")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }


class ClassDetailResponse(ClassListResponse):
    """班级详情响应模型（继承列表模型，新增详情字段）"""
    teacherName: str = Field(description="授课老师名称")
    teacherId: int = Field(description="授课老师ID")
    tasks: List[Union[TaskForTeacherResponse, TaskForStudentResponse]] = Field(
        default=[],
        description="该班级发布的所有作文题目"
    )


# class JoinClassResponse(BaseModel):
#     """加入班级响应模型"""
#     message: str = Field(description="响应消息")
#     class_id: Optional[int] = Field(None, description="班级ID")
#     class_name: Optional[str] = Field(None, description="班级名称")
#     class_code: Optional[str] = Field(None, description="班级code")
#     teacher_name: Optional[str] = Field(None, description="老师名称")
#
#     class Config:
#         from_attributes = True
#
#
# class LeaveClassResponse(BaseModel):
#     """离开班级响应模型"""
#     message: str = Field(description="响应消息")