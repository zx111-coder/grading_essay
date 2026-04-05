# app/services/ocr_service.py
import base64
from app import APP_CONFIG  # 导入全局配置字典
import statistics
import numpy as np
import cv2
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入通用高精度OCR的模块（腾讯云官方命名）
from tencentcloud.ocr.v20181119 import ocr_client, models
# 导入图片预处理
from app.services.image_preprocessor import is_screenshot_image, preprocess_image_for_ocr, get_strike_line_mask, \
    is_word_struck_out


# ===================== 作文专属优化函数（核心，确保准确度）=====================
def optimize_essay_text(ocr_text):
    """
    作文专属优化：删除冗余字符、修正OCR识别错误、规整分段，保留学生真实错别字
    核心逻辑：只修正OCR识别导致的明显误写（如形近字、音近字识别偏差），不修正学生真实写错的字
    """
    # 1. 删除冗余字符（修正栏、修正柱、无效符号等，适配作文批改场景）
    redundant_chars = ["修正栏", "修正柱", "修正", "IN", "in"]
    for char in redundant_chars:
        ocr_text = ocr_text.replace(char, "")
    import re
    ocr_text = re.sub(r'\d+x\d+=\d+', '', ocr_text)  # 删除 16x25=400 这类算式
    ocr_text = re.sub(r'[<>|]', '', ocr_text)  # 删除特殊符号
    # 2. 只修正【OCR识别错误】（不修正学生真实错别字）
    # 仅修正：OCR大概率识别偏差的形近字、音近字，学生不可能主动写错的搭配
    ocr_error_correction = {
        # OCR常见识别错误（学生不会主动这么写）
        "甚致至": "甚至",  # OCR多识别一个字，非学生错误
        "看着完": "看完",  # OCR语序识别错误，非学生错误
        "自过我": "自己",  # OCR笔画识别偏差，非学生错误
        ".": "。",
        "I": "",
        "9120": ""
    }
    # 循环替换，不拆词，避免误改学生真实书写
    for wrong, correct in ocr_error_correction.items():
        ocr_text = ocr_text.replace(wrong, correct)
    # 3. 清理多余空格（但保留段落结构）
    ocr_text = ocr_text.replace(" ", "").strip()
    return ocr_text


# ===================== 辅助函数：区分OCR错误和学生错别字（可选调用）=====================
def get_ocr_errors(original_ocr, optimized_ocr):
    """
    对比优化前后的文本，提取OCR识别错误（供老师参考，避免误判学生）
    返回：OCR识别错误列表，格式[{"错误文字": "xxx", "修正后": "xxx"}]
    """
    errors = []
    # 简单对比，提取差异（仅针对OCR识别错误的修正）
    if original_ocr != optimized_ocr:
        # 按字符对比，筛选出OCR修正的部分（简化逻辑，适配作文场景）
        original_chars = list(original_ocr)
        optimized_chars = list(optimized_ocr)
        min_len = min(len(original_chars), len(optimized_chars))
        for i in range(min_len):
            if original_chars[i] != optimized_chars[i]:
                # 避免单个字符偏差误判，取前后各1个字符对比
                original_context = original_ocr[max(0, i - 1):min(len(original_ocr), i + 2)]
                optimized_context = optimized_ocr[max(0, i - 1):min(len(optimized_ocr), i + 2)]
                errors.append({
                    "错误文字": original_context,
                    "修正后": optimized_context,
                    "说明": "推测为OCR识别错误，非学生真实错别字"
                })
    return errors


# 手写图片
def hand_ocr_image(image_stream):
    """
    调用腾讯云通用高精度OCR识别图片文字
    """
    try:
        # 获取配置
        TENCENT_SECRET_ID = APP_CONFIG.get('TENCENT_SECRET_ID')
        TENCENT_SECRET_KEY = APP_CONFIG.get('TENCENT_SECRET_KEY')
        TENCENT_REGION = APP_CONFIG.get('TENCENT_OCR_REGION')

        if not all([TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_REGION]):
            return {
                "success": False,
                "error": "OCR配置错误",
                "text": "", "text_lines": [], "ocr_errors": []
            }

        processed_base64 = None
        if processed_base64:
            print("图片预处理成功")
            image_base64 = processed_base64
        else:
            image_stream.seek(0)
            image_base64 = base64.b64encode(image_stream.read()).decode("utf-8")

        # ===================== 【生成删除线掩码】 =====================
        image_stream.seek(0)
        img_array = np.frombuffer(image_stream.read(), np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        strike_mask = get_strike_line_mask(binary)

        # 初始化腾讯云客户端
        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        client = ocr_client.OcrClient(cred, TENCENT_REGION)

        # 构造请求
        req = models.GeneralAccurateOCRRequest()  # 创建OCR请求对象
        req.ImageBase64 = image_base64  # 传入图片（Base64）
        req.EnableDetectSplit = True  # 开启“分段检测”
        req.IsWords = True  # 开启“按单词/单字返回”

        resp = client.GeneralAccurateOCR(req)  # 发给阿里云 OCR 服务器
        # 解析结果
        if resp.TextDetections:
            text_lines = []

            for item in resp.TextDetections:
                if item.Confidence < 50:
                    continue

                line_text = item.DetectedText
                words = item.Words
                coord_points = item.WordCoordPoint if hasattr(item, 'WordCoordPoint') else []

                kept_chars = []
                max_idx = min(len(words), len(coord_points))

                for idx in range(max_idx):
                    word = words[idx]
                    coord = coord_points[idx]
                    char = word.Character

                    polygon = [{"x": pt.X, "y": pt.Y} for pt in coord.WordCoordinate]

                    # 被划掉就不保留
                    if not is_word_struck_out(polygon, strike_mask):
                        kept_chars.append(char)

                cleaned_text = ''.join(kept_chars)

                text_lines.append({
                    "text": cleaned_text,
                    "confidence": item.Confidence,
                    "polygon": [{"x": pt.X, "y": pt.Y} for pt in item.Polygon]
                })

            # ===================== 基于缩进的段落重组 =====================
            if text_lines:
                # 1. 给每个块计算中心点Y和左边界X（稳定排序的基础）
                for line in text_lines:
                    if line['polygon']:
                        ys = [p['y'] for p in line['polygon']]
                        xs = [p['x'] for p in line['polygon']]
                        line['center_y'] = sum(ys) / len(ys)
                        line['left_x'] = min(xs)
                    else:
                        line['center_y'] = 0
                        line['left_x'] = 0

                # 2. 按中心点Y排序（解决乱序），同一行按左边界X排序
                text_lines.sort(key=lambda x: (round(x['center_y'], -1), x['left_x']))

                # 3. 合并同一行的所有碎块（最关键！）
                merged_lines = []
                current_line = None
                # 你的作文格子用 25-30 最合适，防止行内碎块被分到下一行
                line_merge_threshold = 28

                for line in text_lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    if current_line is None:
                        current_line = {
                            'text': text,
                            'left_x': line['left_x'],
                            'center_y': line['center_y']
                        }
                    else:
                        # 判断Y坐标差距是否在合并阈值内
                        if abs(line['center_y'] - current_line['center_y']) < line_merge_threshold:
                            # 合并碎块（追加空格保证单词间分离）
                            current_line['text'] += " " + text
                            current_line['left_x'] = min(current_line['left_x'], line['left_x'])
                        else:
                            # 差距大，说明是新的一行，把当前行存入结果
                            merged_lines.append(current_line)
                            current_line = {
                                'text': text,
                                'left_x': line['left_x'],
                                'center_y': line['center_y']
                            }
                # 循环结束后，把最后一行加进去
                if current_line:
                    merged_lines.append(current_line)

                # 4. 计算基准左边界（用合并后的行，极度准确）
                left_margins = [l['left_x'] for l in merged_lines if l['left_x'] > 0]
                if not left_margins:
                    raw_ocr_text = "\n".join([l['text'] for l in merged_lines])
                else:
                    # 取中位数作为基准，稳定抗干扰
                    baseline_left = statistics.median(left_margins)
                    # 缩进阈值：针对方格本，两个字宽度建议 35-40
                    indent_threshold_px = 38

                    # 5. 纯缩进分段（无任何智能判断，你要的方式）
                    paragraphs = []
                    current_para = []

                    for line in merged_lines:
                        text = line['text'].strip()
                        if not text:
                            continue

                        # 只判断缩进
                        is_indented = (line['left_x'] - baseline_left) > indent_threshold_px

                        if is_indented:
                            # 有缩进是新段落，先保存上一段
                            if current_para:
                                paragraphs.append(''.join(current_para))
                            current_para = [text]
                        else:
                            # 无缩进，追加到当前段落
                            current_para.append(text)

                    # 保存最后一段
                    if current_para:
                        paragraphs.append(''.join(current_para))

                    # 段落之间用空行分隔
                    raw_ocr_text = "\n\n".join(paragraphs)

                # 5. 后续优化（你保留的代码）
                optimized_ocr_text = optimize_essay_text(raw_ocr_text)
                ocr_errors = get_ocr_errors(raw_ocr_text, optimized_ocr_text)
                return {
                    "success": True,
                    "text": optimized_ocr_text,
                    "original_ocr_text": raw_ocr_text,
                    "ocr_errors": ocr_errors,
                    "text_lines": text_lines,
                    "language": resp.Language if hasattr(resp, 'Language') else "zh"
                }
            else:
                return {
                    "success": False, "error": "未识别到文字",
                    "text": "", "original_ocr_text": "", "ocr_errors": [], "text_lines": []
                }
        else:
            return {
                "success": False, "error": "未识别到文字",
                "text": "", "original_ocr_text": "", "ocr_errors": [], "text_lines": []
            }

    except TencentCloudSDKException as e:
        return {
            "success": False, "error": f"腾讯云OCR调用失败：{e.message}",
            "text": "", "original_ocr_text": "", "ocr_errors": [], "text_lines": []
        }
    except Exception as e:
        return {
            "success": False, "error": f"OCR识别失败：{str(e)}",
            "text": "", "original_ocr_text": "", "ocr_errors": [], "text_lines": []
        }


# 截图图片
def screenshot_ocr_image(image_stream):
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


def ocr_image(image_stream):
    # 预处理图片
    iss = is_screenshot_image(image_stream)
    if iss:
        print("🖥️  判定为：截图 → 执行预处理")
        return screenshot_ocr_image(image_stream)
    else:
        print("✍️ 判定为：手写作文 → 不预处理（保持高精度）")
        return hand_ocr_image(image_stream)


