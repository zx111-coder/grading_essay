# app/service/coze_workflow_stream.py
"""
使用官方 cozepy SDK 的工作流服务
只支持流式响应
"""
import asyncio
from typing import AsyncGenerator, Dict, Any
import json
from app import APP_CONFIG
from cozepy import Coze, TokenAuth, WorkflowEventType, COZE_CN_BASE_URL


# ============ 配置管理 ============
def get_coze_config() -> Dict[str, str]:  # 返回值是一个字典
    """获取扣子配置"""
    return {
        "api_token": APP_CONFIG.get("COZE_API_TOKEN"),
        "workflow_id": APP_CONFIG.get("COZE_WORKFLOW_ID")
    }


def get_coze_client() -> Coze:
    """获取扣子客户端实例"""
    config = get_coze_config()
    return Coze(
        auth=TokenAuth(token=config["api_token"]),
        base_url=COZE_CN_BASE_URL  # 使用官方SDK的中国区URL
    )


# ============ 核心流式调用函数 ============
async def stream_workflow_execution(
        requirements: str,
        words_count: int,
        paragraphs: list[str],
        paragraph_count: int,
        essay: str,
        grade: int = 0
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    流式执行工作流（使用官方SDK）
    返回格式：{"event": "message/error/done", "data": {...}, "complete": bool}
    """
    config = get_coze_config()
    coze = get_coze_client()
    try:
        # 调用工作流流式接口
        stream = coze.workflows.runs.stream(
            workflow_id=config["workflow_id"],
            parameters={
                "input": {
                    "topic_requirement": requirements,
                    "words_count": words_count,
                    "paragraphs": paragraphs,
                    "paragraph_count": paragraph_count,
                    "grade": grade,
                    "essay": essay
                }
            }
        )
        print(f"✅ stream对象已创建: {stream}")
        # 变量
        is_json_started = False  # 标记JSON开始收集
        json_buffer = ""  # 专门收集JSON的字符串
        json_sent = False  # 标记JSON是否已发送
        event_count = 0
        last_event_processed = False  # 标记是否处理了最后一个事件

        for event in stream:
            event_count += 1
            print("event:", event)

            if event.event == WorkflowEventType.MESSAGE:
                current_message = event.message.content or ""
                is_finish = getattr(event.message, 'node_is_finish', False)

                if not is_json_started:
                    json_start_index = current_message.find("{")
                    if json_start_index != -1:
                        content_to_send = current_message[:json_start_index]
                        is_json_started = True
                        json_buffer += current_message[json_start_index:]
                    else:
                        content_to_send = current_message

                    # 推送文本内容，推完立刻刷新
                    if content_to_send.strip():
                        yield {
                            "event": "message",
                            "data": {
                                "message": content_to_send,
                                "type": "text"
                            },
                            "complete": False
                        }
                        # ✅ 关键：yield后立即异步刷新，强制推给前端
                        await asyncio.sleep(0.001)
                else:
                    json_buffer += current_message

                # 处理最后一个事件
                if is_finish:
                    try:
                        first_brace = json_buffer.find("{")
                        last_brace = json_buffer.rfind("}")
                        if first_brace != -1 and last_brace != -1 and not json_sent:
                            clean_json_str = json_buffer[first_brace:last_brace + 1]
                            sum_json = json.loads(clean_json_str)
                            # 推送JSON数据，推完刷新
                            yield {
                                "event": "sum_json",
                                "data": {
                                    "message": sum_json,
                                    "type": "json"
                                },
                                "complete": False
                            }
                            await asyncio.sleep(0.001)
                            json_sent = True
                    except json.JSONDecodeError as e:
                        yield {
                            "event": "error",
                            "data": {
                                "error": "JSON解析失败",
                                "message": str(e),
                                "raw_json_str": json_buffer
                            },
                            "complete": False
                        }
                        await asyncio.sleep(0.001)
                    last_event_processed = True
                    break

            elif event.event == WorkflowEventType.ERROR:
                yield {
                    "event": "error",
                    "data": {
                        "error_code": "WORKFLOW_ERROR",
                        "message": str(event.error)
                    },
                    "complete": True
                }
                await asyncio.sleep(0.001)
                break

            elif event.event == WorkflowEventType.INTERRUPT:
                yield {
                    "event": "interrupt",
                    "data": {
                        "event_id": event.interrupt.interrupt_data.event_id,
                        "interrupt_type": event.interrupt.interrupt_data.type,
                        "message": "需要用户交互"
                    },
                    "complete": False
                }
                await asyncio.sleep(0.001)
                break

            if last_event_processed:
                break

        print(f"📊 总共收到 {event_count} 个事件")

    except Exception as e:
        yield {
            "event": "error",
            "data": {
                "error_code": "EXCEPTION",
                "message": f"流式请求异常: {str(e)}"
            },
            "complete": True
        }
        await asyncio.sleep(0.001)


def extract_analysis_from_stream(messages: list) -> Dict[str, Any]:
    """
    从流式消息中提取分析结果
    这个函数需要根据你工作流实际返回的消息格式进行调整
    """

    if not messages:
        return {
            "comment": "",
            "sum": "",
            "scores": {
                "score": 0,
                "content": 0,
                "structure": 0,
                "language": 0,
                "basic": 0,
            },
        }
    # 将所有消息拼接成一个完整的文本
    full_text = ""
    full_json = {}
    for msg in messages:
        if isinstance(msg, dict):
            if msg.get("type") == "text":
                full_text += msg.get("message", "")
            elif msg.get("type") == "json":
                full_json = msg.get("message", {})

    # 默认返回
    return {
        "comment": full_text,
        "sum": full_json.get("sum", ""),
        "scores": full_json.get("scores", "")
    }


