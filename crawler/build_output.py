"""
构建最终输出的 JSON 数据文件

以校名为唯一标识，自动去重并生成稳定 ID。
优先使用 OCR 真实位次，不足时用分数估算。
"""

import json
import hashlib
import math
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


def estimate_rank(score, year, subject):
    """分数估算位次（无 OCR 数据时的回退）"""
    if score is None:
        return None
    if subject == "physics":
        max_s, min_s, max_r = 700, 430, 300000
    else:
        max_s, min_s, max_r = 680, 430, 200000

    adj = {2021: 1.00, 2022: 1.05, 2023: 1.10, 2024: 1.15, 2025: 1.20}.get(year, 1.0)
    if score >= max_s:
        return 1 + int((max_s - score) * 5)
    if score <= min_s:
        return max_r

    ln_mr = math.log(max_r)
    ln_top = math.log(5)
    B = (ln_mr - ln_top) / (max_s - min_s)
    ln_A = ln_top + B * max_s
    return max(1, min(int(math.exp(ln_A - B * score) * adj), int(max_r * adj)))


def interpolate_rank(score, rank_map):
    """在 OCR 位次表中查找最接近的分数位次。
    返回 (rank, is_real): is_real=False 表示超出 OCR 范围需估算。"""
    if not rank_map:
        return None, False
    int_map = {int(k): v for k, v in rank_map.items()}
    if score in int_map:
        return int_map[score], True

    scores = sorted(int_map.keys(), reverse=True)
    hi, lo = scores[0], scores[-1]  # hi=最高分(最低rank), lo=最低分(最高rank)

    if score > hi:
        # 超出 OCR 高分端 → 线性外推（rank 递减）
        # 取最高两个点做外推
        if len(scores) >= 2:
            s1, s2 = scores[0], scores[1]
            r1, r2 = int_map[s1], int_map[s2]
            slope = (r1 - r2) / (s1 - s2)  # 每分对应多少 rank
            est = max(1, int(r1 + slope * (score - s1)))
            return est, False
        return max(1, int(int_map[hi] * 0.5)), False

    if score < lo:
        # 低于 OCR 低分端 → 返回最低分的 rank（保守）
        return int_map[lo], True

    # 在范围内 → 线性插值
    for i, s in enumerate(scores):
        if score >= s:
            if i > 0:
                s_above = scores[i - 1]
                r_above = int_map[s_above]
                r_below = int_map[s]
                ratio = (score - s) / (s_above - s) if s_above != s else 0
                return int(r_below + (r_above - r_below) * ratio), True
            return int_map[s], True

    return int_map[scores[-1]], False


def build_school_index(score_records, gaokao_schools):
    """构建学校索引（以校名为键）"""
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

    # 用阳光高考网数据补充
    if gaokao_schools:
        glist = gaokao_schools if isinstance(gaokao_schools, list) else list(gaokao_schools.values())
        gmap = {s.get("name", ""): s for s in glist if s.get("name")}
        for name, info in schools_by_name.items():
            if name in gmap:
                gs = gmap[name]
                info["province"] = gs.get("province", "")
                info["level"] = gs.get("features", "") or gs.get("level", "")
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

    # 统计非空率
    total = len(schools_list)
    for field in ["province", "level", "type"]:
        filled = sum(1 for s in schools_list if s.get(field))
        print(f"  {field}: {filled}/{total} ({filled*100//total}%)")

    print(f"  ✓ {total} 所学校 → {out}")
    return name_to_id


def build_score_jsons(score_records, ocr_ranks, name_to_id):
    """构建分片 JSON"""
    print("\n--- 构建分数线分片 JSON ---")

    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        groups.setdefault(key, []).append(r)

    # 统计 OCR 覆盖情况
    ocr_stats = {}
    for year in YEARS:
        for subj in SUBJECTS:
            key = f"{year}_{subj}"
            rm = ocr_ranks.get(str(year), {}).get(subj, {})
            ocr_stats[key] = len(rm)

    output_files = []
    for (year, subject), records in groups.items():
        rank_map = ocr_ranks.get(str(year), {}).get(subject, {})
        ocr_count = len(rank_map)

        output_records = []
        real_rank_count = 0

        for r in records:
            school_name = r.get("schoolName", "").strip()
            school_id = name_to_id.get(school_name, stable_id(school_name))

            # 优先用 OCR 真实位次
            rank_result = interpolate_rank(r["minScore"], rank_map)
            if rank_result[0] is not None:
                min_rank, is_real = rank_result
            else:
                min_rank, is_real = None, False
            is_estimated = not is_real
            if is_estimated:
                min_rank = estimate_rank(r["minScore"], year, subject)
            else:
                real_rank_count += 1

            output_records.append({
                "schoolId": school_id,
                "major": r.get("majorName", ""),
                "majorCode": r.get("majorCode", ""),
                "minScore": r["minScore"],
                "maxScore": None,
                "avgScore": None,
                "minRank": min_rank,
                "minRankEstimated": is_estimated,
                "planNum": None,
                "remark": r.get("remark", ""),
            })

        filename = f"{subject}-{year}.json"
        out = os.path.join(OUTPUT_DIR, filename)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"year": year, "subject": subject, "records": output_records}, f, ensure_ascii=False, indent=2)

        pct = real_rank_count * 100 // len(output_records) if output_records else 0
        print(f"  ✓ {filename}: {len(output_records)} 条 | 真实位次 {real_rank_count} ({pct}%) | OCR 分数点 {ocr_count}")
        output_files.append(filename)

    return output_files


def main():
    print("=" * 60)
    print("🏗️  构建最终输出数据（含 OCR 真实位次）")
    print("=" * 60)

    score_records = load_json(f"{RAW_DIR}/_parsed_scores.json") or []
    ocr_ranks = load_json(f"{RAW_DIR}/_rank_maps_ocr.json") or {}
    gaokao_schools = load_json(f"{RAW_DIR}/_gaokao_schools.json")

    print(f"  分数线记录: {len(score_records)}")
    print(f"  OCR 位次: {sum(len(v) for y in ocr_ranks.values() for v in y.values())} 个分数点")
    print(f"  阳光高考网: {'✓' if gaokao_schools else '❌'}")

    name_to_id = build_school_index(score_records, gaokao_schools)
    build_score_jsons(score_records, ocr_ranks, name_to_id)

    print(f"\n{'=' * 60}")
    print(f"✅ 完成！输出到 {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
