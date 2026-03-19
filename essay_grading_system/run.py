import uvicorn  # 用于启动FastAPI
from app import create_app

app = create_app()
# 5. 可选：保留启动入口（替代原app.run，方便习惯python run.py启动）
if __name__ == "__main__":
    # 配置和原Flask一致：允许局域网访问、端口5000、开发模式自动重启
    uvicorn.run(
        "run:app",        # 格式：文件名:应用实例名
        host="0.0.0.0",   # 对应原host
        port=5000,        # 对应原port
        reload=False       # 对应原debug=True（开发模式自动重启）
    )