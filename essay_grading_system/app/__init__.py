# app/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # FastAPI的跨域中间件
import os
from dotenv import load_dotenv
from app.config import settings

# 加载.env配置
load_dotenv()

# 2. 定义全局配置字典
# 把原app.config的配置提取为全局字典，方便其他模块调用
APP_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), os.getenv('UPLOAD_FOLDER', 'uploads')),
    'ALLOWED_EXTENSIONS': set(os.getenv('ALLOWED_EXTENSIONS', '').split(',')),
    'MAX_CONTENT_LENGTH': int(os.getenv('MAX_CONTENT_LENGTH', 10485760)),  # 默认10MB
    'TENCENT_SECRET_ID': os.getenv('TENCENT_SECRET_ID'),
    'TENCENT_SECRET_KEY': os.getenv('TENCENT_SECRET_KEY'),
    'TENCENT_OCR_REGION': os.getenv('TENCENT_OCR_REGION'),
    'COZE_API_TOKEN': os.getenv('COZE_API_TOKEN'),
    'COZE_WORKFLOW_ID': os.getenv('COZE_WORKFLOW_ID')
}


# FastAPI应用工厂函数
def create_app():
    """创建FastAPI应用实例（对应原Flask的create_app）"""
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    # 配置 CORS
    origins = [
        "http://localhost:5173",  # 前端地址
        "http://127.0.0.1:5173",
        # 如果有其他前端环境，也可以加在这里
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 允许的域名
        allow_credentials=True,  # 允许前端携带Cookie等凭证
        allow_methods=["*"],  # 允许所有 HTTP 方法（GET/POST/PUT/DELETE等）
        allow_headers=["*"],  # 允许所有请求头（比如Token、Content-Type等）
    )

    # 批量注册所有路由
    from app.api import all_routers
    for router, prefix, tags in all_routers:
        app.include_router(router, prefix=prefix, tags=tags)

    # 7. 保留测试接口
    @app.get('/')
    def index():
        return {
            'code': 200,
            'msg': '后端服务启动成功，接口已就绪！'
        }  # FastAPI自动返回200状态码，无需手动指定

    return app
