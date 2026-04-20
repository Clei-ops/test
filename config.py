"""
AI舆情分析日报系统配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# 数据文件路径
RAW_NEWS_FILE = DATA_DIR / "raw_news.json"
STRUCTURED_NEWS_FILE = DATA_DIR / "structured_news.json"

# 输出文件路径
DAILY_REPORT_FILE = OUTPUT_DIR / "daily_report.md"
VISUALIZATION_FILE = OUTPUT_DIR / "visualization.html"

# ============================================
# 阿里云百炼 API 配置
# ============================================
# API Key (直接配置或通过环境变量)
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-687f4676396e48818cfd34ef974bab64")

# API 基础 URL (阿里云百炼 OpenAI 兼容接口)
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 模型配置
MODEL_NAME = "qwen-plus"  # 可选: qwen-turbo (更快更便宜), qwen-max (更强)
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # 低温度确保稳定输出

# ============================================

# 处理配置
BATCH_SIZE = 5  # 每批处理新闻数量
MAX_NEWS_PER_RUN = 50  # 最大处理新闻数

# Schema枚举值
SOURCE_TYPES = ["official", "social", "media", "aggregate"]
REGIONS = ["cn", "us", "global"]
CATEGORIES = ["技术", "产品", "商业", "政策", "研究", "应用"]
SENTIMENTS = ["positive", "negative", "neutral"]
IMPORTANCE_LEVELS = ["high", "medium", "low"]
IMPACT_LEVELS = ["industry", "company", "product", "technology"]

# 风险与机会类型
RISK_TYPES = ["regulatory_risk", "competitive_risk", "technical_risk", "market_risk"]
OPPORTUNITY_TYPES = ["investment_opportunity", "business_opportunity", "partnership_opportunity", "technology_opportunity"]
RISK_OPPORTUNITY_TYPES = ["risk", "opportunity", "neutral"]