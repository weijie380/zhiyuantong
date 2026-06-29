"""
爬取学校元数据 v2 -- 阳光高考网 + 本地推断兜底

输出: data_raw/_gaokao_schools.json（兼容 build_output.py）
"""

import json
import re
import time
import random
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
PARSED_SCORES_PATH = os.path.join(RAW_DIR, "_parsed_scores.json")
OUTPUT_PATH = os.path.join(RAW_DIR, "_gaokao_schools.json")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
]
MIN_DELAY, MAX_DELAY, MAX_RETRIES = 1.5, 3.5, 3


def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}


def load_existing():
    if Path(OUTPUT_PATH).exists():
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return {s["name"]: s for s in data}
            return data
        except Exception:
            pass
    return {}


def save(metadata):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(metadata.values()), f, ensure_ascii=False, indent=1)


def extract_schools():
    with open(PARSED_SCORES_PATH, encoding="utf-8") as f:
        records = json.load(f)
    schools = {}
    for r in records:
        name = r.get("schoolName", "").strip()
        if not name or name in schools:
            if name in schools:
                if not schools[name].get("city") and r.get("city"):
                    schools[name]["city"] = r["city"]
            continue
        schools[name] = {
            "name": name, "schoolCode": r.get("schoolCode", ""),
            "city": r.get("city", ""), "nature": r.get("nature", "公办"),
        }
    print(f"  {len(schools)} 所学校")
    return schools


def crawl_gaokao(name, session):
    """阳光高考网搜索"""
    url = "https://gaokao.chsi.com.cn/sch/search.do"
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, params={"keywords": name, "page": "1"},
                             headers=get_headers(), timeout=15)
            if resp.status_code != 200:
                time.sleep(2)
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for tr in soup.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) < 3:
                    continue
                a = cells[0].find("a")
                if not a:
                    continue
                page_name = a.get_text(strip=True)
                if page_name != name and name not in page_name:
                    continue
                province = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                authority = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                level = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                features = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                sch_id = ""
                m = re.search(r'schId[=/-](\d+)', a.get("href", ""))
                if m:
                    sch_id = m.group(1)
                return {"province": province, "level": level or features,
                        "features": features, "authority": authority, "schId": sch_id}
            return None
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 * (attempt + 1))
    return None


# --- 本地推断 ---
UNIVERSITIES_985 = {"北京大学","清华大学","复旦大学","上海交通大学","浙江大学",
    "中国科学技术大学","南京大学","武汉大学","华中科技大学","中山大学",
    "哈尔滨工业大学","西安交通大学","北京航空航天大学","北京理工大学",
    "天津大学","南开大学","大连理工大学","吉林大学","同济大学",
    "华东师范大学","东南大学","厦门大学","山东大学","中国海洋大学",
    "湖南大学","中南大学","国防科技大学","华南理工大学","电子科技大学",
    "四川大学","重庆大学","西北工业大学","西北农林科技大学","兰州大学",
    "东北大学","北京师范大学","中国人民大学","中国农业大学","中央民族大学"}

UNIVERSITIES_211 = UNIVERSITIES_985 | {
    "北京交通大学","北京工业大学","北京科技大学","北京化工大学","北京邮电大学",
    "北京林业大学","北京中医药大学","北京外国语大学","中国传媒大学",
    "中央财经大学","对外经济贸易大学","中国政法大学","华北电力大学",
    "上海财经大学","上海大学","华东理工大学","东华大学","上海外国语大学",
    "南京航空航天大学","南京理工大学","河海大学","南京农业大学","中国药科大学",
    "南京师范大学","苏州大学","江南大学","武汉理工大学","中国地质大学",
    "华中农业大学","华中师范大学","中南财经政法大学","湖南师范大学",
    "暨南大学","华南师范大学","西南交通大学","西南财经大学","西南大学",
    "四川农业大学","西安电子科技大学","长安大学","西北大学","陕西师范大学",
    "哈尔滨工程大学","东北林业大学","东北农业大学","大连海事大学","辽宁大学",
    "太原理工大学","内蒙古大学","南昌大学","安徽大学","合肥工业大学",
    "郑州大学","中国矿业大学","广西大学","贵州大学","云南大学",
    "海南大学","西藏大学","新疆大学","石河子大学","宁夏大学","青海大学","延边大学","福州大学"}

TYPE_KW = {"理工":"理工","师范":"师范","医药":"医药","财经":"财经","政法":"政法",
    "语言":"语言","艺术":"艺术","体育":"体育","农林":"农林","民族":"民族",
    "石油":"理工","矿业":"理工","地质":"理工","建筑":"理工","电子":"理工",
    "邮电":"理工","交通":"理工","航空":"理工","航天":"理工","农业":"农林",
    "林业":"农林","中医":"医药","药科":"医药","化工":"理工"}

CITY_PROV = {
    "北京":"北京","上海":"上海","天津":"天津","重庆":"重庆",
    "石家庄":"河北","唐山":"河北","秦皇岛":"河北","邯郸":"河北","保定":"河北",
    "张家口":"河北","承德":"河北","沧州":"河北","廊坊":"河北","衡水":"河北","邢台":"河北",
    "太原":"山西","大同":"山西","临汾":"山西","运城":"山西","长治":"山西",
    "呼和浩特":"内蒙古","包头":"内蒙古","赤峰":"内蒙古","通辽":"内蒙古",
    "沈阳":"辽宁","大连":"辽宁","鞍山":"辽宁","锦州":"辽宁","抚顺":"辽宁",
    "长春":"吉林","吉林市":"吉林","延边":"吉林","四平":"吉林",
    "哈尔滨":"黑龙江","齐齐哈尔":"黑龙江","大庆":"黑龙江","佳木斯":"黑龙江","牡丹江":"黑龙江",
    "南京":"江苏","苏州":"江苏","无锡":"江苏","常州":"江苏","徐州":"江苏",
    "扬州":"江苏","镇江":"江苏","南通":"江苏","连云港":"江苏","盐城":"江苏","泰州":"江苏","宿迁":"江苏",
    "杭州":"浙江","宁波":"浙江","温州":"浙江","嘉兴":"浙江","绍兴":"浙江","金华":"浙江","衢州":"浙江","台州":"浙江","丽水":"浙江",
    "合肥":"安徽","芜湖":"安徽","蚌埠":"安徽","淮南":"安徽","马鞍山":"安徽",
    "淮北":"安徽","铜陵":"安徽","安庆":"安徽","阜阳":"安徽","宿州":"安徽","六安":"安徽","亳州":"安徽","滁州":"安徽","宣城":"安徽","池州":"安徽","黄山":"安徽",
    "福州":"福建","厦门":"福建","泉州":"福建","漳州":"福建","莆田":"福建","龙岩":"福建","三明":"福建","南平":"福建","宁德":"福建",
    "南昌":"江西","赣州":"江西","九江":"江西","上饶":"江西","吉安":"江西","景德镇":"江西","新余":"江西","鹰潭":"江西","宜春":"江西","抚州":"江西",
    "济南":"山东","青岛":"山东","烟台":"山东","潍坊":"山东","淄博":"山东","济宁":"山东","临沂":"山东","泰安":"山东","聊城":"山东","威海":"山东",
    "德州":"山东","日照":"山东","枣庄":"山东","菏泽":"山东","滨州":"山东","东营":"山东",
    "郑州":"河南","开封":"河南","洛阳":"河南","平顶山":"河南","安阳":"河南","新乡":"河南",
    "焦作":"河南","濮阳":"河南","许昌":"河南","漯河":"河南","南阳":"河南","商丘":"河南","信阳":"河南","周口":"河南","驻马店":"河南","三门峡":"河南","鹤壁":"河南",
    "武汉":"湖北","宜昌":"湖北","荆州":"湖北","襄阳":"湖北","十堰":"湖北","孝感":"湖北",
    "荆门":"湖北","黄冈":"湖北","黄石":"湖北","咸宁":"湖北","随州":"湖北","恩施":"湖北","鄂州":"湖北",
    "长沙":"湖南","株洲":"湖南","湘潭":"湖南","衡阳":"湖南","邵阳":"湖南","岳阳":"湖南",
    "常德":"湖南","益阳":"湖南","郴州":"湖南","永州":"湖南","怀化":"湖南","娄底":"湖南","湘西":"湖南","张家界":"湖南",
    "广州":"广东","深圳":"广东","珠海":"广东","汕头":"广东","佛山":"广东","韶关":"广东",
    "湛江":"广东","肇庆":"广东","江门":"广东","茂名":"广东","惠州":"广东","梅州":"广东",
    "汕尾":"广东","河源":"广东","阳江":"广东","清远":"广东","东莞":"广东","中山":"广东","潮州":"广东","揭阳":"广东",
    "南宁":"广西","柳州":"广西","桂林":"广西","梧州":"广西","北海":"广西","贵港":"广西","玉林":"广西","百色":"广西","河池":"广西","来宾":"广西","崇左":"广西","钦州":"广西","防城港":"广西","贺州":"广西",
    "海口":"海南","三亚":"海南",
    "成都":"四川","绵阳":"四川","德阳":"四川","宜宾":"四川","南充":"四川","达州":"四川",
    "泸州":"四川","遂宁":"四川","乐山":"四川","内江":"四川","自贡":"四川","攀枝花":"四川",
    "雅安":"四川","广安":"四川","巴中":"四川","资阳":"四川","眉山":"四川","凉山":"四川","甘孜":"四川","阿坝":"四川",
    "贵阳":"贵州","遵义":"贵州","六盘水":"贵州","安顺":"贵州","毕节":"贵州","铜仁":"贵州","黔东南":"贵州","黔南":"贵州","黔西南":"贵州",
    "昆明":"云南","曲靖":"云南","玉溪":"云南","保山":"云南","昭通":"云南","丽江":"云南","普洱":"云南","临沧":"云南","楚雄":"云南","红河":"云南","文山":"云南","大理":"云南","德宏":"云南","西双版纳":"云南",
    "拉萨":"西藏",
    "西安":"陕西","咸阳":"陕西","宝鸡":"陕西","渭南":"陕西","汉中":"陕西","安康":"陕西","商洛":"陕西","延安":"陕西","榆林":"陕西","铜川":"陕西",
    "兰州":"甘肃","天水":"甘肃","庆阳":"甘肃","平凉":"甘肃","酒泉":"甘肃","武威":"甘肃","定西":"甘肃","陇南":"甘肃","金昌":"甘肃","白银":"甘肃","张掖":"甘肃",
    "西宁":"青海","银川":"宁夏","固原":"宁夏","吴忠":"宁夏","中卫":"宁夏","石嘴山":"宁夏",
    "乌鲁木齐":"新疆","石河子":"新疆","昌吉":"新疆","喀什":"新疆","伊犁":"新疆","塔城":"新疆","阿勒泰":"新疆","哈密":"新疆","吐鲁番":"新疆","阿克苏":"新疆","和田":"新疆",
}


def infer_type(name):
    for kw, t in TYPE_KW.items():
        if kw in name:
            return t
    return "综合"


def infer_level(name):
    if name in UNIVERSITIES_985:
        return "985/211"
    if name in UNIVERSITIES_211:
        return "211"
    return "普通本科"


def infer_province(name, city):
    if city:
        for cn, prov in CITY_PROV.items():
            if cn in city:
                return prov
    for prov in ["北京","天津","上海","重庆","河北","山西","内蒙古","辽宁","吉林","黑龙江",
                  "江苏","浙江","安徽","福建","江西","山东","河南","湖北","湖南","广东","广西","海南",
                  "四川","贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆"]:
        if name.startswith(prov) or prov in name:
            return prov
    for cn, prov in CITY_PROV.items():
        if cn in name:
            return prov
    return ""


def main():
    print("=" * 60)
    print("🏫 爬取学校元数据 v2")
    print("=" * 60)

    schools = extract_schools()
    existing = load_existing()
    print(f"  已有元数据: {len(existing)} 条")

    session = requests.Session()
    gaokao_ok = 0
    local_ok = 0
    skipped = 0

    for i, (name, info) in enumerate(schools.items(), 1):
        if name in existing and existing[name].get("province"):
            skipped += 1
            continue

        meta = crawl_gaokao(name, session)
        if meta:
            existing[name] = {
                "name": name, "id": "",
                "province": meta.get("province", ""),
                "city": info.get("city", ""),
                "level": meta.get("level", "") or meta.get("features", ""),
                "type": infer_type(name),
                "nature": info.get("nature", "公办"),
                "batch": "本科",
                "source": "gaokao",
            }
            gaokao_ok += 1
            print(f"  [{i}/{len(schools)}] {name} -> {meta.get('province','')} {meta.get('level','')} ✓")
        else:
            existing[name] = {
                "name": name, "id": "",
                "province": infer_province(name, info.get("city", "")),
                "city": info.get("city", ""),
                "level": infer_level(name),
                "type": infer_type(name),
                "nature": info.get("nature", "公办"),
                "batch": "本科",
                "source": "local",
            }
            local_ok += 1
            print(f"  [{i}/{len(schools)}] {name} -> {existing[name]['province']} {existing[name]['level']} (本地)")

        if i % 20 == 0:
            save(existing)
        if meta:
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    save(existing)
    filled = sum(1 for s in existing.values() if s.get("province"))
    print(f"\n  阳光高考网: {gaokao_ok} | 本地推断: {local_ok} | 跳过: {skipped}")
    print(f"  province 覆盖: {filled}/{len(existing)} ({filled*100//len(existing)}%)")


if __name__ == "__main__":
    main()
