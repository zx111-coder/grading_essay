import base64
from PIL import Image, ImageEnhance, ImageFilter
import io


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