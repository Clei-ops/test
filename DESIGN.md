# AI舆情分析日报系统 - 设计文档

## 一、项目设计思路

### 1.1 核心理念

本项目的设计遵循 **"清晰分层、职责单一、渐进增强"** 的原则：

```
┌─────────────────────────────────────────────────────────────────┐
│                        设计核心理念                               │
├─────────────────────────────────────────────────────────────────┤
│  清晰分层   │  数据层 → 处理层 → 分析层 → 展示层                  │
│  职责单一   │  每个模块只做一件事，便于测试和维护                   │
│  渐进增强   │  支持LLM调用失败时的降级方案                          │
│  配置分离   │  API Key、模型参数等配置与代码分离                     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 架构设计原则

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **模块化** | 各功能模块独立，低耦合 | `data_processor`、`analyzer`、`report_generator`、`visualizer` 分离 |
| **可配置** | 关键参数可配置，不硬编码 | `config.py` 集中管理配置 |
| **可扩展** | 易于添加新数据源、新分析维度 | Schema设计预留扩展字段 |
| **容错性** | LLM调用失败时有降级方案 | `_create_fallback_structure` 方法 |
| **可观测** | 处理进度可视化，便于调试 | `tqdm` 进度条 + 日志输出 |

### 1.3 数据流设计

```
原始数据流程图：

┌──────────────┐
│ raw_news.json│  ← 手动收集/爬虫获取
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ DataProcessor    │  ← 数据清洗 + LLM结构化抽取
│  - clean_news()  │     • 去重、格式化时间
│  - extract()     │     • 实体识别、情感分析
└──────┬───────────┘     • 分类、重要性评估
       │
       ▼
┌────────────────────┐
│ structured_news.json│  ← 标准化JSON输出
└─────────┬──────────┘
          │
          ▼
┌──────────────────┐
│ NewsAnalyzer     │  ← 统计分析 + 热点识别
│  - statistics    │     • 分类/情感/来源分布
│  - hotspots      │     • 实体热度排名
│  - trends        │     • 趋势分析
└──────┬───────────┘
          │
          ▼
┌────────────────────┐
│ analysis_report.json│  ← 分析结果JSON
└─────────┬──────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌─────────┐ ┌─────────────┐
│ Report  │ │ Visualizer  │
│Generator│ │             │
└────┬────┘ └──────┬──────┘
     │             │
     ▼             ▼
┌──────────┐ ┌───────────────┐
│daily_    │ │visualization  │
│report.md │ │.html          │
└──────────┘ └───────────────┘
```

---

## 二、项目架构

### 2.1 目录结构

```
ai-news-analyzer/
├── README.md                    # 项目说明文档
├── DESIGN.md                    # 本设计文档
├── requirements.txt             # Python依赖
├── config.py                    # 集中配置文件
├── main.py                      # 主程序入口
├── .gitignore                   # Git忽略文件
│
├── data/                        # 数据层
│   ├── raw_news.json            # 原始新闻数据（输入）
│   ├── structured_news.json     # 结构化数据（中间产物）
│   └── data_source.md           # 数据来源说明
│
├── src/                         # 处理层
│   ├── __init__.py
│   ├── data_processor.py        # 数据清洗 + 结构化抽取
│   ├── analyzer.py              # 分析器（热点、趋势、实体）
│   ├── report_generator.py      # Markdown报告生成
│   └── visualizer.py            # HTML可视化生成
│
├── output/                      # 输出层
│   ├── daily_report.md          # 每日分析报告
│   ├── visualization.html       # 可视化页面（集成报告）
│   └── analysis_report.json     # 分析数据
│
└── prompts/                     # Prompt工程
    ├── extraction_prompt.txt    # 结构化抽取Prompt
    └── analysis_prompt.txt      # 分析Prompt
```

### 2.2 模块职责

#### 🔹 `config.py` - 配置中心

```python
# 配置内容
├── 路径配置    # 数据目录、输出目录、Prompt目录
├── API配置     # 阿里云百炼 API Key、Base URL、模型名称
├── 模型参数    # MAX_TOKENS、TEMPERATURE
├── 处理参数    # BATCH_SIZE、MAX_NEWS_PER_RUN
└── Schema枚举  # 分类、情感、重要性等枚举值
```

#### 🔹 `data_processor.py` - 数据处理器

```python
class DataProcessor:
    │
    ├── load_raw_news()          # 加载原始数据
    ├── clean_news()             # 数据清洗（去重、格式化）
    ├── extract_structured_data() # LLM结构化抽取
    ├── _validate_and_fill()     # 字段验证与填充
    ├── _create_fallback_structure() # 降级处理
    └── process_all_news()       # 批量处理主流程
```

**关键设计点：**
- 分批处理：每批5条新闻，避免API超时
- 进度可视化：`tqdm` 进度条
- 中间保存：每批处理完保存，防止数据丢失
- 降级方案：LLM失败时返回基础结构

#### 🔹 `analyzer.py` - 分析器

```python
class NewsAnalyzer:
    │
    ├── get_overall_statistics() # 整体统计
    ├── identify_hotspots()      # 热点识别
    ├── analyze_entities()       # 实体热度分析
    ├── analyze_trends()         # 趋势分析
    ├── analyze_sentiment()      # 情感分析
    └── generate_analysis_report() # 生成完整分析
```

**热点识别算法：**
```python
score = importance_weight + impact_weight + entity_count_weight
# 高重要性 +3分，行业级影响 +3分，实体数量加权
# 按分数排序取Top 5
```

#### 🔹 `report_generator.py` - 报告生成器

```python
class ReportGenerator:
    │
    ├── generate_report_with_llm()   # LLM生成（分析性强）
    ├── generate_report_with_template() # 模板生成（稳定性高）
    └── generate_report()            # 主入口（自动降级）
```

**双模式设计：**
- LLM模式：深度分析，自动洞察
- 模板模式：稳定输出，格式统一

#### 🔹 `visualizer.py` - 可视化生成器

```python
class NewsVisualizer:
    │
    ├── load_markdown_report()   # 加载MD报告
    ├── markdown_to_html()       # MD转HTML
    ├── generate_comprehensive_html() # 生成完整页面
    │   ├── 数据概览Tab          # 统计卡片 + 热点列表
    │   ├── 分析报告Tab          # Markdown渲染展示
    │   ├── 可视化图表Tab        # 6种图表
    │   └── 原始数据Tab          # 表格展示
    └── generate_visualization() # 主入口
```

**页面特点：**
- 单HTML文件，无需后端
- CSS渐变背景 + 卡片设计
- Tab切换，四个视图整合
- 响应式布局，支持移动端

#### 🔹 `main.py` - 主程序

```python
# 命令行参数支持
python main.py                      # 完整流程
python main.py --skip-extraction    # 跳过抽取
python main.py --no-llm             # 模板生成
python main.py --extraction-only    # 仅抽取
python main.py --analysis-only      # 仅分析
python main.py --report-only        # 仅报告
python main.py --visualization-only # 仅可视化

# 处理流程
Step 1: 数据清洗与结构化抽取
Step 2: 数据分析与趋势识别
Step 3: 分析报告生成
Step 4: 可视化页面生成
```

---

## 三、Schema设计思路

### 3.1 结构化数据模型

```json
{
  "id": "唯一标识",
  "title": "新闻标题",
  "content": "正文摘要",
  "source": {
    "name": "来源名称",
    "url": "原始链接",
    "type": "official/social/media/aggregate",
    "region": "cn/us/global"
  },
  "publishTime": "ISO8601时间",
  "category": {
    "primary": "技术/产品/商业/政策/研究/应用",
    "secondary": "二级分类"
  },
  "entities": {
    "companies": ["涉及公司"],
    "products": ["相关产品"],
    "technologies": ["技术标签"],
    "people": ["关键人物"]
  },
  "analysis": {
    "sentiment": "positive/negative/neutral",
    "importance": "high/medium/low",
    "keywords": ["关键词"],
    "summary": "一句话摘要(≤50字)"
  },
  "impact": {
    "area": ["影响领域"],
    "level": "industry/company/product/technology",
    "description": "影响描述"
  }
}
```

### 3.2 设计理由

| 字段 | 设计理由 |
|------|---------|
| `source.type` | 区分官方发布、社交媒体、媒体解读，影响可信度加权 |
| `source.region` | 区分中外舆情视角，便于对比分析 |
| `category.primary` | 使用枚举便于统计分析，非自由文本 |
| `entities` | 结构化实体支持聚合查询（如"OpenAI相关新闻"） |
| `analysis.sentiment` | 情感分析服务于舆情监测和风险预警 |
| `analysis.importance` | 重要性分级支持热点筛选 |
| `impact` | 影响评估是趋势判断的核心维度 |

---

## 四、技术选型

### 4.1 核心技术栈

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| **编程语言** | Python 3.11+ | 数据处理生态成熟，AI集成便利 |
| **LLM API** | 阿里云百炼 (Qwen-Plus) | 国内访问稳定，OpenAI兼容接口 |
| **HTTP客户端** | OpenAI SDK | 兼容阿里云百炼，统一接口 |
| **数据格式** | JSON + Markdown | 结构化存储 + 可读报告 |
| **可视化** | 纯HTML/CSS/JS | 无框架依赖，单文件即可运行 |
| **进度显示** | tqdm | 美观的进度条，用户体验好 |

### 4.2 为什么选择阿里云百炼？

| 对比项 | 阿里云百炼 | Anthropic Claude |
|--------|-----------|-----------------|
| 国内访问 | ✅ 稳定 | ❌ 需要代理 |
| 免费额度 | ✅ 首月100万tokens | ❌ 仅$5试用 |
| 审核速度 | ✅ 即时开通 | ⏳ 可能需要审核 |
| 接口兼容 | ✅ OpenAI格式 | ❌ 专属SDK |
| 中文支持 | ✅ 原生优化 | ✅ 支持 |

---

## 五、Prompt设计

### 5.1 结构化抽取Prompt

```
核心设计要点：
1. 明确输出Schema（JSON格式）
2. 提供抽取指南（来源类型判断、分类判断、情感分析标准）
3. 强调输出要求（严格JSON、无额外文本）
4. 提供示例（隐式或显式）

关键技巧：
- 使用枚举值约束输出格式
- 区分事实与观点（客观字段 vs 主观分析）
- 提供评判标准（如重要性评估标准）
```

### 5.2 分析报告Prompt

```
核心设计要点：
1. 输入结构化数据摘要
2. 指定分析维度（概况、热点、分类、实体、情感、趋势）
3. 要求输出格式（Markdown结构）
4. 强调分析原则（客观、洞察、系统、实用、简洁）
```

---

## 六、关键设计决策

### 6.1 为什么分批处理？

```
优点：
├── 错误隔离：单条失败不影响整体
├── 进度可见：实时显示处理进度
├── 中间保存：防止数据丢失
├── 调试友好：快速定位问题新闻
└── API限流：避免超出速率限制
```

### 6.2 为什么手动整理数据？

```
MVP阶段考虑：
├── 数据质量可控：避免爬虫清洗问题
├── 快速验证：聚焦核心分析逻辑
├── 符合要求：需求明确"不强制实现爬虫"
└── 易于演示：预设数据便于展示效果

后续扩展：
├── 接入RSS订阅
├── 爬虫自动化采集
├── 定时任务调度
└── 增量更新机制
```

### 6.3 为什么双模式报告生成？

```
LLM模式：
├── 优点：深度分析、自动洞察、语言流畅
└── 缺点：API依赖、可能失败、成本较高

模板模式：
├── 优点：稳定可靠、无API依赖、成本低
└── 缺点：分析较浅、格式固定

设计策略：
├── 优先使用LLM模式
├── 失败时自动降级到模板
└── 支持 --no-llm 强制使用模板
```

### 6.4 为什么单HTML可视化？

```
优势：
├── 无需后端服务
├── 双击即可打开
├── 便于分享和存档
├── 跨平台兼容
└── 集成Markdown报告展示

技术实现：
├── 纯CSS渐变和动画
├── JavaScript Tab切换
├── Markdown转HTML（markdown库或自定义）
└── 响应式布局
```

---

## 七、扩展方向

### 7.1 短期优化

```
├── 增加更多数据源（RSS、API接口）
├── 支持增量更新（只处理新数据）
├── 添加历史数据对比
├── 支持自定义分析维度
└── 添加邮件/钉钉推送
```

### 7.2 中期扩展

```
├── 定时任务自动运行
├── Web管理后台
├── 多语言支持
├── 图表交互增强（ECharts/Chart.js）
└── 数据导出（Excel、PDF）
```

### 7.3 长期规划

```
├── 实时舆情监控
├── 预警通知机制
├── 舆情趋势预测
├── 竞品分析模块
└── 企业知识图谱
```

---

## 八、使用指南

### 8.1 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行完整流程
python main.py

# 3. 查看结果
open output/visualization.html
```

### 8.2 配置修改

```python
# config.py 中修改
DASHSCOPE_API_KEY = "你的API Key"    # API密钥
MODEL_NAME = "qwen-plus"              # 模型选择
BATCH_SIZE = 5                        # 批次大小
TEMPERATURE = 0.3                     # 输出稳定性
```

### 8.3 数据扩展

```json
// 在 data/raw_news.json 中添加新数据
{
  "id": "news_xxx",
  "title": "新闻标题",
  "content": "新闻内容...",
  "source_name": "来源名称",
  "source_url": "https://...",
  "publish_time": "2024-01-01T00:00:00Z"
}
```

---

## 九、总结

本项目通过**清晰的三层架构**（数据层→处理层→输出层）实现了AI舆情分析的完整流程：

1. **数据层**：标准化Schema设计，支持多数据源扩展
2. **处理层**：模块化设计，LLM增强+降级方案
3. **输出层**：丰富展示，Markdown报告 + HTML可视化

核心设计亮点：
- ✅ **配置分离**：API Key、模型参数集中管理
- ✅ **双模式生成**：LLM深度分析 + 模板稳定兜底
- ✅ **单文件输出**：可视化页面自包含，无外部依赖
- ✅ **分批处理**：错误隔离、进度可视、中间保存
- ✅ **国产化适配**：阿里云百炼，国内访问稳定

---

*文档生成时间: 2024年*
*版本: v1.0.0*