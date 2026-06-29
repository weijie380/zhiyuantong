"""
解析一分一段表 PDF → 分数→位次 映射

PDF 通常包含物理类和历史类两个表格，格式如：
  分数 | 人数 | 累计人数

输出: {year: {subject: {score: rank}}}
"""

import re
from pathlib import Path
import pdfplumber
from config import RAW_DIR, YEARS, SUBJECTS


def parse_rank_pdf(filepath, year):
    """解析一分一段表 PDF，返回 {subject: {score: rank}}"""
    print(f"  解析: {filepath}")

    rank_maps = {"physics": {}, "history": {}}

    try:
        with pdfplumber.open(filepath) as pdf:
            all_text = ""
            all_tables = []

            for page_idx, page in enumerate(pdf.pages):
                # 提取文本
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    all_tables.append(table)

            # 策略 1: 从提取的表格中解析
            if all_tables:
                rank_maps = _parse_from_tables(all_tables, year)
                if _validate_rank_maps(rank_maps):
                    return rank_maps

            # 策略 2: 从文本中按行解析
            print(f"    表格解析不完整，尝试文本解析...")
            rank_maps = _parse_from_text(all_text, year)
            if _validate_rank_maps(rank_maps):
                return rank_maps

    except Exception as e:
        print(f"    ❌ PDF 解析失败: {e}")
        # 返回空映射
        return {"physics": {}, "history": {}}

    return rank_maps


def _parse_from_tables(tables, year):
    """从结构化表格中提取分数→位次映射"""
    rank_maps = {"physics": {}, "history": {}}
    current_subject = None

    for table in tables:
        for row in table:
            if not row or all(c is None for c in row):
                continue

            row_text = " ".join([str(c) if c else "" for c in row])

            # 检测表头，判断当前是物理还是历史
            if "物理" in row_text or "物理科目" in row_text:
                current_subject = "physics"
                continue
            if "历史" in row_text or "历史科目" in row_text:
                current_subject = "history"
                continue

            if current_subject is None:
                continue

            # 跳过表头行
            if "分数" in row_text or "累计" in row_text or "人数" in row_text:
                continue

            # 解析数据行：分数, 人数, 累计人数
            nums = _extract_numbers(row)
            if len(nums) >= 2:
                score = int(nums[0])
                # 累计人数 = rank
                # 通常最后一列是累计人数
                cumulative = int(nums[-1])
                if 100 <= score <= 750 and cumulative > 0:
                    rank_maps[current_subject][score] = cumulative

    return rank_maps


def _parse_from_text(text, year):
    """从纯文本中解析分数→位次映射"""
    rank_maps = {"physics": {}, "history": {}}
    current_subject = None

    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测科类
        if "物理科目组合" in line or ("物理" in line and ("成绩统计" in line or "一分" in line)):
            current_subject = "physics"
            continue
        if "历史科目组合" in line or ("历史" in line and ("成绩统计" in line or "一分" in line)):
            current_subject = "history"
            continue

        if current_subject is None:
            continue

        # 解析数据行：分数 人数 累计
        # 格式可能是: "700 5 5" 或 "700  5  5" 或 "700 5 累计5"
        nums = _extract_numbers(line.split())
        if len(nums) >= 2:
            score = int(nums[0])
            cumulative = int(nums[-1])  # 累计人数 = rank
            if 100 <= score <= 750 and cumulative > 0:
                rank_maps[current_subject][score] = cumulative

    return rank_maps


def _extract_numbers(items):
    """从列表项中提取所有数字"""
    nums = []
    for item in items:
        if item is None:
            continue
        item_str = str(item).strip().replace(",", "").replace("，", "")
        # 尝试直接转换
        try:
            nums.append(float(item_str))
        except ValueError:
            # 提取其中的数字
            found = re.findall(r'\d+', item_str)
            for f in found:
                try:
                    nums.append(float(f))
                except ValueError:
                    pass
    return nums


def _validate_rank_maps(rank_maps):
    """验证映射是否合理"""
    for subject in SUBJECTS:
        if len(rank_maps.get(subject, {})) > 10:
            return True
    return False


def build_rank_lookup(rank_maps, year, subject, score):
    """根据分数查找对应位次（插值）

    rank_maps: {score: cumulative_rank} 如 {700: 5, 699: 12, ...}
    返回: 该分数的近似位次
    """
    mapping = rank_maps.get(subject, {})
    if not mapping:
        return None

    if score in mapping:
        return mapping[score]

    # 找到最近的分数
    scores = sorted(mapping.keys(), reverse=True)  # 从高到低
    for s in scores:
        if score > s:
            return mapping[s]  # 返回略低分数的位次（保守估计）

    # 分数比所有记录都低
    if scores:
        return mapping[scores[-1]]

    return None


def parse_all_ranks():
    """解析所有年份的 PDF"""
    print("\n" + "=" * 60)
    print("📊 解析一分一段表 PDF")
    print("=" * 60)

    all_rank_maps = {}

    for year in YEARS:
        print(f"\n--- {year} 年 ---")
        filepath = f"{RAW_DIR}/{year}_rank.pdf"
        if not Path(filepath).exists():
            print(f"  ⚠️ 文件不存在: {filepath}")
            all_rank_maps[year] = {"physics": {}, "history": {}}
            continue

        rank_maps = parse_rank_pdf(filepath, year)
        all_rank_maps[year] = rank_maps

        for subject in SUBJECTS:
            count = len(rank_maps.get(subject, {}))
            print(f"    {subject}: {count} 个分数点")

    return all_rank_maps


if __name__ == "__main__":
    rank_maps = parse_all_ranks()
    import json
    mid_path = f"{RAW_DIR}/_rank_maps.json"
    # 只保存可序列化的部分
    with open(mid_path, "w", encoding="utf-8") as f:
        json.dump(rank_maps, f, ensure_ascii=False, indent=1)
    print(f"\n中间结果保存至: {mid_path}")
