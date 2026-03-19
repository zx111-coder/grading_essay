# app/api/analysis.py
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
from app.database import get_db  # 导入数据库会话
from sqlalchemy.orm import Session
from app.services.analysis_service import analyze_composition_text
from app.services.database_service import DataService  # 导入数据库服务
import asyncio
router = APIRouter()


@router.post('/analysis')
async def analysis(
        # 接收前端数据
        user_id: int = Form(default=0),
        grade: int = Form(default=0),
        requirements: str = Form(default=""),
        upload_time: str = Form(default=""),
        analysis_text: str = Form(default=""),
        task_id: int = Form(default=0),
        db: Session = Depends(get_db)  # 注入数据库会话
):
    print("task_id:", task_id)
    """
    流式作文分析接口
    返回 Server-Sent Events (SSE) 格式
    """
    # 检查必要参数
    if not analysis_text:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "message": "缺少作文文本内容",
                "data": None
            }
        )

    async def generate_stream():
        """
        生成流式响应
        """
        try:
            # 调用流式分析服务
            async for chunk in analyze_composition_text(
                    text=analysis_text,
                    grade=grade,
                    requirements=requirements,
                    upload_time=upload_time
            ):
                # 格式化SSE消息
                event_name = chunk.get("event")  # "message":默认值
                complete = chunk.get("complete", False)
                print(f"📨 收到事件: {event_name}, complete: {complete}")
                if event_name == "error":
                    # 错误事件
                    data_str = json.dumps({
                        "code": 500,
                        "message": chunk.get("data", {}).get("message", "未知错误"),
                        "data": chunk.get("data", {}),
                        "event": event_name,
                        "complete": True
                    }, ensure_ascii=False)  # ensure_ascii=False：支持中文编码
                elif event_name in ["message", "sum_json", "start", "final_result"]:
                    # 正常事件：message、sum_json、start、final_result
                    data_str = json.dumps({
                        "code": 200,
                        "message": "处理中",
                        "data": chunk.get("data", {}),
                        "event": event_name,
                        "complete": chunk.get("complete", False)
                    }, ensure_ascii=False)
                else:
                    # 其他未知事件
                    data_str = json.dumps({
                        "code": 200,
                        "message": "处理中",
                        "data": chunk.get("data", {}),
                        "event": event_name or "unknown",  # 保留原event或使用默认
                        "complete": chunk.get("complete", False)
                    }, ensure_ascii=False)
                # SSE格式: event: {event_name}\ndata: {data}\n\n
                yield f"event: {event_name}\n"
                yield f"data: {data_str}\n\n"
                await asyncio.sleep(0.001)  # 关键！触发协程切换，刷新输出
                # 如果完成，结果存入数据库，并结束流
                if chunk.get("complete", False):
                    print(f"✅ 收到complete=True的事件: {event_name}")
                    if event_name == "final_result":
                        print("🎯 收到final_result，准备保存数据库")
                        print("final_result:", chunk)
                        correction_data = chunk.get("data", {})  # 批改的最终结果
                        if correction_data:
                            from app.schemas.comments import CommentCreate  # 数据库
                            from app.schemas.essays import EssayCreate
                            from datetime import datetime
                            # 🔴 将字符串转换为 datetime 对象
                            upload_time_str = correction_data.get("upload_time")
                            if upload_time_str:
                                try:
                                    # 前端格式: "2026-02-24 15:30"
                                    upload_date = datetime.strptime(upload_time_str, "%Y-%m-%d %H:%M")
                                    print(f"✅ 日期转换成功: {upload_date}")
                                except Exception as e:
                                    print(f"❌ 日期转换失败: {e}，使用当前时间")
                                    upload_date = datetime.now()
                            else:
                                upload_date = datetime.now()
                                print(f"📅 没有上传时间，使用当前时间: {upload_date}")
                            essay_data = EssayCreate(
                                user_id=user_id,
                                task_id=task_id if task_id > 0 else None,
                                word_count=correction_data.get("words_count"),
                                upload_date=upload_date,
                                grade=grade,
                                requirement=correction_data.get("requirements"),
                                title=correction_data.get("title"),
                                paragraphs=correction_data.get("paragraphs")
                            )
                            try:
                                saved_essay = DataService.save_essay(db, essay_data)
                                print(f"📝 保存essay成功，ID: {saved_essay.id if saved_essay else '无'}")
                                if saved_essay and saved_essay.id:
                                    essay_id = saved_essay.id
                                    from app.schemas.comments import CommentCreate
                                    # 保存comment且修复
                                    comment_create = CommentCreate(
                                        essay_id=essay_id,
                                        comment_details=correction_data.get("comment"),  # 对应 comment_details
                                        scores=correction_data.get("scores"),  # 对应 scores（JSON）
                                        sum=correction_data.get("sum")
                                    )
                                    DataService.save_comment(db, comment_create)
                                    # 修复5：手动提交事务
                                    db.commit()
                                    print("✅ essay和comment数据存储成功（已提交事务）")
                                else:
                                    print("❌ 保存essay失败：返回的saved_essay为空或无ID")
                            except Exception as e:
                                db.rollback()
                                print(f"❌ 数据库存储失败：{str(e)}")
                                # 打印完整错误栈，定位具体问题
                                import traceback
                                print(f"完整错误栈：{traceback.format_exc()}")
                    break

        except Exception as e:
            # 错误处理
            error_data = json.dumps({
                "code": 500,
                "message": f"分析失败: {str(e)}",
                "data": None,
                "event": "error",
                "complete": True
            }, ensure_ascii=False)
            yield f"event: error\n"
            yield f"data: {error_data}\n\n"

    # 返回流式响应
    return StreamingResponse(
        generate_stream(),  # 异步生成器
        media_type="text/event-stream",  # 响应类型为SSE
        headers={
            "Cache-Control": "no-cache",  # 禁止浏览器 / 代理服务器缓存响应数据
            "Connection": "keep-alive",  # 保持 HTTP 长连接
            "X-Accel-Buffering": "no", # 禁用Nginx缓冲
            "Transfer-Encoding": "chunked"  # 强制分块传输
        }
    )

