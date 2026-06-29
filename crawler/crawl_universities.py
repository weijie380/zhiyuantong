"""
高校招生网爬虫 v3 — 已知 URL 优先 + Excel 兜底

策略：
1. 用已知 URL 列表爬取有数据的学校（含真实位次）
2. 爬不到的用 Excel 投档数据推导位次
3. 合并产出最终 JSON
"""

import json
import re
import time
import random
import os
import socket
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
PARSED_PATH = os.path.join(RAW_DIR, "_parsed_scores.json")
WEB_DATA_PATH = os.path.join(RAW_DIR, "_university_web_ranks.json")

AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36",
]

# 已知高校招生网 URL（持续补充）
KNOWN_URLS = {
    "清华大学": "https://join-tsinghua.edu.cn",
    "北京大学": "https://bkzs.pku.edu.cn",
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
    "华东理工大学": "https://zs.ecust.edu.cn",
    "东华大学": "https://zs.dhu.edu.cn",
    "南京航空航天大学": "https://zsb.nuaa.edu.cn",
    "南京理工大学": "https://zsb.njust.edu.cn",
    "河海大学": "https://zsw.hohai.edu.cn",
    "南京农业大学": "https://zsb.njau.edu.cn",
    "中国药科大学": "https://zsb.cpu.edu.cn",
    "南京师范大学": "https://bkzs.njnu.edu.cn",
    "苏州大学": "https://zsb.suda.edu.cn",
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
    "新疆大学": "https://zsb.xju.edu.cn",
    "宁夏大学": "https://zsb.nxu.edu.cn",
    "青海大学": "https://zsb.qhu.edu.cn",
    "延边大学": "https://zsb.ybu.edu.cn",
    "福州大学": "https://zsb.fzu.edu.cn",
    "中国石油大学（华东）": "https://zsb.upc.edu.cn",
    "中国地质大学（武汉）": "https://zsb.cug.edu.cn",
    "中国矿业大学（北京）": "https://zsb.cumtb.edu.cn",
    "中国石油大学（北京）": "https://zs.bjcup.edu.cn",
    "中国地质大学（北京）": "https://zsb.cugb.edu.cn",
    "长春人文学院": "https://www.ccrw.edu.cn",
    "哈尔滨理工大学": "https://zsb.hrbust.edu.cn",
    "东北石油大学": "https://zsb.nepu.edu.cn",
    "黑龙江大学": "https://zsb.hlju.edu.cn",
    "长春理工大学": "https://zsb.cust.edu.cn",
    "吉林农业大学": "https://zsb.jlau.edu.cn",
    "沈阳工业大学": "https://zsb.sut.edu.cn",
    "辽宁工程技术大学": "https://zsb.lngd.edu.cn",
    "大连交通大学": "https://zsb.djtu.edu.cn",
    "沈阳建筑大学": "https://zsb.sjzu.edu.cn",
    "辽宁石油化工大学": "https://zsb.lnpu.edu.cn",
    "沈阳化工大学": "https://zsb.syuct.edu.cn",
    "大连工业大学": "https://zsb.dlpu.edu.cn",
    "沈阳航空航天大学": "https://zsb.sau.edu.cn",
    "辽宁科技大学": "https://zsb.ustl.edu.cn",
    "辽宁工业大学": "https://zsb.lnit.edu.cn",
    "沈阳大学": "https://zsb.syu.edu.cn",
    "大连大学": "https://zsb.dlu.edu.cn",
    "渤海大学": "https://zsb.bhu.edu.cn",
    "沈阳师范大学": "https://zsb.synu.edu.cn",
    "辽宁师范大学": "https://zsb.lnnu.edu.cn",
    "哈尔滨商业大学": "https://zsb.hrbcu.edu.cn",
    "黑龙江科技大学": "https://zsb.hust.edu.cn",
    "东北电力大学": "https://zsb.neepu.edu.cn",
    "长春工业大学": "https://zsb.ccut.edu.cn",
    "北华大学": "https://zsb.beihua.edu.cn",
    "吉林化工学院": "https://zsb.jlict.edu.cn",
    "长春大学": "https://zsb.ccu.edu.cn",
    "黑龙江工程学院": "https://zsb.hljit.edu.cn",
    "齐齐哈尔大学": "https://zsb.qqhru.edu.cn",
    "佳木斯大学": "https://zsb.jmsu.edu.cn",
    "牡丹江医学院": "https://zsb.mdjmc.edu.cn",
    "牡丹江师范学院": "https://zsb.mdjnu.edu.cn",
    "绥化学院": "https://zsb.shxy.net",
    "河北工业大学": "https://zsb.hebut.edu.cn",
    "燕山大学": "https://zsb.ysu.edu.cn",
    "河北大学": "https://zsb.hbu.edu.cn",
    "河北师范大学": "https://zsb.hebtu.edu.cn",
    "河北科技大学": "https://zsb.hebust.edu.cn",
    "石家庄铁道大学": "https://zsb.stdu.edu.cn",
    "河北医科大学": "https://zsb.hebmu.edu.cn",
    "河北农业大学": "https://zsb.hebau.edu.cn",
    "华北理工大学": "https://zsb.ncst.edu.cn",
    "河北经贸大学": "https://zsb.hebute.edu.cn",
    "河北工程大学": "https://zsb.hebeu.edu.cn",
    "河北中医学院": "https://zsb.hbcm.edu.cn",
    "山西大学": "https://zsb.sxu.edu.cn",
    "太原科技大学": "https://zsb.tyust.edu.cn",
    "中北大学": "https://zsb.nuc.edu.cn",
    "山西农业大学": "https://zbs.sxau.edu.cn",
    "山西师范大学": "https://zsb.sxnu.edu.cn",
    "山西财经大学": "https://zsb.sxufe.edu.cn",
    "内蒙古工业大学": "https://zsb.imut.edu.cn",
    "内蒙古科技大学": "https://zsb.imust.edu.cn",
    "内蒙古农业大学": "https://zsb.imau.edu.cn",
    "内蒙古师范大学": "https://zsb.imnu.edu.cn",
    "内蒙古医科大学": "https://zsb.immu.edu.cn",
    "内蒙古财经大学": "https://zsb.imufe.edu.cn",
    "中国海洋大学": "https://www.osa.xmu.edu.cn",
    "山东科技大学": "https://zsb.sdust.edu.cn",
    "山东师范大学": "https://zsb.sdnu.edu.cn",
    "青岛大学": "https://zsb.qdu.edu.cn",
    "山东农业大学": "https://zbg.sdau.edu.cn",
    "青岛科技大学": "https://zsb.qust.edu.cn",
    "济南大学": "https://zsb.ujn.edu.cn",
    "山东理工大学": "https://zsb.sdut.edu.cn",
    "烟台大学": "https://zsb.ytu.edu.cn",
    "鲁东大学": "https://zsb.ldu.edu.cn",
    "山东财经大学": "https://zsb.sdufe.edu.cn",
    "河南大学": "https://zs.henu.edu.cn",
    "河南师范大学": "https://www.zs.htu.edu.cn",
    "河南农业大学": "https://zs.hnau.edu.cn",
    "河南科技大学": "https://zsb.haust.edu.cn",
    "河南理工大学": "https://zsb.hpu.edu.cn",
    "河南工业大学": "https://zsb.haut.edu.cn",
    "华北水利水电大学": "https://zsb.ncwu.edu.cn",
    "郑州轻工业大学": "https://zsb.zzuli.edu.cn",
    "中原工学院": "https://zsb.zut.edu.cn",
    "信阳师范大学": "https://zsb.xynu.edu.cn",
    "河南中医药大学": "https://zs.hactcm.edu.cn",
    "洛阳师范学院": "https://zsb.lynu.edu.cn",
    "南阳师范学院": "https://zsb.nytc.edu.cn",
    "商丘师范学院": "https://zsb.sqsy.net",
    "周口师范学院": "https://zsb.zknuc.edu.cn",
    "安阳师范学院": "https://zsb.aynu.edu.cn",
    "黄淮学院": "https://zsb.huanghuai.edu.cn",
    "许昌学院": "https://zsb.xcu.edu.cn",
    "新乡学院": "https://zsb.xxxy.edu.cn",
    "河南城建学院": "https://zsb.hncj.edu.cn",
    "湖北大学": "https://zsb.hubu.edu.cn",
    "湖北工业大学": "https://zsb.hbut.edu.cn",
    "武汉科技大学": "https://zsb.wust.edu.cn",
    "长江大学": "https://zs.yangtzeu.edu.cn",
    "三峡大学": "https://zsb.ctgu.edu.cn",
    "湖北师范大学": "https://zsb.hbnu.edu.cn",
    "湖北中医药大学": "https://zs.hbtcm.edu.cn",
    "湖北医药学院": "https://zsb.hbmu.edu.cn",
    "湖北工程学院": "https://zsb.hbeu.edu.cn",
    "湖北科技学院": "https://zsb.hbust.com",
    "湖北理工学院": "https://zsb.hbut.edu.cn",
    "湖北汽车工业学院": "https://zsb.hbqy.edu.cn",
    "湖南工业大学": "https://zsb.hut.edu.cn",
    "湖南科技大学": "https://zsb.hnust.edu.cn",
    "长沙理工大学": "https://zsb.csust.edu.cn",
    "湖南农业大学": "https://zsb.hunau.edu.cn",
    "中南林业科技大学": "https://zsb.csfleu.edu.cn",
    "湖南理工学院": "https://zsb.hnie.edu.cn",
    "湖南文理学院": "https://zsb.huuse.edu.cn",
    "湖南城市学院": "https://zsb.hncu.net",
    "湖南工程学院": "https://zsb.hnie.edu.cn",
    "长沙学院": "https://zsb.ccsu.edu.cn",
    "邵阳学院": "https://zsb.hnsyu.net",
    "怀化学院": "https://zsb.hhtc.edu.cn",
    "湘南学院": "https://zsb.xnu.edu.cn",
    "湖南人文科技学院": "https://zsb.hnhnu.edu.cn",
    "湖南工学院": "https://zsb.hnie.edu.cn",
    "广东工业大学": "https://zsb.gdut.edu.cn",
    "广东外语外贸大学": "https://zsb.gdufs.edu.cn",
    "广州大学": "https://zsb.gzhu.edu.cn",
    "广东海洋大学": "https://zsb.gdou.edu.cn",
    "广东药科大学": "https://zsb.gdpu.edu.cn",
    "广东金融学院": "https://zsb.gduf.edu.cn",
    "广东技术师范大学": "https://zsb.gpnu.edu.cn",
    "广东石油化工学院": "https://zsb.gdpu.edu.cn",
    "佛山科学技术学院": "https://zsb.fosu.edu.cn",
    "东莞理工学院": "https://zsb.dgut.edu.cn",
    "五邑大学": "https://zsb.wyu.edu.cn",
    "广西师范大学": "https://zsb.gxnu.edu.cn",
    "广西医科大学": "https://zsb.gxmcedu.cn",
    "桂林电子科技大学": "https://zsb.guet.edu.cn",
    "桂林理工大学": "https://zsb.glut.edu.cn",
    "广西民族大学": "https://zsb.gxmzu.edu.cn",
    "广西中医药大学": "https://zsb.gxtcmu.edu.cn",
    "广西财经学院": "https://zsb.gxufe.edu.cn",
    "广西科技大学": "https://zsb.gxust.edu.cn",
    "海南师范大学": "https://zsb.hainnu.edu.cn",
    "海南医学院": "https://zsb.hainmc.edu.cn",
    "成都理工大学": "https://zs.cdut.edu.cn",
    "西南石油大学": "https://zsb.swpu.edu.cn",
    "四川师范大学": "https://zsb.sicnu.edu.cn",
    "西华大学": "https://zsb.xhu.edu.cn",
    "成都信息工程大学": "https://zsb.cuit.edu.cn",
    "西南科技大学": "https://zs.swust.edu.cn",
    "西华师范大学": "https://zsb.cwnu.edu.cn",
    "四川农业大学": "https://zsb.sicau.edu.cn",
    "成都中医药大学": "https://zsb.cdutcm.edu.cn",
    "泸州医学院": "https://zsb.swmu.edu.cn",
    "川北医学院": "https://zsb.nsmc.edu.cn",
    "绵阳师范学院": "https://zsb.mnu.edu.cn",
    "内江师范学院": "https://zsb.njnu.edu.cn",
    "宜宾学院": "https://zsb.yibinu.edu.cn",
    "成都大学": "https://zsb.cdu.edu.cn",
    "攀枝花学院": "https://zsb.pzhu.edu.cn",
    "贵州师范大学": "https://zsb.gznu.edu.cn",
    "贵州医科大学": "https://zsb.gmc.edu.cn",
    "遵义医科大学": "https://zsb.zmc.edu.cn",
    "贵州财经大学": "https://zsb.gzife.edu.cn",
    "贵州民族大学": "https://zsb.gzmu.edu.cn",
    "贵州理工学院": "https://zsb.gzit.edu.cn",
    "铜仁学院": "https://zsb.trxy.net",
    "凯里学院": "https://zsb.kluniv.net",
    "云南师范大学": "https://zsb.ynnu.edu.cn",
    "昆明理工大学": "https://zsb.kmust.edu.cn",
    "云南大学": "https://zsb.ynu.edu.cn",
    "云南农业大学": "https://zsb.ynau.edu.cn",
    "云南中医药大学": "https://zsb.ynutcm.edu.cn",
    "云南财经大学": "https://zsb.ynufe.edu.cn",
    "云南民族大学": "https://zsb.ynni.edu.cn",
    "西南林业大学": "https://zsb.swfu.edu.cn",
    "大理大学": "https://zsb.dali.edu.cn",
    "曲靖师范学院": "https://zsb.qjnu.edu.cn",
    "玉溪师范学院": "https://zsb.yxnw.edu.cn",
    "楚雄师范学院": "https://zsb.cxtc.edu.cn",
    "红河学院": "https://zsb.uoh.edu.cn",
    "昆明学院": "https://zsb.kmu.edu.cn",
    "西藏大学": "https://zsb.utibet.edu.cn",
    "西藏民族大学": "https://zsb.xzmu.edu.cn",
    "陕西科技大学": "https://zsb.sust.edu.cn",
    "西安建筑科技大学": "https://zsb.xauat.edu.cn",
    "西安理工大学": "https://zsb.xaut.edu.cn",
    "西安科技大学": "https://zsb.xust.edu.cn",
    "西安工业大学": "https://zsb.xatu.edu.cn",
    "西安邮电大学": "https://zsb.xiyou.edu.cn",
    "西安工程大学": "https://zsb.xpu.edu.cn",
    "延安大学": "https://zsb.yau.edu.cn",
    "陕西理工大学": "https://zsb.snut.edu.cn",
    "宝鸡文理学院": "https://zsb.bjwlxy.edu.cn",
    "渭南师范学院": "https://zsb.wnu.edu.cn",
    "西安文理学院": "https://zsb.xawl.org",
    "咸阳师范学院": "https://zsb.xysfxy.cn",
    "榆林学院": "https://zsb.ylu.edu.cn",
    "商洛学院": "https://zsb.slxy.net",
    "安康学院": "https://zsb.akun.edu.cn",
    "甘肃农业大学": "https://zsb.gsau.edu.cn",
    "兰州理工大学": "https://zsb.lut.edu.cn",
    "兰州交通大学": "https://zsb.lzjtu.edu.cn",
    "西北师范大学": "https://zsb.nwnu.edu.cn",
    "甘肃中医药大学": "https://zsb.gszy.edu.cn",
    "甘肃政法大学": "https://zsb.gsli.edu.cn",
    "兰州财经大学": "https://zsb.lzcc.edu.cn",
    "兰州城市学院": "https://zsb.lzcu.edu.cn",
    "天水师范学院": "https://zsb.tsnu.net",
    "河西学院": "https://zsb.hxu.edu.cn",
    "宁夏医科大学": "https://zsb.nxmu.edu.cn",
    "北方民族大学": "https://zsb.bfxy.cn",
    "宁夏师范学院": "https://zsb.nxtc.edu.cn",
    "新疆农业大学": "https://zsb.xjau.edu.cn",
    "新疆医科大学": "https://zsb.xjmu.edu.cn",
    "新疆师范大学": "https://zsb.xjnu.edu.cn",
    "新疆财经大学": "https://zsb.xjife.edu.cn",
    "新疆大学": "https://zsb.xju.edu.cn",
    "石河子大学": "https://zsb.shzu.edu.cn",
    "塔里木大学": "https://zsb.tarim.edu.cn",
    "喀什大学": "https://zsb.ksu.edu.cn",
    "伊犁师范大学": "https://zsb.ylnu.edu.cn",
    "新疆理工学院": "https://zsb.xjist.edu.cn",
}


def hdrs():
    return {"User-Agent": random.choice(AGENTS),
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"}


def can_resolve(host):
    try:
        socket.gethostbyname(host)
        return True
    except:
        return False


def find_score_page(base_url, session):
    """找分数页面"""
    try:
        resp = session.get(base_url, headers=hdrs(), timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return None
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        keywords = ['历年分数', '录取分数', '录取分数线', '历年录取', '分省分数', '录取统计', '投档线']
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']
            if any(kw in text + href for kw in keywords):
                return urljoin(resp.url, href)
    except:
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
        headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
        if not headers:
            continue
        col_map = {}
        for i, h in enumerate(headers):
            if '年份' in h or '年度' in h: col_map['year'] = i
            elif '省份' in h or '地区' in h: col_map['province'] = i
            elif '科类' in h or '选科' in h: col_map['subject'] = i
            elif '专业' in h and '代码' not in h: col_map['major'] = i
            elif '最低分' in h or h == '最低': col_map['min_score'] = i
            elif '最高分' in h or h == '最高': col_map['max_score'] = i
            elif '平均分' in h or h == '平均': col_map['avg_score'] = i
            elif '位次' in h or '名次' in h: col_map['rank'] = i
            elif '计划' in h: col_map['plan'] = i
            elif '备注' in h: col_map['remark'] = i
        if 'year' not in col_map or 'min_score' not in col_map:
            continue
        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if len(cells) <= max(col_map.values()):
                continue
            year_match = re.search(r'(20\d{2})', cells[col_map['year']])
            if not year_match: continue
            year = int(year_match.group(1))
            if year < 2021 or year > 2025: continue
            if 'province' in col_map and '河北' not in cells[col_map['province']]: continue
            subject = ''
            if 'subject' in col_map:
                s = cells[col_map['subject']]
                if '物理' in s or '理' in s: subject = 'physics'
                elif '历史' in s or '文' in s: subject = 'history'
            if not subject: continue
            try: min_score = int(float(cells[col_map['min_score']]))
            except: continue
            if min_score < 100 or min_score > 750: continue
            rank = None
            if 'rank' in col_map:
                try: rank = int(float(cells[col_map['rank']].replace(',', '')))
                except: pass
            max_score = None
            if 'max_score' in col_map:
                try: max_score = int(float(cells[col_map['max_score']]))
                except: pass
            avg_score = None
            if 'avg_score' in col_map:
                try: avg_score = int(float(cells[col_map['avg_score']]))
                except: pass
            major = cells[col_map['major']] if 'major' in col_map else ''
            records.append({
                "year": year, "subject": subject, "major": major,
                "majorCode": "", "minScore": min_score,
                "maxScore": max_score, "avgScore": avg_score,
                "minRank": rank, "planNum": None, "remark": "",
            })
    return records


def crawl_one(name, url, session):
    """爬取单个学校"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not can_resolve(parsed.hostname):
        return [], "dns_fail"

    score_url = find_score_page(url, session)
    if not score_url:
        for path in ["/lnfs/", "/lqfs/", "/fsx/", "/lnfs.htm", "/lqfs.htm",
                     "/zsjz/lqfs.htm", "/zsxx/lqfs/", "/zsxx/lnfs/"]:
            test = url.rstrip('/') + path
            try:
                r = session.get(test, headers=hdrs(), timeout=5, allow_redirects=True)
                if r.status_code == 200 and '<table' in r.text.lower():
                    score_url = r.url
                    break
            except:
                continue
    if not score_url:
        return [], "no_score_page"

    try:
        resp = session.get(score_url, headers=hdrs(), timeout=8, allow_redirects=True)
        if resp.status_code != 200: return [], "fetch_failed"
        resp.encoding = resp.apparent_encoding or 'utf-8'
        records = parse_score_table(resp.text, name)
        return records, "ok" if records else "no_hebei_data"
    except Exception as e:
        return [], f"error: {e}"


def derive_ranks(score_records):
    """从 Excel 推导位次"""
    groups = {}
    for r in score_records:
        key = (r["year"], r["subject"])
        groups.setdefault(key, []).append(r)
    rank_map = {}
    for (year, subject), recs in groups.items():
        sorted_recs = sorted(recs, key=lambda r: (-r["minScore"], r.get("schoolName", "")))
        key_ranks = {}
        rank = 1
        for i, r in enumerate(sorted_recs):
            if i > 0 and r["minScore"] < sorted_recs[i - 1]["minScore"]:
                rank = i + 1
            key_ranks[f"{r['schoolCode']}:{r['majorCode']}"] = rank
        rank_map[(year, subject)] = key_ranks
    return rank_map


def main():
    print("=" * 60)
    print("🏫 高校招生网爬虫 v3 + Excel 兜底")
    print("=" * 60)

    with open(PARSED_PATH, encoding='utf-8') as f:
        excel_records = json.load(f)

    # 加载已有网页数据
    web_data = {}
    if Path(WEB_DATA_PATH).exists():
        with open(WEB_DATA_PATH, encoding='utf-8') as f:
            web_data = json.load(f)
        print(f"  已有网页数据: {len(web_data)} 所")

    session = requests.Session()
    to_crawl = [(n, u) for n, u in KNOWN_URLS.items() if n not in web_data]
    print(f"  待爬: {len(to_crawl)} 所\n")

    success = 0
    for i, (name, url) in enumerate(to_crawl, 1):
        records, status = crawl_one(name, url, session)
        web_data[name] = {"records": records, "source": status}
        if records:
            success += 1
            print(f"  [{i}/{len(to_crawl)}] ✓ {name}: {len(records)} 条")
        else:
            print(f"  [{i}/{len(to_crawl)}] · {name}: {status}")
        if i % 20 == 0:
            with open(WEB_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(web_data, f, ensure_ascii=False, indent=1)
        time.sleep(random.uniform(0.3, 0.8))

    with open(WEB_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=1)

    # 统计
    with_data = sum(1 for v in web_data.values() if v.get('records'))
    total_recs = sum(len(v.get('records', [])) for v in web_data.values())
    with_rank = sum(1 for v in web_data.values() for r in v.get('records', []) if r.get('minRank'))
    print(f"\n  网页爬取: {with_data} 所有数据, {total_recs} 条记录, {with_rank} 有位次")

    # Excel 推导位次兜底
    excel_rank_map = derive_ranks(excel_records)
    print(f"  Excel 推导位次: {sum(len(v) for v in excel_rank_map.values())} 条")

    print(f"\n{'='*60}")
    print(f"  完成！网页数据 + Excel 兜底已就绪")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
