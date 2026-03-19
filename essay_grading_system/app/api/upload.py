# app/api/upload.py
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Request
from app.services.upload_service import process_upload
from app.utils.essay_handle import essay_handle
import logging
# 创建路由实例
router = APIRouter()
# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
print("🚀 upload.py 文件被加载了！")


@router.post("/upload")
async def upload(
        request: Request,  # 请求上下文，获取用户权限
        grade: str = Form(default=""),
        requirements: str = Form(default=""),
        files: list[UploadFile] = File(...)
):
    print("🔥🔥🔥 upload函数被调用！")

    try:
        # 调用异步函数
        result = await process_upload(grade, requirements, files)
        print("上传接口内容：", result)
        words_count = essay_handle(result["total_ocr_text"]).get('words_count', 0)
        essay = essay_handle(result["total_ocr_text"]).get('essay', "")
        # 构造响应
        response_data = {
            "code": 200,
            "msg": "文件上传并识别成功！",
            "data": {
                "grade": result["grade"],
                # "grade_label": f"{result['grade']}年级",
                "requirements": result["requirements"] if result["requirements"] else "无",
                "file_count": len(result["processed_files"]),
                "processed_files": result["processed_files"],
                "total_ocr_text": essay,
                "words_count": words_count
            }
        }
        return response_data

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "msg": str(e), "data": None}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": 500, "msg": f"操作失败：{str(e)}", "data": None}
        )
