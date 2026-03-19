# app/services/upload_service.py
import io  # 处理内存流
from app import APP_CONFIG  # 导入全局配置字典
from app.utils.file_utils import allowed_file, read_pdf, read_docx  # 已修改为支持内存流
from app.services.ocr_service import ocr_image  # 已修改为支持内存流


async def process_upload(grade, requirements, files):
    """处理上传业务：校验→内存读取文件→OCR识别（不保存文件）"""
    # 1. 基础校验
    if not files or files[0].filename == "":
        raise ValueError("请上传至少一个文件")
    if not grade or not grade.isdigit() or int(grade) not in range(1, 13):
        raise ValueError("请选择有效的年级（1-12）")
    grade = int(grade)

    # 2. 遍历处理文件
    processed_files = []
    total_ocr_text = ""
    ocr_support_types = {"jpg", "jpeg", "png"}
    doc_support_types = {"pdf", "docx"}
    for file in files:
        if file and allowed_file(file.filename):  # 检查文件后缀
            file_name = file.filename
            file_suffix = file_name.rsplit('.', 1)[1].lower()  # 文件后缀
            ocr_text = ""
            # 核心：读取文件二进制内容到内存，并转为BytesIO流
            file_content = await file.read()  # 异步读取文件内容
            file_stream = io.BytesIO(file_content)  # 转为内存流
            # 3. 根据文件类型处理
            if file_suffix in ocr_support_types:
                # 调用ocr_image传入内存流
                ocr_result = ocr_image(file_stream)
                if ocr_result.get("success"):
                    ocr_text = ocr_result.get("text", "")
                else:
                    ocr_text = f"[识别失败] {ocr_result.get('error', '未知错误')}"
                total_ocr_text += ocr_text

            elif file_suffix in doc_support_types:
                # 调用修改后的read_pdf/read_docx（传入内存流）
                if file_suffix == "pdf":
                    ocr_text = read_pdf(file_stream)
                else:
                    ocr_text = read_docx(file_stream)
                total_ocr_text += ocr_text

            else:
                ocr_text = f"只支持pdf、docx、jpg、jpeg、png格式的文件"

            # 记录文件信息（仅元数据，无路径/URL）
            processed_files.append({
                "original_name": file_name,
                "file_size": len(file_content),  # 内存中获取文件大小
                "ocr_text": ocr_text
            })
        else:
            raise ValueError(f"文件{file.filename}格式不支持！仅支持{APP_CONFIG['ALLOWED_EXTENSIONS']}")

    return {
        "grade": grade,
        "requirements": requirements,
        "processed_files": processed_files,
        "total_ocr_text": total_ocr_text.strip() if total_ocr_text else "无可识别的文件内容"
    }