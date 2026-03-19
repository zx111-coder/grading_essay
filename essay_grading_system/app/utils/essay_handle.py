# app/utils/essay_handle.py
import re


def essay_handle(text=''):
    if text:
        print("作文：", text)
        # 清洗文本
        clean_text = text.replace('\r', '').replace('\t', '')
        paragraphs = re.split(r'\n+', clean_text)
        paragraph_count = len([p for p in paragraphs if p.strip()])

        # 精确统计字数（匹配Word规则）
        words_count = count_words_like_word(clean_text)
    else:
        paragraphs = []
        paragraph_count = 0
        words_count = 0

    essay = '\n'.join(paragraphs)

    return {
        "paragraphs": paragraphs,
        "paragraph_count": paragraph_count,
        "words_count": words_count,
        "essay": essay
    }


def count_words_like_word(text):
    # 移除空格和换行符
    text = text.replace(' ', '').replace('\n', '')
    # 移除全角空格（中文空格）
    text = text.replace('　', '')  # 全角空格

    # 也可以移除其他不可见字符
    text = re.sub(r'[\u3000\xa0]', '', text)  # 全角空格和&nbsp;
    if not text:
        return 0

    # 将连续数字（如2024、3.14）替换为单个字符'N'
    text = re.sub(r'\d+(\.\d+)?', 'N', text)
    # 将连续的点号（省略号）替换为单个字符'.'
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'…{2,}', '…', text)
    # # 移除单边引号（一对为一个）
    # text = text.replace('“', '').replace('"', '')
    # # 处理破折号
    # text = re.sub(r'-{2,}', '—', text)
    # text = re.sub(r'—{2,}', '—', text)
    print("处理后的作文：", text)
    return len(text)
