# 志愿通 · 爬虫

从河北省教育考试院采集全国高校在河北的本科批录取数据（2021-2025）。

## 数据源

| 数据 | 来源 | 格式 | 说明 |
|------|------|------|------|
| 投档统计 | 河北省教育考试院「往年数据」 | Excel (.xlsx) | 专业级录取最低分，分物理/历史 |
| 一分一段表 | 河北省教育考试院 | PDF（扫描版） | 分数→位次映射，需 OCR |
| 学校元数据 | 阳光高考网 gaokao.chsi.com.cn | HTML/AJAX | 学校名称、所在地、层次、类型 |

## 快速开始

```bash
cd crawler

# 1. 安装依赖
pip3 install requests beautifulsoup4 openpyxl pdfplumber

# 2. 运行全流程
python3 main.py

# 或分步运行：
python3 main.py --step 1   # 仅下载原始文件
python3 main.py --step 2   # 仅解析 Excel
python3 main.py --step 3   # 仅解析 PDF（需中文 OCR）
python3 main.py --step 4   # 仅爬取阳光高考网
python3 main.py --step 5   # 仅构建 JSON
```

## 流程

```
download.py          parse_scores.py     parse_rankmap.py    crawl_schools.py
  ↓ 下载 Excel+PDF      ↓ 解析 Excel        ↓ 解析 PDF          ↓ 爬学校元数据
data_raw/*.xlsx      _parsed_scores.json  _rank_maps.json    _gaokao_schools.json
  *.pdf                                                   
                     └──────────┬─────────────┬──────────────┘
                                ↓              
                          build_output.py
                                ↓
                      public/data/*.json
```

## 产出

| 文件 | 内容 |
|------|------|
| `schools.json` | 1379 所高校索引（id, name, province, city, level, type, nature） |
| `physics-{year}.json` | 物理类分年专业分数线（minScore, minRank, major, majorCode） |
| `history-{year}.json` | 历史类分年专业分数线 |

共 11 个 JSON 文件，约 30 MB，覆盖 117,905 条专业录取记录。

## 数据字段

### schools.json
```json
{
  "schools": [
    {
      "id": "296084",           // 稳定 6 位数字 ID（基于校名哈希）
      "name": "北京大学",
      "province": "北京",
      "city": "北京",
      "level": "985/211",
      "type": "综合",
      "nature": "公办",
      "batch": "本科"
    }
  ]
}
```

### {subject}-{year}.json
```json
{
  "year": 2025,
  "subject": "physics",
  "records": [
    {
      "schoolId": "296084",     // 关联 schools.json
      "major": "计算机科学与技术",
      "majorCode": "16",        // 省编专业代号（非国标）
      "minScore": 685,          // 投档最低分
      "maxScore": null,         // 官方不发布
      "avgScore": null,         // 官方不发布
      "minRank": 120,           // 最低位次（精确或估算）
      "minRankEstimated": true, // 是否估算值
      "planNum": null,          // 官方不发布
      "remark": ""
    }
  ]
}
```

## 已知限制

1. **位次为估算值**：一分一段表为扫描版 PDF，当前未做 OCR，`minRank` 使用分数指数模型估算。精度约 ±15%。运行 `parse_rankmap.py` 前需安装中文 OCR：
   ```bash
   brew install tesseract tesseract-lang
   pip3 install pytesseract pdf2image
   ```

2. **专业代号非国标**：Excel 中的专业代号是学校内部编号（如 "16"），非教育部标准专业代码（如 "080901"）。

3. **缺少数字段**：官方 Excel 不发布 `maxScore`、`avgScore`、`planNum`，这些字段为 null。

4. **学校元数据不全**：`province`、`level`、`type` 等字段仅当阳光高考网爬取成功时才填充。

## 年度更新

每年 7-8 月河北省教育考试院发布新数据后：

```bash
# 1. 在 config.py 中添加新年份
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

# 2. 添加新文章 URL
SCORE_ARTICLES[2026] = "https://www.hebeea.edu.cn/c/2026-07-XX/XXXXXX.html"
RANK_ARTICLES[2026] = "https://www.hebeea.edu.cn/c/2026-06-XX/XXXXXX.html"

# 3. 重新运行
python3 main.py
```
