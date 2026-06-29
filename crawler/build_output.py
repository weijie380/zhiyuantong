"""
构建最终输出 JSON — 用官方锚点模型将 minScore 换算为真实省排位次
"""

import json
import hashlib
import os
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


def build_school_index(score_records, gaokao_schools):
    print("\n--- 构建学校索引 ---")
    schools_by_name = {}
    for r in score_records:
        name = r.get("schoolName", "").strip()
        if not name or name in schools_by_name:
            continue
        schools_by_name[name] = {
            "name": name, "city": r.get("city", ""), "nature": r.get("nature", "公办"),
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
            "id": sid, "name": info["name"],
            "province": info.get("province", ""), "city": info.get("city", ""),
            "level": info.get("level", ""), "type": info.get("type", ""),
            "nature": info.get("nature", "公办"), "batch": "本科",
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


def main():
    print("=" * 60)
    print("🏗️  构建最终输出（官方锚点位次模型）")
    print("=" * 60)

    score_records = load_json(f"{RAW_DIR}/_parsed_scores.json") or []
    gaokao_schools = load_json(f"{RAW_DIR}/_gaokao_schools.json")
    rank_model = load_json(f"{RAW_DIR}/_score_rank_model.json")

    print(f"  分数线记录: {len(score_records)}")
    print(f"  位次模型: {len(rank_model)} 年")

    name_to_id = build_school_index(score_records, gaokao_schools)

    # 构建分片 JSON
    print("\n--- 构建分数线分片 JSON ---")
    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        groups.setdefault(key, []).append(r)

    for (year, subject), records in groups.items():
        year_str = str(year)
        model = rank_model.get(year_str, {}).get(subject, {})

        output_records = []
        for r in records:
            school_name = r.get("schoolName", "").strip()
            school_id = name_to_id.get(school_name, stable_id(school_name))
            score = r["minScore"]
            min_rank = model.get(str(score))

            output_records.append({
                "schoolId": school_id,
                "major": r.get("majorName", ""),
                "majorCode": r.get("majorCode", ""),
                "minScore": score,
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

        has_rank = sum(1 for r in output_records if r["minRank"] is not None)
        min_r = min((r["minRank"] for r in output_records if r["minRank"]), default=0)
        max_r = max((r["minRank"] for r in output_records if r["minRank"]), default=0)
        print(f"  ✓ {filename}: {len(output_records)} 条 | 有位次 {has_rank} | 位次范围 {min_r}-{max_r}")

    print(f"\n{'='*60}")
    print(f"✅ 完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
