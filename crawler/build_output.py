"""
构建最终输出的 JSON 数据文件

以校名为唯一标识（省编代号跨年不稳定），自动去重并生成稳定 ID。
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
    """基于校名生成稳定的 6 位数字 ID"""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    # 取前 6 位十六进制 → 转十进制取模保证 6 位
    return str(int(h[:6], 16) % 900000 + 100000)


def estimate_rank(score, year, subject):
    """
    基于分数的位次估算（无一分一段表时的回退方案）
    使用指数衰减模型拟合分数-位次关系。
    """
    if score is None:
        return None

    if subject == "physics":
        max_score, min_score = 700, 430
        max_rank = 300000
    else:
        max_score, min_score = 680, 430
        max_rank = 200000

    year_adjustments = {2021: 1.00, 2022: 1.05, 2023: 1.10, 2024: 1.15, 2025: 1.20}
    adj = year_adjustments.get(year, 1.0)

    if score >= max_score:
        return 1 + int((max_score - score) * 5)
    if score <= min_score:
        return max_rank

    ln_max_rank = math.log(max_rank)
    ln_top = math.log(5)
    B = (ln_max_rank - ln_top) / (max_score - min_score)
    ln_A = ln_top + B * max_score
    rank = int(math.exp(ln_A - B * score) * adj)
    return max(1, min(rank, int(max_rank * adj)))


def build_school_index(score_records, gaokao_schools):
    """
    构建以校名为键的学校索引。
    返回: {school_name: school_info}, name_to_id: {school_name: stable_id}
    """
    print("\n--- 构建学校索引 ---")

    schools_by_name = OrderedDict()

    # 从投档数据提取所有学校
    for r in score_records:
        name = r.get("schoolName", "").strip()
        if not name:
            continue
        if name not in schools_by_name:
            schools_by_name[name] = {
                "name": name,
                "province": "",
                "city": r.get("city", ""),
                "level": "",
                "type": "",
                "nature": r.get("nature", "公办"),
                "batch": "本科",
            }

    # 如果阳光高考网有数据，尝试用校名匹配补充 provinces/level/type
    if gaokao_schools:
        gaokao_list = (gaokao_schools if isinstance(gaokao_schools, list)
                       else list(gaokao_schools.values()))
        gaokao_by_name = {}
        for sch in gaokao_list:
            n = sch.get("name", "")
            if n:
                gaokao_by_name[n] = sch

        for name, info in schools_by_name.items():
            if name in gaokao_by_name:
                gs = gaokao_by_name[name]
                info["province"] = gs.get("province", info["province"])
                info["level"] = gs.get("features", "") or gs.get("level", info["level"])
                info["type"] = gs.get("type", info["type"])
            # 模糊匹配
            else:
                for gn, gs in gaokao_by_name.items():
                    if name in gn or gn in name:
                        info["province"] = gs.get("province", info["province"])
                        info["level"] = gs.get("features", "") or gs.get("level", info["level"])
                        info["type"] = gs.get("type", info["type"])
                        break

    # 分配稳定 ID
    name_to_id = {}
    schools_list = []
    for name, info in schools_by_name.items():
        sid = stable_id(name)
        name_to_id[name] = sid
        schools_list.append({
            "id": sid,
            "name": info["name"],
            "province": info["province"],
            "city": info["city"],
            "level": info["level"],
            "type": info["type"],
            "nature": info["nature"],
            "batch": info["batch"],
        })

    # 输出 schools.json
    output_path = os.path.join(OUTPUT_DIR, "schools.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"schools": schools_list}, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {len(schools_list)} 所学校 → {output_path}")
    return name_to_id


def build_score_jsons(score_records, rank_maps, name_to_id):
    """构建按科类×年份分片的分数线 JSON"""
    print("\n--- 构建分数线分片 JSON ---")

    # 按 (year, subject) 分组
    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    # 检查是否有有效的 rank_maps
    has_real_ranks = False
    if rank_maps:
        for year_data in rank_maps.values():
            for subj_data in year_data.values():
                if subj_data and len(subj_data) > 0:
                    has_real_ranks = True
                    break

    if not has_real_ranks:
        print("  ⚠️ 无精确位次数据，使用分数估算位次")

    output_files = []
    for (year, subject), records in groups.items():
        output_records = []
        for r in records:
            school_name = r.get("schoolName", "").strip()
            school_id = name_to_id.get(school_name, stable_id(school_name))

            # 计算位次
            min_rank = None
            if has_real_ranks and rank_maps:
                year_rank_map = rank_maps.get(str(year), rank_maps.get(year, {}))
                if year_rank_map and subject in year_rank_map:
                    from parse_rankmap import build_rank_lookup
                    min_rank = build_rank_lookup(
                        year_rank_map, year, subject, r["minScore"]
                    )

            if min_rank is None:
                min_rank = estimate_rank(r["minScore"], year, subject)

            output_records.append({
                "schoolId": school_id,
                "major": r.get("majorName", ""),
                "majorCode": r.get("majorCode", ""),
                "minScore": r["minScore"],
                "maxScore": None,
                "avgScore": None,
                "minRank": min_rank,
                "minRankEstimated": not has_real_ranks,
                "planNum": None,
                "remark": r.get("remark", ""),
            })

        filename = f"{subject}-{year}.json"
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "year": year,
                "subject": subject,
                "records": output_records,
            }, f, ensure_ascii=False, indent=2)

        with_rank = sum(1 for r in output_records if r["minRank"] is not None)
        print(f"  ✓ {filename}: {len(output_records)} 条"
              f"（{with_rank} 条有位次{'，估算值' if not has_real_ranks else ''}）")
        output_files.append(filename)

    return output_files


def main():
    print("=" * 60)
    print("🏗️  构建最终输出数据")
    print("=" * 60)

    scores_path = f"{RAW_DIR}/_parsed_scores.json"
    rank_path = f"{RAW_DIR}/_rank_maps.json"
    school_path = f"{RAW_DIR}/_gaokao_schools.json"

    score_records = load_json(scores_path) or []
    rank_maps = load_json(rank_path) or {}
    gaokao_schools = load_json(school_path)

    print(f"  加载: {len(score_records)} 条分数线")
    print(f"  加载: {len(rank_maps)} 年位次映射")
    print(f"  加载: {'✓' if gaokao_schools else '❌（跳过）'} 阳光高考网学校数据")

    # 构建学校索引（以校名为准）
    name_to_id = build_school_index(score_records, gaokao_schools)

    # 构建分片 JSON
    output_files = build_score_jsons(score_records, rank_maps, name_to_id)

    print(f"\n{'=' * 60}")
    print(f"✅ 完成！输出 {len(output_files) + 1} 个文件到 {OUTPUT_DIR}/")
    print(f"{'=' * 60}")
    # Check if ranks are estimated
    real_ranks = any(
        any(len(m) > 0 for m in year_data.values())
        for year_data in rank_maps.values()
    ) if rank_maps else False
    if not real_ranks:
        print(f"\n💡 minRank 使用分数估算值。运行 download.py → parse_rankmap.py 后重新 build 可获精确位次。")


if __name__ == "__main__":
    main()
