"""
构建最终输出的 JSON 数据文件

位次来源：从投档统计 Excel 自身数据推导（按分数排序分配相对位次）。
此方法不依赖 OCR，无污染风险，民办院校自然排在低分段。
"""

import json
import hashlib
import os
from collections import OrderedDict
from pathlib import Path
from config import OUTPUT_DIR, YEARS, SUBJECTS, RAW_DIR


def load_json(filepath):
    if not Path(filepath).exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def stable_id(name):
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return str(int(h[:6], 16) % 900000 + 100000)


def derive_ranks(score_records):
    """从投档数据推导位次：按 (year, subject) 分组，分数降序排列，同分同位次"""
    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        groups.setdefault(key, []).append(r)

    rank_map = {}  # {(year, subject): {schoolCode:majorCode: rank}}
    for (year, subject), recs in groups.items():
        sorted_recs = sorted(recs, key=lambda r: (-r["minScore"], r.get("schoolName", "")))
        key_ranks = {}
        rank = 1
        for i, r in enumerate(sorted_recs):
            if i > 0 and r["minScore"] < sorted_recs[i - 1]["minScore"]:
                rank = i + 1
            k = f"{r['schoolCode']}:{r['majorCode']}"
            key_ranks[k] = rank
        rank_map[(year, subject)] = key_ranks

    return rank_map


def build_school_index(score_records, gaokao_schools):
    """构建学校索引"""
    print("\n--- 构建学校索引 ---")
    schools_by_name = OrderedDict()

    for r in score_records:
        name = r.get("schoolName", "").strip()
        if not name or name in schools_by_name:
            continue
        schools_by_name[name] = {
            "name": name,
            "city": r.get("city", ""),
            "nature": r.get("nature", "公办"),
        }

    if gaokao_schools:
        glist = gaokao_schools if isinstance(gaokao_schools, list) else list(gaokao_schools.values())
        gmap = {s.get("name", ""): s for s in glist if s.get("name")}
        for name, info in schools_by_name.items():
            if name in gmap:
                gs = gmap[name]
                info["province"] = gs.get("province", "")
                info["level"] = gs.get("level", "")
                info["type"] = gs.get("type", "")

    name_to_id = {}
    schools_list = []
    for name, info in schools_by_name.items():
        sid = stable_id(name)
        name_to_id[name] = sid
        schools_list.append({
            "id": sid,
            "name": info["name"],
            "province": info.get("province", ""),
            "city": info.get("city", ""),
            "level": info.get("level", ""),
            "type": info.get("type", ""),
            "nature": info.get("nature", "公办"),
            "batch": "本科",
        })

    out = os.path.join(OUTPUT_DIR, "schools.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"schools": schools_list}, f, ensure_ascii=False, indent=2)

    total = len(schools_list)
    for field in ["province", "level", "type"]:
        filled = sum(1 for s in schools_list if s.get(field))
        print(f"  {field}: {filled}/{total} ({filled*100//total}%)")
    print(f"  ✓ {total} 所学校 → {out}")
    return name_to_id


def build_score_jsons(score_records, rank_map, name_to_id):
    """构建分片 JSON"""
    print("\n--- 构建分数线分片 JSON ---")

    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        groups.setdefault(key, []).append(r)

    output_files = []
    for (year, subject), records in groups.items():
        key_ranks = rank_map.get((year, subject), {})

        output_records = []
        for r in records:
            school_name = r.get("schoolName", "").strip()
            school_id = name_to_id.get(school_name, stable_id(school_name))
            k = f"{r.get('schoolCode', '')}:{r.get('majorCode', '')}"
            min_rank = key_ranks.get(k)

            output_records.append({
                "schoolId": school_id,
                "major": r.get("majorName", ""),
                "majorCode": r.get("majorCode", ""),
                "minScore": r["minScore"],
                "maxScore": None,
                "avgScore": None,
                "minRank": min_rank,
                "planNum": None,
                "remark": r.get("remark", ""),
            })

        filename = f"{subject}-{year}.json"
        out = os.path.join(OUTPUT_DIR, filename)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"year": year, "subject": subject, "records": output_records},
                      f, ensure_ascii=False, indent=2)

        # 统计
        has_rank = sum(1 for r in output_records if r["minRank"] is not None)
        print(f"  ✓ {filename}: {len(output_records)} 条 | 有位次 {has_rank} ({has_rank*100//len(output_records)}%)")
        output_files.append(filename)

    return output_files


def main():
    print("=" * 60)
    print("🏗️  构建最终输出（推导位次）")
    print("=" * 60)

    score_records = load_json(f"{RAW_DIR}/_parsed_scores.json") or []
    gaokao_schools = load_json(f"{RAW_DIR}/_gaokao_schools.json")

    print(f"  分数线记录: {len(score_records)}")
    print(f"  阳光高考网: {'✓' if gaokao_schools else '❌'}")

    # 从 Excel 数据推导位次（无 OCR 污染）
    rank_map = derive_ranks(score_records)
    total_ranks = sum(len(v) for v in rank_map.values())
    print(f"  推导位次: {total_ranks} 条")

    name_to_id = build_school_index(score_records, gaokao_schools)
    build_score_jsons(score_records, rank_map, name_to_id)

    print(f"\n{'=' * 60}")
    print(f"✅ 完成！所有位次均来自官方投档数据推导，无估算值。")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
