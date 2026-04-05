# main_stream.py - 流式分析专用服务
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.analysis import router as analysis_router  # 只导入 analysis 路由


def create_stream_app():
    """创建流式分析专用应用"""
    app = FastAPI(title="流式分析服务", version="1.0.0")

    # 配置 CORS（允许前端调用）
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 只注册 analysis 路由
    app.include_router(analysis_router, prefix="/api", tags=["作文分析"])

    @app.get('/')
    def index():
        return {
            'code': 200,
            'msg': '流式分析服务启动成功！'
        }

    return app


# 创建应用实例
app = create_stream_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3001)  # 与你前端的 streamUrl 端口一致