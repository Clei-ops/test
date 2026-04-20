# AI舆情分析日报系统

> 从每日AI新闻中提取结构化洞察，支持趋势分析和可视化展示

## 📖 项目简介

本项目是一个AI舆情分析系统，旨在从每日AI新闻信息中提取结构化洞察，服务于：
- AI行业趋势分析
- 舆情监测与风险预警
- 信息快速理解与决策辅助

### 核心功能

✅ **数据获取** - 支持手动整理或爬虫采集（当前MVP版本使用手动数据）
✅ **结构化抽取** - 使用Claude API进行智能信息抽取
✅ **趋势分析** - 自动识别热点事件和趋势方向
✅ **报告生成** - 生成Markdown格式的分析报告
✅ **可视化展示** - 生成交互式HTML图表

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI舆情分析日报系统                            │
├─────────────────────────────────────────────────────────────────┤
│  数据获取层         │  数据处理层       │  分析输出层            │
│  ──────────         │  ──────────       │  ──────────            │
│  - 新闻数据源       │  - 数据清洗       │  - 结构化结果(JSON)    │
│    (TechCrunch)     │  - Schema抽取     │  - 分析报告(Markdown)  │
│    (机器之心)        │  - 实体识别       │  - 可视化图表(HTML)    │
│    (Hacker News)    │  - 情感分析       │                        │
│    (arXiv)          │  - 重要性评估     │                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
ai-news-analyzer/
├── README.md                    # 本文档
├── requirements.txt             # Python依赖
├── config.py                    # 配置文件
├── main.py                      # 主程序入口
│
├── data/
│   ├── raw_news.json            # 原始新闻数据
│   ├── structured_news.json     # 结构化结果
│   └── data_source.md           # 数据来源说明
│
├── src/
│   ├── __init__.py
│   ├── data_processor.py        # 数据清洗与结构化抽取
│   ├── analyzer.py              # 分析器（热点、趋势）
│   ├── report_generator.py      # 报告生成器
│   └── visualizer.py            # 可视化模块
│
├── output/
│   ├── daily_report.md          # 每日分析报告
│   └── visualization.html       # 可视化页面
│
└── prompts/
    ├── extraction_prompt.txt    # 结构化抽取Prompt
    └── analysis_prompt.txt      # 分析Prompt
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Anthropic API Key（用于Claude调用）

### 2. 安装依赖

```bash
cd ai-news-analyzer
pip install -r requirements.txt
```

### 3. 配置API Key

```bash
export ANTHROPIC_API_KEY='your_api_key_here'
```

### 4. 运行完整流程

```bash
python main.py
```

### 5. 查看结果

- **可视化图表**: 在浏览器中打开 `output/visualization.html`
- **分析报告**: 使用Markdown阅读器查看 `output/daily_report.md`
- **结构化数据**: 查看 `data/structured_news.json`

---

## 💡 详细使用说明

### 命令行参数

```bash
# 运行完整流程（默认）
python main.py

# 跳过数据抽取，使用已有结构化数据
python main.py --skip-extraction

# 仅运行数据抽取
python main.py --extraction-only

# 仅运行数据分析
python main.py --analysis-only

# 仅生成报告（使用模板，不调用LLM）
python main.py --report-only --no-llm

# 仅生成可视化
python main.py --visualization-only
```

### 处理流程说明

```
原始数据(raw_news.json)
    │
    ▼
┌─────────────────┐
│ Step 1: 数据清洗 │  - 去重、格式化时间、统一编码
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 2: 结构化抽取│  - 按Schema提取实体、分类、情感
└────────┬────────┘         (分批处理，每条新闻单独处理)
         │
         ▼
┌─────────────────┐
│ Step 3: 重要性评估│  - 综合来源、内容、实体计算重要性
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 4: 趋势分析 │  - 汇总分类、聚合实体、识别热点
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Step 5: 报告生成 │  - 生成结构化JSON + 分析报告MD + 可视化HTML
└─────────────────┘
```

---

## 📊 数据Schema设计

### 结构化数据模型

```json
{
  "id": "string - 唯一标识",
  "title": "string - 新闻标题",
  "content": "string - 正文内容或摘要",
  "source": {
    "name": "string - 来源名称",
    "url": "string - 原始链接",
    "type": "enum - official/social/media/aggregate",
    "region": "string - cn/us/global"
  },
  "publishTime": "ISO8601 - 发布时间",
  "category": {
    "primary": "enum - 技术/产品/商业/政策/研究/应用",
    "secondary": "string - 二级分类"
  },
  "entities": {
    "companies": ["涉及公司列表"],
    "products": ["相关产品列表"],
    "technologies": ["相关技术标签"],
    "people": ["关键人物"]
  },
  "analysis": {
    "sentiment": "enum - positive/negative/neutral",
    "importance": "enum - high/medium/low",
    "keywords": ["关键词列表"],
    "summary": "string - 一句话摘要(≤50字)"
  },
  "impact": {
    "area": ["影响领域列表"],
    "level": "enum - industry/company/product/technology",
    "description": "string - 影响描述"
  }
}
```

### Schema设计理由

| 字段 | 设计理由 |
|------|---------|
| `source.type` | 区分官方发布、社交媒体讨论、媒体解读，影响可信度权重 |
| `source.region` | 区分中外舆情视角，便于对比分析 |
| `category.primary` | 使用枚举值便于统计分析 |
| `entities` | 结构化实体信息支持聚合查询（如"OpenAI相关新闻"） |
| `analysis.sentiment` | 情感分析服务于舆情监测和风险预警 |
| `analysis.importance` | 重要性分级支持热点筛选 |
| `impact` | 影响评估是趋势判断的核心维度 |

---

## 📈 示例输出

### 可视化图表示例

系统生成的可视化页面包含：
- 📊 **分类分布饼图** - 新闻主分类占比
- 💭 **情感分布柱状图** - 正面/中性/负面情感统计
- 🎯 **重要性分布** - 高/中/低重要性新闻分布
- 🏢 **公司活跃度TOP10** - 最受关注的公司
- 💻 **技术热度TOP10** - 最热门的技术关键词
- 📰 **新闻来源分布** - 各数据源贡献度
- 📅 **时间趋势图** - 新闻发布时间分布

### 分析报告示例

生成的Markdown报告包含：
- 整体概况统计
- 热点事件Top5
- 实体分析（公司/产品/技术）
- 情感与影响分析
- 趋势洞察
- 关键摘要

---

## 🎯 核心设计决策

### 1. 为什么采用分批处理？

- **体现处理逻辑** - 可追踪每条新闻的处理情况
- **错误隔离** - 单条失败不影响整体流程
- **便于调试** - 可快速定位问题新闻

### 2. 为什么手动整理数据？

- **符合MVP原则** - 聚焦核心分析逻辑
- **数据质量可控** - 避免爬虫清洗问题
- **快速验证** - 节省开发时间

### 3. 为什么使用Claude API？

- **结构化抽取能力强** - 支持复杂Schema输出
- **多语言支持** - 中英文混合内容处理
- **可控输出** - 可指定JSON Schema格式

---

## 🔧 扩展与定制

### 添加新的数据源

1. 在 `data/raw_news.json` 中添加新闻数据
2. 更新 `data/data_source.md` 说明新来源
3. 重新运行处理流程

### 自定义分析维度

1. 修改 `src/analyzer.py` 添加新的分析方法
2. 更新 `prompts/extraction_prompt.txt` 调整抽取字段
3. 在 `src/report_generator.py` 添加报告章节

### 调整可视化图表

1. 修改 `src/visualizer.py` 添加新图表
2. 支持两种模式：
   - 使用 `pyecharts` 生成交互式图表
   - 使用HTML模板生成静态图表（无依赖）

---

## 📝 数据来源

当前示例数据来源于：
- **Hacker News** - 技术社区热点
- **机器之心** - 国内AI专业媒体
- **TechCrunch** - 国际科技媒体
- **arXiv** - 学术研究论文

详见 `data/data_source.md`

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Anthropic Claude](https://www.anthropic.com/) - 强大的结构化抽取能力
- [pyecharts](https://github.com/pyecharts/pyecharts) - 精美的Python可视化库

---

**生成时间**: 2024年

**版本**: v1.0.0
