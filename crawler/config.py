"""
志愿通爬虫 · 配置文件
数据源：河北省教育考试院 + 阳光高考网
"""

import os

# --- 路径 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "public", "data")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 年份与科类 ---
YEARS = [2021, 2022, 2023, 2024, 2025]
SUBJECTS = ["physics", "history"]
SUBJECT_LABELS = {
    "physics": "物理科目组合",
    "history": "历史科目组合",
}

# --- 河北省教育考试院：本科批投档统计（Excel） ---
SCORE_ARTICLES = {
    2025: "https://www.hebeea.edu.cn/c/2025-07-23/489213.html",
    2024: "https://www.hebeea.edu.cn/c/2024-07-22/489446.html",
    2023: "https://www.hebeea.edu.cn/c/2023-07-25/489286.html",
    2022: "https://www.hebeea.edu.cn/c/2022-07-25/488817.html",
    2021: "https://www.hebeea.edu.cn/c/2021-07-24/488945.html",
}

# --- 河北省教育考试院：一分一段表（PDF） ---
RANK_ARTICLES = {
    2025: "https://www.hebeea.edu.cn/c/2025-06-24/488903.html",
    2024: "https://www.hebeea.edu.cn/c/2024-06-24/489444.html",
    2023: "https://www.hebeea.edu.cn/c/2023-06-24/488564.html",
    2022: "https://www.hebeea.edu.cn/c/2022-06-24/489265.html",
    2021: "https://www.hebeea.edu.cn/c/2021-06-24/488536.html",
}

# --- 阳光高考网：院校库 ---
GAOKAO_SCHOOL_SEARCH = "https://gaokao.chsi.com.cn/sch/search.do"
# AJAX 接口（推测，实际可能需要抓包确认）
GAOKAO_SCHOOL_API = "https://gaokao.chsi.com.cn/sch/search.do"

# --- 请求头 ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# --- 下载延迟（秒），避免被封 ---
DOWNLOAD_DELAY = 1.0
