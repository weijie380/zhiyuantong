"""
高校招生网爬虫 v2 — 暴力探测 + 多源解析

策略：
1. 暴力探测常见域名模式 (zs/zhaosheng/bkzs + pinyin + edu.cn)
2. 在探测到的页面中搜索「录取分数」「历年分数」链接
3. 解析分数表提取河北数据（含位次）
"""

import json
import re
import time
import random
import os
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
OUTPUT_PATH = os.path.join(RAW_DIR, "_university_ranks.json")
PARSED_PATH = os.path.join(RAW_DIR, "_parsed_scores.json")

AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36",
]

# 已知高校招生网 URL（按学校名称索引，持续补充）
KNOWN_URLS = {
    "北京大学": "https://bkzs.pku.edu.cn",
    "清华大学": "https://join-tsinghua.edu.cn",
    "浙江大学": "https://zsw.zju.edu.cn",
    "复旦大学": "https://ao.fudan.edu.cn",
    "上海交通大学": "https://zsb.sjtu.edu.cn",
    "南京大学": "https://bkzs.nju.edu.cn",
    "中国科学技术大学": "https://zsb.ustc.edu.cn",
    "武汉大学": "https://aoff.whu.edu.cn",
    "华中科技大学": "https://zs.hust.edu.cn",
    "中山大学": "https://admission.sysu.edu.cn",
    "哈尔滨工业大学": "https://zsb.hit.edu.cn",
    "西安交通大学": "https://zs.xjtu.edu.cn",
    "北京航空航天大学": "https://zsb.buaa.edu.cn",
    "北京理工大学": "https://zsb.bit.edu.cn",
    "天津大学": "https://zsb.tju.edu.cn",
    "南开大学": "https://zsb.nankai.edu.cn",
    "大连理工大学": "https://zs.dlut.edu.cn",
    "吉林大学": "https://zsb.jlu.edu.cn",
    "同济大学": "https://zsb.tongji.edu.cn",
    "华东师范大学": "https://www.zsb.ecnu.edu.cn",
    "东南大学": "https://zsb.seu.edu.cn",
    "厦门大学": "https://zs.xmu.edu.cn",
    "山东大学": "https://www.bkzs.sdu.edu.cn",
    "中国海洋大学": "https://www.osa.xmu.edu.cn",
    "湖南大学": "https://zsb.hnu.edu.cn",
    "中南大学": "https://zsb.csu.edu.cn",
    "华南理工大学": "https://admission.scut.edu.cn",
    "电子科技大学": "https://zsb.uestc.edu.cn",
    "四川大学": "https://zsb.scu.edu.cn",
    "重庆大学": "https://zsb.cqu.edu.cn",
    "西北工业大学": "https://zsb.nwpu.edu.cn",
    "兰州大学": "https://zsb.lzu.edu.cn",
    "东北大学": "https://zs.neu.edu.cn",
    "北京师范大学": "https://zsb.bnu.edu.cn",
    "中国人民大学": "https://zs.ruc.edu.cn",
    "中国农业大学": "https://zs.cau.edu.cn",
    "中央民族大学": "https://zsb.muc.edu.cn",
    "北京交通大学": "https://zsb.bjtu.edu.cn",
    "北京科技大学": "https://zhaosheng.ustb.edu.cn",
    "北京邮电大学": "https://zsb.bupt.edu.cn",
    "北京化工大学": "https://bkzs.buct.edu.cn",
    "北京林业大学": "https://zsb.bjfu.edu.cn",
    "对外经济贸易大学": "https://zhaosheng.uibe.edu.cn",
    "中央财经大学": "https://zsb.cufe.edu.cn",
    "中国政法大学": "https://zs.cupl.edu.cn",
    "华北电力大学": "https://zsb.ncepu.edu.cn",
    "上海财经大学": "https://zs.shfe.edu.cn",
    "华东理工大学": "https://zs.ecust.edu.cn",
    "东华大学": "https://zs.dhu.edu.cn",
    "上海外国语大学": "https://ao.shisu.edu.cn",
    "南京航空航天大学": "https://zsb.nuaa.edu.cn",
    "南京理工大学": "https://zsb.njust.edu.cn",
    "河海大学": "https://zsw.hohai.edu.cn",
    "南京农业大学": "https://zsb.njau.edu.cn",
    "中国药科大学": "https://zsb.cpu.edu.cn",
    "南京师范大学": "https://bkzs.njnu.edu.cn",
    "苏州大学": "https://zsb.suda.edu.cn",
    "江南大学": "https://zhaoSheng.jiangnan.edu.cn",
    "武汉理工大学": "https://zsb.whut.edu.cn",
    "华中农业大学": "https://zs.hzau.edu.cn",
    "华中师范大学": "https://zs.ccnu.edu.cn",
    "中南财经政法大学": "https://zs.zuel.edu.cn",
    "湖南师范大学": "https://zsb.hunnu.edu.cn",
    "暨南大学": "https://zsb.jnu.edu.cn",
    "华南师范大学": "https://zsb.scnu.edu.cn",
    "西南交通大学": "https://zsb.swjtu.edu.cn",
    "西南财经大学": "https://zsb.swufe.edu.cn",
    "西南大学": "https://zsb.swu.edu.cn",
    "四川农业大学": "https://zsc.sicau.edu.cn",
    "西安电子科技大学": "https://zsb.xidian.edu.cn",
    "长安大学": "https://zsb.chd.edu.cn",
    "西北大学": "https://zsb.nwu.edu.cn",
    "陕西师范大学": "https://zsb.snnu.edu.cn",
    "哈尔滨工程大学": "https://zsb.hrbeu.edu.cn",
    "东北林业大学": "https://zsb.nefu.edu.cn",
    "东北农业大学": "https://zsb.neau.edu.cn",
    "大连海事大学": "https://zsb.dlmu.edu.cn",
    "辽宁大学": "https://zsb.lnu.edu.cn",
    "太原理工大学": "https://zsb.tyut.edu.cn",
    "内蒙古大学": "https://zsb.imu.edu.cn",
    "南昌大学": "https://zsb.ncu.edu.cn",
    "安徽大学": "https://zsb.ahu.edu.cn",
    "合肥工业大学": "https://zsb.hfut.edu.cn",
    "郑州大学": "https://zsb.zzu.edu.cn",
    "中国矿业大学": "https://zs.cumt.edu.cn",
    "广西大学": "https://zsb.gxu.edu.cn",
    "贵州大学": "https://zs.gzu.edu.cn",
    "云南大学": "https://zsb.ynu.edu.cn",
    "海南大学": "https://ha.hainanu.edu.cn",
    "西藏大学": "https://zsb.utibet.edu.cn",
    "新疆大学": "https://zsb.xju.edu.cn",
    "宁夏大学": "https://zsb.nxu.edu.cn",
    "青海大学": "https://zsb.qhu.edu.cn",
    "延边大学": "https://zsb.ybu.edu.cn",
    "福州大学": "https://zsb.fzu.edu.cn",
    "南昌大学": "https://zsb.ncu.edu.cn",
    "中国石油大学（华东）": "https://zsb.upc.edu.cn",
    "中国地质大学（武汉）": "https://zsb.cug.edu.cn",
    "中国矿业大学（北京）": "https://zsb.cumtb.edu.cn",
    "中国石油大学（北京）": "https://zs.bjcup.edu.cn",
    "中国地质大学（北京）": "https://zsb.cugb.edu.cn",
}


def hdrs():
    return {"User-Agent": random.choice(AGENTS),
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"}


def discover_url(school_name, session):
    """探测招生网 URL"""
    # 1. 已知列表
    if school_name in KNOWN_URLS:
        return KNOWN_URLS[school_name]

    # 2. 暴力探测常见模式
    # 从校名提取拼音关键词
    # 简化：用中文名直接拼接常见域名后缀
    pinyin_map = {
        "北京": "bj", "天津": "tj", "上海": "sh", "重庆": "cq",
        "河北": "heb", "山西": "sx", "内蒙古": "nm", "辽宁": "ln",
        "吉林": "jl", "黑龙江": "hlj", "江苏": "js", "浙江": "zj",
        "安徽": "ah", "福建": "fj", "江西": "jx", "山东": "sd",
        "河南": "hn", "湖北": "hb", "湖南": "hun", "广东": "gd",
        "广西": "gx", "海南": "hi", "四川": "sc", "贵州": "gz",
        "云南": "yn", "西藏": "xz", "陕西": "sn", "甘肃": "gs",
        "青海": "qh", "宁夏": "nx", "新疆": "xj",
    }

    # 尝试直接访问常见域名
    # 大多数高校招生网域名格式: zs.{school_pinyin}.edu.cn
    # 但我们不知道拼音，所以尝试其他方法

    # 3. 访问学校官网找招生链接
    # 常见学校官网域名
    school_clean = school_name.replace("大学", "").replace("学院", "")
    school_clean = re.sub(r'[（(].*?[)）]', '', school_clean)

    # 尝试几个常见官网域名
    for prefix in ["www", "www2"]:
        for domain_suffix in [".edu.cn"]:
            url = f"http://{prefix}.{school_clean}{domain_suffix}"
            try:
                resp = session.get(url, headers=hdrs(), timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    # 在页面中找招生链接
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        text = a.get_text(strip=True)
                        href = a['href']
                        if any(kw in text for kw in ['招生', '本科招生', '招生网']):
                            return urljoin(resp.url, href)
            except Exception:
                continue

    return None


def find_score_page(base_url, session):
    """在招生网找分数页面"""
    try:
        resp = session.get(base_url, headers=hdrs(), timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return None
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 找分数相关链接
        keywords = ['历年分数', '录取分数', '录取分数线', '分数查询', '历年录取',
                    '分省分数', '专业分数', '录取统计', '投档线', '录取查询']
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']
            full_text = text + href
            if any(kw in full_text for kw in keywords):
                return urljoin(resp.url, href)

        # 模糊匹配
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.search(r'lnfs|lqfs|fsx|分数|录取', href, re.I):
                return urljoin(resp.url, href)

    except Exception:
        pass
    return None


def parse_score_table(html, school_name):
    """解析分数表"""
    soup = BeautifulSoup(html, 'html.parser')
    records = []

    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if len(rows) < 3:
            continue

        # 解析表头
        header_row = rows[0]
        # 可能有合并单元格，取所有 th/td
        headers = []
        for cell in header_row.find_all(['th', 'td']):
            colspan = int(cell.get('colspan', 1))
            text = cell.get_text(strip=True)
            headers.extend([text] * colspan)

        if not headers:
            continue

        # 识别列
        col_map = {}
        for i, h in enumerate(headers):
            h_lower = h.lower()
            if '年份' in h or '年度' in h or 'year' in h_lower:
                col_map['year'] = i
            elif '省份' in h or '地区' in h or '招生地' in h:
                col_map['province'] = i
            elif '科类' in h or '选科' in h or '科目' in h:
                col_map['subject'] = i
            elif '专业' in h and '代码' not in h and '组' not in h:
                col_map['major'] = i
            elif '最低分' in h or '录取线' in h or h == '最低':
                col_map['min_score'] = i
            elif '最高分' in h or h == '最高':
                col_map['max_score'] = i
            elif '平均分' in h or h == '平均':
                col_map['avg_score'] = i
            elif '位次' in h or '名次' in h or '排名' in h:
                col_map['rank'] = i
            elif '计划' in h or '人数' in h:
                col_map['plan'] = i
            elif '备注' in h or '说明' in h:
                col_map['remark'] = i

        if 'year' not in col_map or 'min_score' not in col_map:
            continue

        # 解析数据行
        for row in rows[1:]:
            cells = []
            for cell in row.find_all(['td', 'th']):
                colspan = int(cell.get('colspan', 1))
                text = cell.get_text(strip=True)
                cells.extend([text] * colspan)

            if len(cells) <= max(col_map.values()):
                continue

            # 年份
            year_str = cells[col_map['year']]
            year_match = re.search(r'(20\d{2})', year_str)
            if not year_match:
                continue
            year = int(year_match.group(1))
            if year < 2021 or year > 2025:
                continue

            # 河北
            if 'province' in col_map:
                if '河北' not in cells[col_map['province']]:
                    continue

            # 科类
            subject = ''
            if 'subject' in col_map:
                s = cells[col_map['subject']]
                if '物理' in s or '理' in s:
                    subject = 'physics'
                elif '历史' in s or '文' in s:
                    subject = 'history'
            if not subject:
                continue

            # 分数
            try:
                min_score = int(float(cells[col_map['min_score']]))
            except (ValueError, IndexError):
                continue
            if min_score < 100 or min_score > 750:
                continue

            # 位次
            rank = None
            if 'rank' in col_map:
                try:
                    rank_str = cells[col_map['rank']].replace(',', '').replace('，', '')
                    rank = int(float(rank_str))
                except (ValueError, IndexError):
                    pass

            # 其他字段
            max_score = None
            if 'max_score' in col_map:
                try: max_score = int(float(cells[col_map['max_score']]))
                except: pass

            avg_score = None
            if 'avg_score' in col_map:
                try: avg_score = int(float(cells[col_map['avg_score']]))
                except: pass

            major = cells[col_map.get('major', -1)] if 'major' in col_map else ''
            major_code = ''
            plan = None
            if 'plan' in col_map:
                try: plan = int(cells[col_map['plan']])
                except: pass
            remark = cells[col_map.get('remark', -1)] if 'remark' in col_map else ''

            records.append({
                "year": year, "subject": subject,
                "major": major, "majorCode": major_code,
                "minScore": min_score, "maxScore": max_score,
                "avgScore": avg_score, "minRank": rank,
                "planNum": plan, "remark": remark,
            })

    return records


def crawl_one(school_name, session):
    """爬取单个学校"""
    base_url = discover_url(school_name, session)
    if not base_url:
        return [], "no_url"

    score_url = find_score_page(base_url, session)
    if not score_url:
        # 尝试常见路径
        for path in ["/lnfs/", "/lqfs/", "/fsx/", "/lnfs.htm", "/lqfs.htm",
                     "/zsjz/lqfs.htm", "/zsxx/lqfs/"]:
            test = base_url.rstrip('/') + path
            try:
                r = session.get(test, headers=hdrs(), timeout=5, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 500:
                    score_url = r.url
                    break
            except:
                continue

    if not score_url:
        return [], "no_score_page"

    try:
        resp = session.get(score_url, headers=hdrs(), timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return [], "fetch_failed"
        resp.encoding = resp.apparent_encoding or 'utf-8'
        records = parse_score_table(resp.text, school_name)
        return records, "ok" if records else "no_hebei_data"
    except Exception as e:
        return [], f"error: {e}"


def main():
    print("=" * 60)
    print("🏫 高校招生网爬虫 v2")
    print("=" * 60)

    with open(PARSED_PATH, encoding='utf-8') as f:
        all_records = json.load(f)
    schools = {}
    for r in all_records:
        name = r.get("schoolName", "").strip()
        if name and name not in schools:
            schools[name] = {"nature": r.get("nature", "公办")}

    # 加载已有
    existing = {}
    if Path(OUTPUT_PATH).exists():
        with open(OUTPUT_PATH, encoding='utf-8') as f:
            existing = json.load(f)
        print(f"  已有: {len(existing)} 所")

    session = requests.Session()
    to_crawl = [(n, info) for n, info in schools.items() if n not in existing]
    print(f"  待爬: {len(to_crawl)} 所\n")

    success = 0
    no_data = 0

    for i, (name, info) in enumerate(to_crawl, 1):
        records, status = crawl_one(name, session)
        tag = "✓" if status == "ok" else "·"

        existing[name] = {
            "name": name, "nature": info["nature"],
            "records": records, "source": status,
        }

        if records:
            success += 1
            print(f"  [{i}/{len(to_crawl)}] {tag} {name}: {len(records)} 条")
        else:
            no_data += 1
            if i <= 50 or i % 100 == 0:
                print(f"  [{i}/{len(to_crawl)}] {tag} {name}: {status}")

        if i % 20 == 0:
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=1)

        time.sleep(random.uniform(0.3, 0.8))

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=1)

    print(f"\n{'='*60}")
    print(f"  成功: {success} | 无数据: {no_data} | 总: {len(existing)}")
    total_records = sum(len(v.get('records', [])) for v in existing.values())
    with_rank = sum(1 for v in existing.values() for r in v.get('records', []) if r.get('minRank'))
    print(f"  总记录: {total_records} | 有位次: {with_rank}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
