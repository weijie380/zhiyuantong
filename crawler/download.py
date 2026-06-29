"""
下载原始数据文件
- 从河北省教育考试院文章页下载投档统计 Excel
- 从河北省教育考试院文章页下载一分一段表 PDF
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from config import (
    RAW_DIR, YEARS, SUBJECTS, SUBJECT_LABELS,
    SCORE_ARTICLES, RANK_ARTICLES,
    HEADERS, DOWNLOAD_DELAY,
)


def download_file(url, dest_path):
    """下载文件到本地"""
    print(f"  下载: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=60, allow_redirects=True)
    resp.raise_for_status()
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    size_kb = len(resp.content) / 1024
    print(f"    → {dest_path} ({size_kb:.1f} KB)")
    return dest_path


def find_links_from_article(article_url):
    """从河北省教育考试院文章页中提取附件下载链接"""
    print(f"  解析文章页: {article_url}")
    resp = requests.get(article_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if not text:
            # 可能链接在 img 或其他元素内
            text = a.get("title", "")

        # 过滤出附件链接
        if "file.hebeea.edu.cn" in href and (".xlsx" in href or ".xls" in href or ".pdf" in href):
            # 确保完整 URL
            if href.startswith("/"):
                href = f"https://www.hebeea.edu.cn{href}"
            elif not href.startswith("http"):
                href = f"https://www.hebeea.edu.cn/{href}"

            links[text] = href

    if not links:
        # 尝试通过正则匹配正文中的链接
        found = re.findall(r'https?://file\.hebeea\.edu\.cn[^\s"\']+\.(?:xlsx|xls|pdf)', resp.text)
        for url in found:
            links[url.split("/")[-1]] = url

    print(f"    找到 {len(links)} 个附件链接")
    for name, url in links.items():
        print(f"      {name}: {url[:80]}...")
    return links


def download_score_excels():
    """下载所有年份×科类的投档统计 Excel"""
    print("\n" + "=" * 60)
    print("📥 下载投档统计 Excel 文件")
    print("=" * 60)

    for year in YEARS:
        print(f"\n--- {year} 年 ---")
        article_url = SCORE_ARTICLES[year]
        links = find_links_from_article(article_url)

        # 按科类分类
        subject_files = {"physics": None, "history": None}
        for name, url in links.items():
            if not url.endswith((".xlsx", ".xls")):
                continue
            if "物理" in name or "physics" in name.lower():
                subject_files["physics"] = url
            elif "历史" in name or "history" in name.lower():
                subject_files["history"] = url

        for subject in SUBJECTS:
            url = subject_files.get(subject)
            if not url:
                print(f"  ⚠️ 未找到 {subject} 的 Excel 链接，尝试自动匹配...")
                # 回退：尝试按 URL 文件名匹配
                for link_name, link_url in links.items():
                    if not link_url.endswith((".xlsx", ".xls")):
                        continue
                    subj_label = SUBJECT_LABELS[subject]
                    if subj_label in link_name or subj_label in link_url:
                        url = link_url
                        break
                if url:
                    print(f"  ✓ 自动匹配到: {url[:80]}...")

            if url:
                ext = "xlsx" if url.endswith("xlsx") else "xls"
                dest = f"{RAW_DIR}/{year}_{subject}.{ext}"
                if Path(dest).exists():
                    print(f"  ✓ {dest} 已存在，跳过")
                else:
                    download_file(url, dest)
            else:
                print(f"  ❌ 无法找到 {year} {subject} 的下载链接")

        time.sleep(DOWNLOAD_DELAY)


def download_rank_pdfs():
    """下载所有年份的一分一段表 PDF"""
    print("\n" + "=" * 60)
    print("📥 下载一分一段表 PDF 文件")
    print("=" * 60)

    for year in YEARS:
        print(f"\n--- {year} 年 ---")
        article_url = RANK_ARTICLES[year]
        links = find_links_from_article(article_url)

        # 找物理/历史成绩统计表
        rank_pdf = None
        for name, url in links.items():
            if not url.endswith(".pdf"):
                continue
            # 匹配物理/历史组合的成绩统计表
            if ("物理" in name and "历史" in name) or "成绩统计" in name or "一分一档" in name:
                # 优先匹配同时包含物理和历史的（一般是一个文件）
                if "物理" in name and "历史" in name:
                    rank_pdf = url
                    break
                elif rank_pdf is None:
                    rank_pdf = url

        if rank_pdf:
            dest = f"{RAW_DIR}/{year}_rank.pdf"
            if Path(dest).exists():
                print(f"  ✓ {dest} 已存在，跳过")
            else:
                download_file(rank_pdf, dest)
        else:
            print(f"  ❌ 未找到 {year} 年一分一段表")

        time.sleep(DOWNLOAD_DELAY)


if __name__ == "__main__":
    download_score_excels()
    download_rank_pdfs()
    print("\n✅ 下载完成")
