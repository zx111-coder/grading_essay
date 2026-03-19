# app/api/__init__.py
# 导入FastAPI的APIRouter（替代原Flask蓝图）
from .upload import router as upload_router
from .analysis import router as analysis_router
from .auth import router as auth_router
from .history import router as history_router
from app.api.classes import router as class_router
from .tasks import router as task_router
from .student import router as student_router
# 定义所有路由列表（替代原all_blueprints）
all_routers = [
    # 格式：(router实例, 前缀, 标签)
    (upload_router, "/api", ["文件上传"]),
    (analysis_router, "/api", ["作文分析"]),
    (auth_router, "/api/auth", ["用户认证"]),
    (history_router, "/api", ["历史记录"]),
    (class_router, "/api", ["班级管理"]),
    (task_router, "/api/class", ["作文要求"]),
    (student_router, "/api/student", ["学生管理"])
    # 后续新增路由，直接在这里添加即可（比如用户路由）
    # (user_router, "/api/user", ["用户管理"]),
]