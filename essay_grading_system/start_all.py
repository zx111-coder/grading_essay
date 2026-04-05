# start_all.py
import subprocess
import sys
import os


def start_services():
    """同时启动两个服务"""
    print("🚀 正在启动服务...")

    # 启动普通服务（5000端口）
    normal_process = subprocess.Popen(
        [sys.executable, "run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("✅ 普通API服务启动中 (端口5000)...")

    # 启动流式服务（3001端口）
    stream_process = subprocess.Popen(
        [sys.executable, "main_stream.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("✅ 流式API服务启动中 (端口3001)...")

    print("\n✨ 所有服务已启动！")
    print("按 Ctrl+C 停止所有服务...")

    try:
        # 保持主进程运行
        while True:
            # 检查两个进程是否还在运行
            if normal_process.poll() is not None:
                print("❌ 普通API服务已停止")
                break
            if stream_process.poll() is not None:
                print("❌ 流式API服务已停止")
                break
    except KeyboardInterrupt:
        print("\n🛑 正在停止所有服务...")
        normal_process.terminate()
        stream_process.terminate()
        print("✅ 所有服务已停止")


if __name__ == "__main__":
    start_services()