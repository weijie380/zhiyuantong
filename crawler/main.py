"""
志愿通爬虫 · 主流程

运行顺序:
  1. download.py  - 下载原始 Excel & PDF
  2. parse_scores.py - 解析 Excel → 结构化记录
  3. parse_rankmap.py - 解析 PDF → 分数→位次映射
  4. crawl_schools.py - 爬取阳光高考网学校元数据
  5. build_output.py - 构建最终 JSON

用法:
  python main.py           # 运行全流程
  python main.py --step 1  # 只运行第 1 步
"""

import sys
import subprocess
from pathlib import Path


STEPS = [
    ("download", "下载原始文件", "download.py"),
    ("parse_scores", "解析投档统计 Excel", "parse_scores.py"),
    ("parse_rankmap", "解析一分一段表 PDF", "parse_rankmap.py"),
    ("crawl_schools", "爬取学校元数据", "crawl_schools.py"),
    ("build_output", "构建最终 JSON", "build_output.py"),
]


def run_step(script_name, description):
    """运行单个步骤"""
    print("\n" + "█" * 60)
    print(f"█  步骤: {description}")
    print("█" * 60)

    script_path = Path(__file__).parent / script_name
    result = subprocess.run(
        ["python3", str(script_path)],
        cwd=str(Path(__file__).parent),
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\n❌ 步骤失败（exit code: {result.returncode}）")
        return False
    return True


def main():
    args = sys.argv[1:]

    # 解析 --step 参数
    step_filter = None
    if args and args[0] == "--step":
        step_filter = int(args[1])

    print("╔══════════════════════════════════════════════════════╗")
    print("║         🎓 志愿通 · 高考录取数据爬虫                  ║")
    print("║   数据源: 河北省教育考试院 + 阳光高考网                ║")
    print("╚══════════════════════════════════════════════════════╝")

    for i, (name, desc, script) in enumerate(STEPS, 1):
        if step_filter and i != step_filter:
            continue
        if not run_step(script, desc):
            print(f"\n⚠️ 步骤 {i} ({name}) 失败，停止后续步骤")
            break

    print("\n" + "=" * 60)
    print("🎉 爬虫运行完毕！")
    print("=" * 60)


if __name__ == "__main__":
    main()
