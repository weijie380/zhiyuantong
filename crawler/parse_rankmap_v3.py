"""
一分一段表 OCR v3 — 按分数模式分段，不依赖页眉

PDF 结构：前半=物理类，后半=历史类
检测策略：所有页提取 score→cumulative，然后按分数模式切分两段。
物理类最高分通常 > 690，历史类最高分通常 < 680。
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

NUM_FIX = {'S': '5', 'O': '0', 'o': '0', 'l': '1', 'I': '1', 'Z': '2', 'B': '8', 'G': '6'}


def fix_num(t):
    for k, v in NUM_FIX.items():
        t = t.replace(k, v)
    return t


def ocr_page_extract_scores(img):
    """从单页图片提取所有 (score, cumulative) 对，不判断科类"""
    data = pytesseract.image_to_data(
        img, lang='chi_sim+eng', config='--psm 11',
        output_type=pytesseract.Output.DICT
    )

    words = []
    for i in range(len(data['text'])):
        t = data['text'][i].strip()
        conf = int(data['conf'][i])
        if t and conf > 15:
            words.append({'text': fix_num(t), 'x': data['left'][i], 'y': data['top'][i]})
    words.sort(key=lambda w: (w['y'], w['x']))

    # 按 y 分行
    rows, cur, cy = [], [], None
    for w in words:
        if cy is None or abs(w['y'] - cy) > 15:
            if cur: rows.append(cur)
            cur = [w]; cy = w['y']
        else:
            cur.append(w)
    if cur: rows.append(cur)

    results = []
    for row in rows:
        texts = [w['text'] for w in sorted(row, key=lambda w: w['x'])]
        nums, above = [], False
        for t in texts:
            if '及' in t or '以' in t or '上' in t:
                above = True
            cl = ''.join(c for c in t if c.isdigit())
            if cl: nums.append(int(cl))
        if len(nums) < 2 or above:
            continue
        score = nums[0]
        if score < 300 or score > 750:
            continue
        cumulative = nums[2] if len(nums) >= 3 else nums[1]
        if cumulative > 0:
            results.append((score, cumulative))

    return results


def split_physics_history(all_page_results):
    """
    按分数模式切分物理/历史。

    策略：所有页的 (score, cumulative) 数据合并后，
    按分数降序排列。物理类最高分通常 > 690，历史类 < 680。
    在分数跳变处（从低分突然跳到高分）切分。
    """
    # 合并所有页的数据
    all_scores = {}
    for page_results in all_page_results:
        for score, cumulative in page_results:
            # 同一分取最小的 cumulative（最精确）
            if score not in all_scores or cumulative < all_scores[score]:
                all_scores[score] = cumulative

    if not all_scores:
        return {}, {}

    # 按分数降序排列
    sorted_scores = sorted(all_scores.items(), key=lambda x: -x[0])

    # 找切分点：分数从低到高的跳变
    # 物理类：分数从 ~700 递减到 ~350
    # 历史类：分数从 ~680 递减到 ~350
    # 切分点：当分数从 ~350 突然跳到 ~680 时

    physics = {}
    history = {}

    # 找到最大的分数跳变（>100分的跳变）
    split_score = None
    for i in range(1, len(sorted_scores)):
        prev_score = sorted_scores[i-1][0]
        curr_score = sorted_scores[i][0]
        if prev_score - curr_score > 100:  # 从高分跳到低分（跳变）
            # 这里 prev_score 是较高分，curr_score 是较低分
            # 跳变发生在从物理低分到历史高分
            split_score = curr_score
            break

    if split_score is None:
        # 没有明显跳变，尝试按最高分判断
        max_score = sorted_scores[0][0]
        if max_score > 690:
            # 只有物理类数据
            physics = all_scores
        else:
            history = all_scores
    else:
        # 按切分点分配
        for score, cumulative in sorted_scores:
            if score >= split_score:
                history[score] = cumulative
            else:
                physics[score] = cumulative

    return physics, history


def parse_rank_pdf(filepath, year):
    """解析一分一段表 PDF"""
    print(f"  OCR: {filepath}")
    pdf = pdfplumber.open(filepath)
    total = len(pdf.pages)
    pdf.close()
    print(f"    共 {total} 页")

    all_page_results = []

    for page_num in range(total):
        print(f"    第 {page_num + 1}/{total} 页...", end=" ")

        with pdfplumber.open(filepath) as pdf2:
            page = pdf2.pages[page_num]
            im = page.to_image(resolution=150)
            tmp = f"/tmp/_ocr3_{os.getpid()}_{page_num}.png"
            im.save(tmp)

        img = Image.open(tmp).convert('RGB')
        results = ocr_page_extract_scores(img)
        all_page_results.append(results)

        if results:
            scores = [s for s, c in results]
            print(f"{len(results)} 条 (scores: {min(scores)}-{max(scores)})")
        else:
            print("无数据")

        try: os.remove(tmp)
        except: pass

    # 切分物理/历史
    physics, history = split_physics_history(all_page_results)
    print(f"    物理类: {len(physics)} 个分数点, 历史类: {len(history)} 个分数点")

    if physics:
        top = sorted(physics.items(), key=lambda x: -x[0])[:3]
        print(f"    物理 top: {top}")
    if history:
        top = sorted(history.items(), key=lambda x: -x[0])[:3]
        print(f"    历史 top: {top}")

    return {"physics": physics, "history": history}


def parse_all_ranks():
    """解析所有年份"""
    print("\n" + "=" * 60)
    print("📊 OCR 解析一分一段表 v3（自动分段）")
    print("=" * 60)

    all_rank_maps = {}
    for year in YEARS:
        print(f"\n--- {year} 年 ---")
        filepath = f"{RAW_DIR}/{year}_rank.pdf"
        if not Path(filepath).exists():
            print(f"  ⚠️ 文件不存在")
            all_rank_maps[str(year)] = {"physics": {}, "history": {}}
            continue
        rank_maps = parse_rank_pdf(filepath, year)
        all_rank_maps[str(year)] = rank_maps

    return all_rank_maps


if __name__ == "__main__":
    rank_maps = parse_all_ranks()
    out_path = f"{RAW_DIR}/_rank_maps_v3.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rank_maps, f, ensure_ascii=False, indent=1)
    print(f"\n结果保存至: {out_path}")
