import os
import statistics
import uuid
from app import APP_CONFIG
import pdfplumber
from docx import Document


# 允许的文件后缀

def allowed_file(filename):
    """检查文件后缀是否合法"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in APP_CONFIG['ALLOWED_EXTENSIONS']


def get_unique_filename(filename):
    """生成唯一文件名，避免覆盖"""
    suffix = filename.rsplit('.', 1)[1].lower()
    prefix = str(uuid.uuid4())
    return f"{prefix}.{suffix}"


def ensure_upload_folder_exists(upload_folder):
    """确保上传目录存在，不存在则创建"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)


def read_pdf(file_stream):
    """
    读取PDF文件内容（从内存流），基于行级坐标进行缩进分段
    :param file_stream: PDF内存流（BytesIO）【关键修改：不再是文件路径】
    :return: 分段后的文本 / 错误提示
    """
    try:
        # 存储所有行数据（格式与OCR的text_lines一致）
        all_lines = []
        # 关键修改：从内存流打开PDF
        with pdfplumber.open(file_stream) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 关键：提取带坐标的文本行
                text_lines = page.extract_text_lines()

                if not text_lines:
                    continue

                for line in text_lines:
                    # 提取文本和坐标信息
                    text = line['text'].strip()
                    if not text:  # 跳过空行
                        continue

                    # 获取行的边界框坐标
                    x0, top, x1, bottom = line['x0'], line['top'], line['x1'], line['bottom']

                    # 构建与OCR返回格式一致的数据结构
                    all_lines.append({
                        "text": text,
                        # 模拟OCR的多边形坐标（矩形框的四个顶点）
                        "polygon": [
                            {"x": x0, "y": top},  # 左上
                            {"x": x1, "y": top},  # 右上
                            {"x": x1, "y": bottom},  # 右下
                            {"x": x0, "y": bottom}  # 左下
                        ],
                        # 保存原始坐标用于调试
                        "_raw_coords": {"x0": x0, "top": top, "x1": x1, "bottom": bottom}
                    })

        if not all_lines:
            return "PDF文件中未识别到文字"

        # --- 【核心：应用与图片OCR完全相同的缩进检测算法】---
        text_lines = all_lines

        # 按垂直位置排序（从上到下）
        text_lines.sort(key=lambda line: line['polygon'][0]['y'])

        # 1. 计算所有行的左边界
        left_margins = []
        for line in text_lines:
            if line['polygon']:
                # 取多边形最左边的X坐标（即左上角点的x值）
                left_x = line['polygon'][0]['x']
                left_margins.append(left_x)

        if not left_margins:
            # 如果没有坐标信息，回退到简单拼接
            ocr_text = "\n".join([line["text"] for line in text_lines])
            return ocr_text

        # 2. 计算基准左边界（使用中位数减少异常值影响）
        try:
            baseline_left = statistics.median(left_margins)
        except:
            baseline_left = sum(left_margins) / len(left_margins)

        # 3. 缩进阈值设置（关键参数！）
        # 初始值设为20，需要根据你的PDF调整
        indent_threshold_px = 20

        # 4. 根据缩进重组段落
        merged_paragraphs = []
        current_paragraph = ""

        for i, line in enumerate(text_lines):
            line_text = line["text"]

            if line['polygon']:
                # 获取当前行的左边界
                line_left = line['polygon'][0]['x']
                # 判断是否有明显缩进
                is_indented = (line_left - baseline_left) > indent_threshold_px

                # 调试信息：打印前几行的缩进情况
                if i < 5:
                    indent_diff = line_left - baseline_left
                    print(
                        f"调试 - 第{i}行: '{line_text[:30]}...' | 左边界={line_left:.1f} | 基准={baseline_left:.1f} | 差值={indent_diff:.1f} | 是否缩进={is_indented}")
            else:
                # 回退方案：根据文本开头的空格判断
                is_indented = line_text.startswith("  ") or line_text.startswith("　")

            # 段落重组逻辑
            if not current_paragraph:
                # 第一个段落开始
                current_paragraph = line_text
            elif is_indented:
                # 检测到缩进，开始新段落
                merged_paragraphs.append(current_paragraph.strip())
                current_paragraph = line_text
            else:
                current_paragraph += line_text

        # 添加最后一个段落
        if current_paragraph:
            merged_paragraphs.append(current_paragraph.strip())

        # 5. 用双换行符连接段落
        final_content = "\n\n".join(merged_paragraphs)
        # --- 【算法结束】---

        if not final_content.strip():
            return "PDF文件中未识别到文字"

        return final_content

    except Exception as e:
        return f"PDF读取失败：{str(e)}"


def read_docx(file_stream):
    """
    读取Word(.docx)文件内容（从内存流），完整保留原格式（段落换行+缩进）
    修复：ParagraphFormat无indent_first_line属性的问题
    :param file_stream: DOCX内存流（BytesIO）【关键修改：不再是文件路径】
    :return: 带格式的文本内容 / 错误提示
    """
    try:
        content = []  # 存储每个段落的处理结果（缩进+文本）
        # 关键修改：从内存流打开DOCX
        doc = Document(file_stream)  # 打开docx文件，返回Document对象

        for para in doc.paragraphs:
            para_text = para.text.strip()
            if not para_text:
                # 空段落：保留一个空行（\n\n）
                content.append("\n")
                continue

            # 获取首行缩进（返回的是Length对象）
            indent_obj = para.paragraph_format.first_line_indent

            # 转换为磅值（Pt）
            if indent_obj is not None:
                # 将缩进值转换为磅
                indent_pt = indent_obj.pt if hasattr(indent_obj, 'pt') else 0

                # 磅值转全角空格（经验值：1磅 ≈ 0.35mm，1个全角空格≈2磅）
                # 常用规则：28.35磅=1厘米，首行缩进通常2字符≈1厘米
                if indent_pt >= 14:  # 约半个字符
                    indent_spaces = "\u3000\u3000"  # 2个全角空格
                elif indent_pt > 0:
                    indent_spaces = "\u3000"  # 1个全角空格
                else:
                    indent_spaces = ""
            else:
                indent_spaces = ""

            # 拼接缩进+段落文本
            content.append(f"{indent_spaces}{para_text}\n")

        # 拼接所有段落
        formatted_content = '\n'.join(content).strip()
        return formatted_content if formatted_content else "Word文件中未识别到文字"

    except Exception as e:
        return f"Word(.docx)读取失败：{str(e)}"

# def read_doc(file_path):
#     """读取老版Word(.doc)文件内容"""
#     try:
#         import textract
#         # 自动检测文件类型并提取文本
#         text = textract.process(file_path).decode('utf-8')
#
#         # 简单的段落格式化（doc通常没有缩进信息）
#         paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
#         formatted_content = '\n'.join(paragraphs)
#
#         return formatted_content if formatted_content else "Word(.doc)文件中未识别到文字"
#     except ImportError:
#         return "请安装textract库: pip install textract"
#     except Exception as e:
#         return f"Word(.doc)读取失败：{str(e)}"
