"""
解析投档统计 Excel → 结构化数据

Excel 列结构（Row 3-5 是合并表头，Row 6 起是数据）:
  院校代号 | 院校名称 | 专业代号 | 专业名称 | 投档最低分 | 排序项×7 | 备注

返回格式:
  records: [{school_code, school_name, major_code, major_name,
             min_score, remark, year, subject}]
"""

import re
import openpyxl
from pathlib import Path
from config import RAW_DIR, YEARS, SUBJECTS


def parse_school_info(raw_name):
    """从院校名称中提取：名称、城市、性质
    例: '安徽财经大学(蚌埠市)[公办]' → ('安徽财经大学', '蚌埠市', '公办')
        '北京大学[公办]' → ('北京大学', '', '公办')
    """
    name = raw_name.strip()

    # 提取性质 [公办]/[民办]/[中外合作]
    nature = ""
    nature_match = re.search(r'\[(公办|民办|中外合作.*?|内地与港澳台.*?)\]', name)
    if nature_match:
        nature = nature_match.group(1)
        name = name.replace(nature_match.group(0), "")

    # 提取城市 (xxx市)
    city = ""
    city_match = re.search(r'\((.+?市)\)', name)
    if city_match:
        city = city_match.group(1)
        name = name.replace(city_match.group(0), "")

    return name.strip(), city, nature


def parse_score_excel(filepath, year, subject):
    """解析单个投档统计 Excel 文件"""
    print(f"  解析: {filepath}")
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active

    records = []
    errors = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=6, values_only=True), start=6):
        # 跳过空行和说明行
        if not row[0] and not row[1]:
            # 检查是否是说明文字
            first_cell = str(row[0] or "").strip()
            if first_cell.startswith("说明") or first_cell.startswith("注"):
                continue
            continue

        try:
            school_code = str(row[0] or "").strip()
            school_name_raw = str(row[1] or "").strip()
            major_code_internal = str(row[2] or "").strip()
            major_name = str(row[3] or "").strip()
            min_score_str = str(row[4] or "").strip()
            remark = str(row[12] or "").strip() if len(row) > 12 else ""

            if not school_code or not school_name_raw or not major_name:
                continue

            # 跳过表头行（如果 min_row 设置不对）
            if school_code in ("院校代号", "院校", "代号"):
                continue

            min_score = None
            try:
                min_score = int(float(min_score_str))
            except (ValueError, TypeError):
                pass

            if min_score is None:
                continue

            school_name, city, nature = parse_school_info(school_name_raw)

            records.append({
                "schoolCode": school_code,
                "schoolName": school_name,
                "schoolNameRaw": school_name_raw,
                "city": city,
                "nature": nature,
                "majorCode": major_code_internal,
                "majorName": major_name,
                "minScore": min_score,
                "remark": remark,
                "year": year,
                "subject": subject,
            })
        except Exception as e:
            errors.append(f"Row {row_idx}: {e}")

    wb.close()
    print(f"    ✓ 解析 {len(records)} 条记录" + (f", {len(errors)} 条错误" if errors else ""))
    return records


def parse_all_scores():
    """解析所有年份×科类的 Excel"""
    print("\n" + "=" * 60)
    print("📊 解析投档统计 Excel")
    print("=" * 60)

    all_records = []

    for year in YEARS:
        for subject in SUBJECTS:
            filepath = f"{RAW_DIR}/{year}_{subject}.xlsx"
            if not Path(filepath).exists():
                # 尝试 xls 扩展名
                filepath_xls = f"{RAW_DIR}/{year}_{subject}.xls"
                if Path(filepath_xls).exists():
                    filepath = filepath_xls
                else:
                    print(f"  ⚠️ 文件不存在: {filepath}")
                    continue

            records = parse_score_excel(filepath, year, subject)
            all_records.extend(records)

    print(f"\n  📊 总计: {len(all_records)} 条记录")

    # 统计
    by_year = {}
    by_subject = {}
    for r in all_records:
        by_year[r["year"]] = by_year.get(r["year"], 0) + 1
        by_subject[r["subject"]] = by_subject.get(r["subject"], 0) + 1

    for y in sorted(by_year):
        print(f"    {y}年: {by_year[y]} 条")
    for s in sorted(by_subject):
        print(f"    {s}: {by_subject[s]} 条")

    return all_records


if __name__ == "__main__":
    records = parse_all_scores()
    # 保存中间结果
    import json
    mid_path = f"{RAW_DIR}/_parsed_scores.json"
    with open(mid_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    print(f"\n中间结果保存至: {mid_path}")
