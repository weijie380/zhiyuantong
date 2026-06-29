"""
一分一段表 OCR 解析器 v2

直接用 pytesseract + tesseract(chi_sim) 逐页 OCR。
PSM 11 模式识别表格结构。
"""

import re
import os
import json
import pytesseract
from PIL import Image
import pdfplumber
from pathlib import Path
from config import RAW_DIR, YEARS

os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

# OCR 常见数字错误映射
NUM_FIX = {'S': '5', 'O': '0', 'o': '0', 'l': '1', 'I': '1',
           'Z': '2', 'B': '8', 'G': '6', 'D': '0', 'q': '9'}


def fix_number(text):
    """修正 OCR 数字识别错误"""
    for k, v in NUM_FIX.items():
        text = text.replace(k, v)
    return text


def ocr_page_to_rankmap(img):
    """对单页图片做 PSM 11 OCR，提取 score→cumulative_rank 映射"""
    # 先检测科类
    header_text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 3')
    if '物理' in header_text:
        subject = 'physics'
    elif '历史' in header_text:
        subject = 'history'
    else:
        return None, []

    # PSM 11 提取带坐标的文本
    data = pytesseract.image_to_data(
        img, lang='chi_sim+eng', config='--psm 11',
        output_type=pytesseract.Output.DICT
    )

    words = []
    for i in range(len(data['text'])):
        t = data['text'][i].strip()
        conf = int(data['conf'][i])
        if t and conf > 15:
            words.append({
                'text': fix_number(t),
                'x': data['left'][i],
                'y': data['top'][i],
                'conf': conf,
            })

    words.sort(key=lambda w: (w['y'], w['x']))

    # 按 y 坐标分行
    rows = []
    cur_row = []
    cur_y = None
    for w in words:
        if cur_y is None or abs(w['y'] - cur_y) > 15:
            if cur_row:
                rows.append(cur_row)
            cur_row = [w]
            cur_y = w['y']
        else:
            cur_row.append(w)
    if cur_row:
        rows.append(cur_row)

    # 解析每行提取 score→cumulative
    results = []
    for row in rows:
        items = sorted(row, key=lambda w: w['x'])
        texts = [w['text'] for w in items]

        nums = []
        is_above = False
        for t in texts:
            if '及' in t or '以' in t or '上' in t:
                is_above = True
            cleaned = ''.join(c for c in t if c.isdigit())
            if cleaned:
                nums.append(int(cleaned))

        if len(nums) < 2:
            continue

        score = nums[0]
        if score < 300 or score > 750:
            continue

        if is_above:
            continue

        # 3列: score, count, cumulative
        if len(nums) >= 3:
            cumulative = nums[2]
            if cumulative > 0:
                results.append((score, cumulative))
        # 2列: score, cumulative（中间列漏了）
        elif len(nums) == 2:
            if nums[1] > 10:
                results.append((score, nums[1]))

    return subject, results


def parse_rank_pdf(filepath, year):
    """解析单个一分一段表 PDF"""
    print(f"  OCR: {filepath}")
    pdf = pdfplumber.open(filepath)
    total = len(pdf.pages)
    pdf.close()
    print(f"    共 {total} 页")

    rank_maps = {"physics": {}, "history": {}}

    for page_num in range(total):
        print(f"    第 {page_num + 1}/{total} 页...", end=" ")

        # 转图片
        with pdfplumber.open(filepath) as pdf2:
            page = pdf2.pages[page_num]
            im = page.to_image(resolution=150)
            tmp = f"/tmp/_ocr_{os.getpid()}_{page_num}.png"
            im.save(tmp)

        img = Image.open(tmp).convert('RGB')
        subject, results = ocr_page_to_rankmap(img)

        if subject and results:
            for score, cumulative in results:
                rank_maps[subject][score] = cumulative
            print(f"{subject}: +{len(results)} 条")
        else:
            print("无数据")

        # 清理临时文件
        try:
            os.remove(tmp)
        except OSError:
            pass

    return rank_maps


def parse_all_ranks():
    """解析所有年份"""
    print("\n" + "=" * 60)
    print("📊 OCR 解析一分一段表（v2）")
    print("=" * 60)

    all_rank_maps = {}

    for year in YEARS:
        print(f"\n--- {year} 年 ---")
        filepath = f"{RAW_DIR}/{year}_rank.pdf"
        if not Path(filepath).exists():
            print(f"  ⚠️ 文件不存在")
            all_rank_maps[year] = {"physics": {}, "history": {}}
            continue

        rank_maps = parse_rank_pdf(filepath, year)
        all_rank_maps[year] = rank_maps

        for subj in ["physics", "history"]:
            c = len(rank_maps.get(subj, {}))
            if c > 0:
                top = sorted(rank_maps[subj].items(), key=lambda x: -x[0])[:3]
                print(f"    {subj}: {c} 个分数点, 最高分={top[0][0]} rank={top[0][1]}")

    return all_rank_maps


if __name__ == "__main__":
    rank_maps = parse_all_ranks()
    out_path = f"{RAW_DIR}/_rank_maps_ocr.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rank_maps, f, ensure_ascii=False, indent=1)
    print(f"\n结果保存至: {out_path}")
