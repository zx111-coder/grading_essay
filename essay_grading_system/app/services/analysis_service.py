# app/services/analysis_service.py
from datetime import datetime
from typing import AsyncGenerator
from typing import Dict, Any
from .coze_workflow_stream import (
    stream_workflow_execution,  # 调用工作流
    extract_analysis_from_stream
)
from app.utils.essay_handle import essay_handle


async def analyze_composition_text(text='', grade=None, requirements="", upload_time=None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Args:
        text: 作文文本内容
        grade: 单个年级（数字），如 3 表示三年级
        requirements: 作文要求
        upload_time: 上传时间
    Returns:
        分析结果字典
    """
    # 生成分析ID
    # analysis_id = str(uuid.uuid4())
    # 基础分析
    paragraphs = essay_handle(text).get('paragraphs', '')
    paragraph_count = essay_handle(text).get('paragraph_count', 0)
    words_count = essay_handle(text).get('words_count', 0)

    # 开始分析，发送初始信息
    yield {
        "event": "start",
        "data": {
            # "analysis_id": analysis_id,
            "status": "processing",
            "message": "开始分析作文..."
        },
        "complete": False
    }
    # 收集流式消息（用于后续提取结构化结果）
    collected_messages = []
    try:
        # 调用底层的 Coze 工作流流式接口
        print("开始调用底层的 Coze 工作流流式接口")
        async for event in stream_workflow_execution(
                requirements=requirements,
                words_count=words_count,
                paragraphs=paragraphs,
                paragraph_count=paragraph_count,
                grade=grade,
                essay=text
        ):
            # 1. 直接转发底层事件（如 message/error/done 等）给调用方
            yield event

            # 2. 收集 message 类型的事件，用于后续提取最终结构化结果
            if event.get("event") in ["message", "sum_json"]:
                collected_messages.append(event.get("data", {}))

            # # 3. 如果底层流结束（complete=True），终止循环
            # if event.get("complete", False):
            #     break

        # 流结束后，提取结构化分析结果
        analysis_result = extract_analysis_from_stream(collected_messages)

        # 发送最终结果
        yield {
            "event": "final_result",
            "data": {
                # "analysis_id": analysis_id,
                "title": paragraphs[0][:10] + "..." if len(paragraphs[0]) > 10 else paragraphs[0],
                'essay': text,
                "paragraphs": paragraphs,
                "words_count": words_count,
                "requirements": requirements if requirements else "无",
                "grade": grade,
                "upload_time": upload_time or datetime.now().isoformat(),
                "comment": analysis_result.get("comment"),
                "sum": analysis_result.get("sum"),
                "scores": analysis_result.get("scores")
            },
            "complete": True
        }
    except Exception as e:
        # 错误处理
        yield {
            "event": "error",
            "data": {
                # "analysis_id": analysis_id,
                "error_code": "SERVICE_ERROR",
                "message": f"分析服务异常: {str(e)}"
            },
            "complete": True
        }

