"""
爬取阳光高考网院校库 → 学校元数据

数据来源: gaokao.chsi.com.cn/sch/ 院校库
通过 AJAX 接口获取全国高校列表，包括:
  - 院校名称、所在地、主管部门、办学层次、院校特性

产出: schools.json 格式的学校列表
"""

import json
import re
import time
import requests
from bs4 import BeautifulSoup
from config import HEADERS, DOWNLOAD_DELAY, RAW_DIR, OUTPUT_DIR
from pathlib import Path


def fetch_school_list_page(province_code="", page=1):
    """获取一页学校列表

    阳光高考网院校搜索使用 AJAX 分页。
    尝试多种方式获取数据。
    """
    url = "https://gaokao.chsi.com.cn/sch/search.do"

    params = {
        "ssdm": province_code,  # 省份代码，空=全国
        "yxls": "",  # 学历层次
        "bxlx": "",  # 办学类型
        "zypc": "",  # 院校特性
        "page": page,
    }

    # 尝试 POST（Vue.js 常用）
    try:
        resp = requests.post(url, data=params, headers={
            **HEADERS,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }, timeout=30)
        if resp.status_code == 200 and len(resp.text) > 100:
            return resp.text
    except Exception:
        pass

    # 回退 GET
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 200 and len(resp.text) > 100:
            return resp.text
    except Exception as e:
        print(f"    ❌ 请求失败: {e}")

    return None


def parse_school_list(html):
    """从 HTML 中解析学校列表"""
    soup = BeautifulSoup(html, "html.parser")
    schools = []

    # 尝试多种可能的 HTML 结构
    # 结构 1: 表格行 <tr>
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue

        try:
            name_tag = cells[0].find("a") or cells[0]
            name = name_tag.get_text(strip=True)

            # 提取链接中的学校 ID
            href = name_tag.get("href", "") if name_tag.name == "a" else ""
            sch_id = ""
            id_match = re.search(r'schId[=/](\d+)', href)
            if id_match:
                sch_id = id_match.group(1)

            province = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            authority = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            level = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            features = cells[4].get_text(strip=True) if len(cells) > 4 else ""

            if name and (sch_id or province):
                schools.append({
                    "id": sch_id,
                    "name": name,
                    "province": province,
                    "authority": authority,
                    "level": level,
                    "features": features,
                })
        except Exception:
            continue

    # 结构 2: div 列表
    if not schools:
        for item in soup.find_all("div", class_=re.compile(r"sch|school|item|list")):
            name_tag = item.find("a")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            href = name_tag.get("href", "")
            sch_id = ""
            id_match = re.search(r'schId[=/](\d+)', href)
            if id_match:
                sch_id = id_match.group(1)

            if name and sch_id:
                schools.append({
                    "id": sch_id,
                    "name": name,
                    "province": "",
                    "authority": "",
                    "level": "",
                    "features": "",
                })

    return schools


def crawl_all_schools(max_pages=200):
    """爬取全国所有高校"""
    print("\n" + "=" * 60)
    print("🏫 爬取阳光高考网院校库")
    print("=" * 60)

    all_schools = {}
    seen = set()

    for page in range(1, max_pages + 1):
        print(f"  第 {page} 页...", end=" ")

        html = fetch_school_list_page(page=page)
        if not html:
            print("无数据（可能已到末页）")
            # 可能是最后一页，也可能被限制
            if page > 5:
                break  # 连续失败就停止
            continue

        schools = parse_school_list(html)
        if not schools:
            print("解析为空")
            # 检查是否到了末页（可能返回空页面）
            if "没有找到" in html or "无数据" in html:
                break
            continue

        new_count = 0
        for sch in schools:
            key = sch["id"] or sch["name"]
            if key not in seen:
                seen.add(key)
                all_schools[sch["id"]] = sch
                new_count += 1

        print(f"找到 {len(schools)} 所，新增 {new_count} 所（累计 {len(all_schools)}）")

        if new_count == 0:
            break  # 没有新学校了

        time.sleep(DOWNLOAD_DELAY)

    print(f"\n  📊 共爬取 {len(all_schools)} 所高校")
    return all_schools


def build_school_id_mapping(score_records, gaokao_schools):
    """建立省编代号 → 教育部标准代码的映射

    策略：
    1. 名称精确匹配
    2. 名称模糊匹配（去掉括号内容）
    3. 手工规则
    """
    print("\n" + "=" * 60)
    print("🔗 建立学校代码映射")
    print("=" * 60)

    # 从投档数据中提取所有学校
    provincial_codes = {}  # {provincial_code: school_name}
    for r in score_records:
        code = r["schoolCode"]
        name = r["schoolName"]
        if code and code not in provincial_codes:
            provincial_codes[code] = name

    # 建立名称→国标代码索引
    name_to_std = {}  # {name: std_id}
    for std_id, sch in gaokao_schools.items():
        name = sch.get("name", "")
        if name:
            name_to_std[name] = std_id

    # 映射
    mapping = {}  # {provincial_code: std_id}
    unmatched = []

    for prov_code, prov_name in provincial_codes.items():
        # 精确匹配
        if prov_name in name_to_std:
            mapping[prov_code] = name_to_std[prov_name]
            continue

        # 模糊匹配：去掉括号
        clean_name = prov_name.replace("（", "(").replace("）", ")")
        # 有些名称有多余后缀
        for std_name, std_id in name_to_std.items():
            if std_name == prov_name or prov_name == std_name:
                mapping[prov_code] = std_id
                break
            # 包含匹配
            if len(prov_name) >= 4 and (prov_name in std_name or std_name in prov_name):
                mapping[prov_code] = std_id
                break
        else:
            unmatched.append((prov_code, prov_name))

    print(f"  ✓ 映射成功: {len(mapping)} 所")
    print(f"  ❌ 未匹配: {len(unmatched)} 所")

    if unmatched:
        print("  未匹配学校:")
        for code, name in unmatched[:20]:
            print(f"    {code}: {name}")

    # 保存映射
    map_path = f"{RAW_DIR}/_code_mapping.json"
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump({"mapping": mapping, "unmatched": unmatched},
                  f, ensure_ascii=False, indent=1)
    print(f"  映射保存至: {map_path}")

    return mapping


if __name__ == "__main__":
    schools = crawl_all_schools()
    out_path = f"{RAW_DIR}/_gaokao_schools.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(list(schools.values()), f, ensure_ascii=False, indent=1)
    print(f"\n学校数据保存至: {out_path}")
