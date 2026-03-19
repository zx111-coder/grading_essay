# app/services/ocr_service.py
import base64
from app import APP_CONFIG  # 导入全局配置字典
import io  # 处理内存流
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入通用高精度OCR的模块（腾讯云官方命名）
from tencentcloud.ocr.v20181119 import ocr_client, models
# 导入图片预处理
from app.services.image_preprocessor import preprocess_image_for_ocr


def ocr_image(image_stream):
    """
    调用腾讯云通用高精度OCR识别图片文字
    :param image_path: 本地图片文件路径（如app/static/uploads/xxx.png）
    :return: 拼接后的识别文字 / 错误提示
    """
    try:
        # 核心修复：移到函数内部获取配置，此时上下文已激活，且修正get语法
        # 从配置中获取腾讯云参数，get方法可设置默认值
        TENCENT_SECRET_ID = APP_CONFIG.get('TENCENT_SECRET_ID')
        TENCENT_SECRET_KEY = APP_CONFIG.get('TENCENT_SECRET_KEY')
        TENCENT_REGION = APP_CONFIG.get('TENCENT_OCR_REGION')
        # 新增：配置空值判断，提前抛出明确错误，避免腾讯云SDK无意义报错
        if not all([TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_REGION]):
            return {
                "success": False,
                "error": "OCR配置错误：腾讯云SecretId/SecretKey/Region未配置，请检查配置",
                "text": "",
                "text_lines": []
            }
        processed_base64 = preprocess_image_for_ocr(image_stream)
        if processed_base64:
            # 使用预处理后的图片
            image_base64 = processed_base64
        else:
            # 如果预处理失败，回退到原图（从内存流读取）
            # 重置流的指针到开头（避免读取空内容）
            image_stream.seek(0)
            image_base64 = base64.b64encode(image_stream.read()).decode("utf-8")
        # 2. 初始化腾讯云鉴权凭证
        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        # 3. 初始化OCR客户端
        client = ocr_client.OcrClient(cred, TENCENT_REGION)

        # 4. 构造OCR请求参数（指定base64图片，开启文字行拼接）
        req = models.GeneralAccurateOCRRequest()
        req.ImageBase64 = image_base64  # 核心参数：图片base64编码

        # 5. 调用腾讯云OCR接口，获取响应
        resp = client.GeneralAccurateOCR(req)

        # 6. 解析响应结果
        if resp.TextDetections:
            text_lines = []
            for item in resp.TextDetections:
                # 确保坐标信息存在
                polygon = [{"x": pt.X, "y": pt.Y} for pt in item.Polygon] if hasattr(item, 'Polygon') else []
                text_lines.append({
                    "text": item.DetectedText,
                    "confidence": item.Confidence,
                    "polygon": polygon
                })

            # --- 【核心新增部分：基于首行缩进的智能段落重组】---
            if text_lines:
                # 步骤1：按行排序（从上到下，从左到右）
                text_lines.sort(key=lambda line: (
                    line['polygon'][0]['y'] if line['polygon'] and len(line['polygon']) > 0 else 0,
                    line['polygon'][0]['x'] if line['polygon'] and len(line['polygon']) > 0 else 0
                ))

                # 步骤2：计算“基准左边界”和“缩进阈值”
                # 找出所有行的大致左边界（取多边形最左点的X坐标）
                left_margins = []
                for line in text_lines:
                    if line['polygon']:
                        # 取多边形所有点中X坐标的最小值作为该行的左边界
                        left_x = min(point['x'] for point in line['polygon'])
                        left_margins.append(left_x)

                if not left_margins:
                    # 如果没有坐标信息，回退到简单拼接
                    ocr_text = "\n".join([line["text"] for line in text_lines])
                else:
                    # 计算一个参考的左边界（例如，取所有左边界的中位数或众数，以避免异常值影响）
                    import statistics
                    try:
                        baseline_left = statistics.median(left_margins)
                    except:
                        baseline_left = sum(left_margins) / len(left_margins)  # 如果出错用平均值

                    # 定义“缩进阈值”：比基准左边界大多少像素算作一个段落的开始？
                    # 这个值需要根据你的图片DPI和字体大小调整。对于标准截图，15-30像素可能是个合理的起始值。
                    indent_threshold_px = 25  # 【关键参数！可能需要调整】

                    # 步骤3：根据缩进重组段落
                    merged_paragraphs = []
                    current_paragraph = ""

                    for line in text_lines:
                        line_text = line["text"].strip()
                        if not line_text:  # 跳过空行
                            continue

                        if line['polygon']:
                            line_left = min(point['x'] for point in line['polygon'])
                            # 判断该行是否有明显缩进
                            is_indented = (line_left - baseline_left) > indent_threshold_px
                        else:
                            # 如果没有坐标信息，尝试根据文本开头是否有两个空格判断
                            is_indented = line["text"].startswith("  ")

                        # 如果当前行为空，或者检测到缩进，则开始一个新的段落
                        if not current_paragraph:
                            current_paragraph = line_text
                        elif is_indented:
                            # 当前行有缩进，说明是新段落
                            merged_paragraphs.append(current_paragraph)
                            current_paragraph = line_text
                        else:
                            # 否则，认为是同一段落内的换行，直接拼接（可以加个空格）
                            current_paragraph += line_text

                    # 不要忘记添加最后一个段落
                    if current_paragraph:
                        merged_paragraphs.append(current_paragraph)

                    # 步骤4：将合并后的段落用两个换行符连接，形成清晰的段落分隔
                    ocr_text = "\n\n".join(merged_paragraphs)
            # --- 【段落重组结束】---

            # 返回结果
            return {
                "success": True,
                "text": ocr_text,  # 这是重组后的、分段正确的文本
                "text_lines": text_lines,  # 原始行数据，可用于调试
                "language": resp.Language if hasattr(resp, 'Language') else "zh"
            }
        else:
            return {
                "success": False,
                "error": "未识别到文字",
                "text": "",
                "text_lines": []
            }
    except TencentCloudSDKException as e:
        return {
            "success": False,
            "error": f"腾讯云OCR调用失败：{e.message}",
            "text": "",
            "text_lines": []
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "OCR识别失败：图片文件不存在",
            "text": "",
            "text_lines": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR识别失败：{str(e)}",
            "text": "",
            "text_lines": []
        }