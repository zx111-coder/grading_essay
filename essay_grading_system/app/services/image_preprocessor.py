# app/services/image_preprocessor.py
import base64
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io


def remove_noise_safe(binary):
    """
    安全去噪：只删真正的噪点，不删文字/标点/引号
    """
    # 连通域分析
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # 创建空白掩码
    mask = np.zeros_like(binary)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        aspect_ratio = max(w, h) / (min(w, h) + 1)

        # ===================== 核心规则 =====================
        # 1. 面积 < 8 的超级小点 → 一定是噪点 → 删除
        # 2. 面积 8~25 之间，但形状细长（不是圆形标点）→ 删除
        # 3. 面积 >25 或 小而圆 → 保留（文字/标点/引号）
        # ====================================================

        if area < 8:
            mask[labels == i] = 255
        elif 8 <= area < 25 and aspect_ratio > 3.0:
            mask[labels == i] = 255

    # 从二值图中减去噪点
    clean = cv2.subtract(binary, mask)
    return clean


def correct_skew_binary(binary):
    """
    自动纠斜：把斜着拍的作文摆正（专门针对黑底白字二值图）
    """
    # 1. 提取所有文字像素坐标
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) < 100:
        return binary  # 文字太少不纠斜

    # 2. 计算最小外接矩形 → 得到倾斜角度
    angle = cv2.minAreaRect(coords)[-1]

    # 3. 修正角度（适配文字方向）
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # 4. 旋转图像，自动摆正
    (h, w) = binary.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    corrected = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return corrected


def is_screenshot_image(image_stream):
    """
    纯PIL实现，无任何第三方危险库
    规则：有作文横线 = 手写 = 返回False
          无横线 = 截图 = 返回True
    任何情况都不会崩溃，不会影响流式响应
    """
    try:
        # 安全重置流
        image_stream.seek(0)

        # 打开图片并缩小小提升速度
        img = Image.open(image_stream).convert("L")
        img = img.resize((400, 400))

        # 检测水平横线（作文本最明显特征）
        line_detected = 0

        # 扫描多行水平像素，判断是否有整齐横线
        for y_pos in range(100, 300, 50):
            row_data = [img.getpixel((x, y_pos)) for x in range(50, 350)]

            # 统计平滑段：横线会非常平滑，手写不会
            smooth_segment = 0
            for i in range(1, len(row_data)):
                if abs(row_data[i] - row_data[i - 1]) < 30:
                    smooth_segment += 1

            # 平滑度极高 = 横线
            if smooth_segment > 280:
                line_detected += 1

        # 流复位
        image_stream.seek(0)

        # 有2条以上横线 → 作文本 → 手写
        if line_detected >= 2:
            print("【判断】有格子线 → 手写作文")
            return False
        else:
            print("【判断】无格子线 → 电子截图")
            return True

    # 捕获所有异常，绝不崩溃，不影响流式输出
    except Exception as e:
        print("图片判断安全异常，默认按手写处理:", str(e))
        image_stream.seek(0)
        return False


def preprocess_image_for_ocr(image_source):
    """
    对图片进行预处理，优化OCR识别效果
    :param image_source: 原始图片路径 OR BytesIO内存流对象（兼容两种输入）
    :return: 处理后的图片Base64字符串 / None（失败时）
    """
    try:
        # 兼容文件路径和内存流两种输入
        if isinstance(image_source, str):
            # 如果是字符串，判定为文件路径，按路径打开
            img = Image.open(image_source)
        else:
            # 如果是内存流（BytesIO），直接打开（先重置流指针到开头）
            image_source.seek(0)
            img = Image.open(image_source)

        # 1. 转换为灰度图 (减少颜色干扰)
        img = img.convert('L')

        # 2. 提高对比度 (让文字更突出)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)  # 2.0倍对比度，可根据效果调整

        # 3. 锐化 (让文字边缘更清晰)
        img = img.filter(ImageFilter.SHARPEN)

        # 4. 二值化 (黑白化，彻底分离文字和背景)
        # 阈值可根据情况调整，127是中值
        img = img.point(lambda x: 0 if x < 180 else 255, '1')  # '1' 模式为黑白

        # 5. 转换为Base64（保持与原有代码兼容）
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # 关闭图片释放资源
        img.close()
        return img_base64
    except Exception as e:
        print(f"图片预处理失败: {e}")
        # 如果预处理失败，返回None，让后续流程使用原图
        return None


if __name__ == "__main__":
    import cv2
    import numpy as np
    import base64
    import io
    import os

    folder_path = r"C:\Users\Administrator\Desktop\毕设\作文数据\初中作文"

    image_files = "图1.jpg"

    if image_files:
        image_path = r"C:\Users\Administrator\Desktop\毕设\作文数据\初中作文\图1.jpg"
        print(f"处理图片: {image_path}")

        with open(image_path, 'rb') as f:
            image_stream = io.BytesIO(f.read())

        result_base64 = preprocess_image_for_ocr(image_stream)

        if result_base64:
            img_data = base64.b64decode(result_base64)
            img_array = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            output_path = r"C:\Users\Administrator\Desktop\denoised_image.png"
            cv2.imwrite(output_path, img)
            print(f"预处理后的图片已保存到: {output_path}")

            cv2.imshow("Denoised Image (涂鸦已去除)", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("预处理失败")
    else:
        print(f"文件夹内没有找到图片: {folder_path}")


# 检测删除线（生成横线掩码）
def get_strike_line_mask(binary_img):
    """
    只提取横线，不处理格子线
    格子线我们靠【位置判断】过滤
    """
    # 抓长横线（你要的长删除线）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    lines = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=1)

    # 轻微膨胀，让线连续一点
    lines = cv2.dilate(lines, np.ones((1, 4), np.uint8), iterations=1)
    return lines


# 判断文字是否被划掉
def is_word_struck_out(polygon, strike_mask):
    """
    输入：字的4个坐标 polygon + 横线掩码
    输出：True = 被划掉，False = 正常
    """
    # 1. 如果没有坐标，直接返回：不是删除字
    if not polygon or len(polygon) < 4:
        return False
    # 2. 计算这个字的 左、上、右、下 坐标（包围盒）
    x_min = int(min(p["x"] for p in polygon))
    y_min = int(min(p["y"] for p in polygon))
    x_max = int(max(p["x"] for p in polygon))
    y_max = int(max(p["y"] for p in polygon))

    # 3. 过滤太小的异常区域
    if x_max - x_min < 5 or y_max - y_min < 5:
        return False

    # 4. 在横线掩码图上，把“这个字的区域”切出来
    crop = strike_mask[y_min:y_max, x_min:x_max]
    h = crop.shape[0]
    if h < 10:
        return False

    start_y = int(h * 0.25)
    end_y = int(h * 0.75)

    # 截取中间区域
    middle_crop = crop[start_y:end_y, :]
    if middle_crop.size == 0:
        return False

    # 4. 统计中间区域的横线像素占比
    white_ratio = cv2.countNonZero(middle_crop) / middle_crop.size

    # 阈值：中间区域横线占比 > 8% 才判定为被划掉
    return white_ratio > 0.08