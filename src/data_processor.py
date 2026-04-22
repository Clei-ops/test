"""
数据清洗与结构化抽取模块
负责原始新闻数据的清洗、转换和结构化处理
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    DASHSCOPE_API_KEY, API_BASE_URL, MODEL_NAME, MAX_TOKENS, TEMPERATURE,
    RAW_NEWS_FILE, STRUCTURED_NEWS_FILE, BATCH_SIZE, PROMPTS_DIR
)
from src.error_handler import ErrorHandler, FallbackStrategy, DataValidator, retry, logger


class DataProcessor:
    """数据处理类，负责数据清洗和结构化抽取"""

    def __init__(self):
        """初始化数据处理模块"""
        self.client = None
        self.extraction_prompt = ""
        self._use_fallback = False

        # 验证API Key
        if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == 'your_api_key_here':
            logger.warning("⚠️ DASHSCOPE_API_KEY 未设置或无效，将使用降级模式")
            self._use_fallback = True
        elif not HAS_OPENAI:
            logger.warning("⚠️ openai库未安装，将使用降级模式")
            self._use_fallback = True
        else:
            try:
                self.client = OpenAI(
                    api_key=DASHSCOPE_API_KEY,
                    base_url=API_BASE_URL
                )
                self._use_fallback = False
                logger.info("✅ API客户端初始化成功")
            except Exception as e:
                logger.error(f"❌ API客户端初始化失败: {e}")
                self._use_fallback = True

        # 加载Prompt模板
        self.extraction_prompt = self._load_prompt("extraction_prompt.txt")
        if not self.extraction_prompt:
            logger.warning("⚠️ Prompt模板加载失败，将使用降级模式")
            self._use_fallback = True

    def _load_prompt(self, filename: str) -> str:
        """加载Prompt模板"""
        prompt_path = PROMPTS_DIR / filename
        return ErrorHandler.safe_load_text(prompt_path, default="")

    def load_raw_news(self, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """加载原始新闻数据"""
        if file_path is None:
            file_path = RAW_NEWS_FILE

        logger.info(f"📂 加载原始数据: {file_path}")

        # 使用错误处理器的安全加载
        news_list = ErrorHandler.safe_load_json(file_path, default=[])

        if not news_list:
            logger.warning(f"⚠️ 未找到有效新闻数据，请检查文件: {file_path}")
            return []

        # 过滤无效新闻
        valid_news = []
        for news in news_list:
            is_valid, error_msg = DataValidator.validate_news(news)
            if is_valid:
                valid_news.append(news)
            else:
                logger.warning(f"⚠️ 跳过无效新闻: {error_msg}")

        logger.info(f"✅ 成功加载 {len(valid_news)}/{len(news_list)} 条有效新闻")
        return valid_news

    def clean_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单条新闻数据"""
        try:
            cleaned = {}

            # 清洗ID
            cleaned['id'] = news.get('id', '') or self._generate_id(news)

            # 清洗标题
            title = DataValidator.sanitize_string(news.get('title', ''), max_length=500)
            if not title:
                title = DataValidator.sanitize_string(
                    news.get('content', '')[:100] or f"未命名新闻_{cleaned['id']}"
                )
                logger.warning(f"⚠️ 新闻标题为空，使用默认标题: {title[:30]}")
            cleaned['title'] = title

            # 清洗内容
            content = DataValidator.sanitize_string(news.get('content', ''))
            if not content:
                content = cleaned['title']
            cleaned['content'] = content[:5000]

            # 清洗来源
            cleaned['source_name'] = DataValidator.sanitize_string(
                news.get('source_name') or news.get('source', {}).get('name', 'Unknown'),
                max_length=200
            )
            cleaned['source_url'] = DataValidator.sanitize_string(
                news.get('source_url') or news.get('source', {}).get('url', ''),
                max_length=500
            )

            # 清洗时间
            cleaned['publish_time'] = self._normalize_time(
                news.get('publish_time') or news.get('publishTime')
            )

            return cleaned

        except Exception as e:
            logger.error(f"❌ 清洗新闻数据失败: {e}")
            return {
                'id': news.get('id', f"news_error_{hash(str(news)) % 10000}"),
                'title': news.get('title', '数据清洗错误'),
                'content': news.get('content', news.get('title', '')),
                'source_name': news.get('source_name', 'Unknown'),
                'source_url': news.get('source_url', ''),
                'publish_time': datetime.now().isoformat() + 'Z'
            }

    def _generate_id(self, news: Dict[str, Any]) -> str:
        """生成唯一ID"""
        content = f"{news.get('title', '')}{news.get('publish_time', '')}"
        return f"news_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    def _normalize_time(self, time_str: Optional[str]) -> str:
        """标准化时间格式"""
        if time_str is None:
            return datetime.now().isoformat() + 'Z'

        # 如果已经是ISO格式
        if 'T' in time_str:
            return time_str

        # 尝试解析其他格式
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            return dt.isoformat() + 'Z'
        except ValueError:
            try:
                dt = datetime.strptime(time_str, '%Y-%m-%d')
                return dt.isoformat() + 'Z'
            except ValueError:
                return datetime.now().isoformat() + 'Z'

    @retry(max_retries=2, delay=1.0, exceptions=(Exception,))
    def extract_structured_data(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM提取结构化数据"""
        # 检查是否需要使用降级模式
        if self._use_fallback or not self.client:
            logger.info(f"📋 使用降级模式处理: {news.get('title', 'Unknown')[:30]}...")
            return FallbackStrategy.get_default_news_structure(news)

        # 准备Prompt
        try:
            prompt = self.extraction_prompt.format(
                title=news['title'],
                content=news['content'],
                source_name=news['source_name'],
                source_url=news['source_url'],
                publish_time=news['publish_time']
            )
        except KeyError as e:
            logger.error(f"❌ Prompt模板格式错误: {e}")
            return FallbackStrategy.get_default_news_structure(news)

        try:
            # 调用阿里云百炼 API (OpenAI 兼容格式)
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )

            # 解析响应
            if not response.choices:
                raise ValueError("API返回空响应")

            response_text = response.choices[0].message.content
            if not response_text:
                raise ValueError("API返回空内容")

            # 提取JSON部分（处理可能的Markdown代码块）
            json_str = self._extract_json(response_text)

            structured_data = json.loads(json_str)

            # 验证并填充缺失字段
            structured_data = self._validate_and_fill(structured_data, news)

            return structured_data

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            return FallbackStrategy.get_default_news_structure(news)
        except Exception as e:
            logger.error(f"❌ LLM提取失败: {e}")
            return FallbackStrategy.get_default_news_structure(news)

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 尝试提取```json```代码块中的内容
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()

        # 尝试提取```代码块中的内容
        if '```' in text:
            start = text.find('```') + 3
            # 跳过可能的语言标识符
            if text[start:start+4] == 'json':
                start += 4
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()

        # 尝试直接解析整个文本
        return text.strip()

    def _validate_and_fill(self, data: Dict[str, Any], original: Dict[str, Any]) -> Dict[str, Any]:
        """验证并填充缺失字段"""
        # 确保必要字段存在
        required_fields = {
            'id': original.get('id', ''),
            'title': original.get('title', ''),
            'content': original.get('content', ''),
            'source': {
                'name': original.get('source_name', 'Unknown'),
                'url': original.get('source_url', ''),
                'type': 'media',
                'region': 'global'
            },
            'publishTime': original.get('publish_time', ''),
            'category': {
                'primary': '技术',
                'secondary': ''
            },
            'entities': {
                'companies': [],
                'products': [],
                'technologies': [],
                'people': []
            },
            'analysis': {
                'sentiment': 'neutral',
                'importance': 'medium',
                'keywords': [],
                'summary': ''
            },
            'impact': {
                'area': [],
                'level': 'company',
                'description': ''
            },
            'risk_opportunity': {
                'type': 'neutral',
                'category': '',
                'description': '',
                'affected_entities': [],
                'suggestion': ''
            }
        }

        # 合并数据
        for key, default_value in required_fields.items():
            if key not in data:
                data[key] = default_value
            elif isinstance(default_value, dict) and isinstance(data.get(key), dict):
                for sub_key, sub_default in default_value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_default

        return data

    def _create_fallback_structure(self, news: Dict[str, Any], error: str) -> Dict[str, Any]:
        """创建降级结构（当LLM失败时）"""
        return {
            'id': news.get('id', ''),
            'title': news.get('title', ''),
            'content': news.get('content', ''),
            'source': {
                'name': news.get('source_name', 'Unknown'),
                'url': news.get('source_url', ''),
                'type': 'media',
                'region': 'global'
            },
            'publishTime': news.get('publish_time', ''),
            'category': {
                'primary': '技术',
                'secondary': ''
            },
            'entities': {
                'companies': [],
                'products': [],
                'technologies': [],
                'people': []
            },
            'analysis': {
                'sentiment': 'neutral',
                'importance': 'medium',
                'keywords': [],
                'summary': f'[LLM提取失败: {error}]'
            },
            'impact': {
                'area': [],
                'level': 'company',
                'description': ''
            },
            'risk_opportunity': {
                'type': 'neutral',
                'category': '',
                'description': '',
                'affected_entities': [],
                'suggestion': ''
            },
            '_extraction_error': error
        }

    def process_all_news(self, news_list: List[Dict[str, Any]],
                         save_intermediate: bool = True) -> List[Dict[str, Any]]:
        """批量处理所有新闻"""
        structured_news = []
        total = len(news_list)

        print(f"\n🔄 开始处理 {total} 条新闻...")
        print(f"📦 批次大小: {BATCH_SIZE}")
        print(f"🤖 模型: {MODEL_NAME} (阿里云百炼)")
        print("-" * 50)

        # 分批处理
        for i in tqdm(range(0, total, BATCH_SIZE), desc="处理进度"):
            batch = news_list[i:i+BATCH_SIZE]

            for news in batch:
                try:
                    # 清洗数据
                    cleaned_news = self.clean_news(news)

                    # 结构化抽取
                    structured = self.extract_structured_data(cleaned_news)

                    structured_news.append(structured)

                except Exception as e:
                    print(f"\n❌ 处理失败: {news.get('title', 'Unknown')[:30]}...")
                    print(f"   错误: {str(e)}")
                    continue

            # 保存中间结果
            if save_intermediate and structured_news:
                self._save_intermediate(structured_news)

        print(f"\n✅ 处理完成: {len(structured_news)}/{total} 条新闻")

        return structured_news

    def _save_intermediate(self, news_list: List[Dict[str, Any]]):
        """保存中间结果"""
        with open(STRUCTURED_NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)

    def save_structured_news(self, news_list: List[Dict[str, Any]],
                             output_path: Optional[Path] = None):
        """保存结构化结果"""
        if output_path is None:
            output_path = STRUCTURED_NEWS_FILE

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)

        print(f"💾 结构化数据已保存: {output_path}")


def main():
    """数据处理器主函数"""
    processor = DataProcessor()

    # 加载原始数据
    raw_news = processor.load_raw_news()

    # 处理数据
    structured_news = processor.process_all_news(raw_news)

    # 保存结果
    processor.save_structured_news(structured_news)

    # 打印统计信息
    print("\n" + "="*50)
    print("📊 处理统计")
    print("="*50)
    print(f"原始新闻数: {len(raw_news)}")
    print(f"成功处理数: {len(structured_news)}")

    # 统计分类分布
    categories = {}
    for news in structured_news:
        primary = news.get('category', {}).get('primary', 'Unknown')
        categories[primary] = categories.get(primary, 0) + 1

    print("\n分类分布:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count}条")

    # 统计重要性分布
    importance_dist = {}
    for news in structured_news:
        imp = news.get('analysis', {}).get('importance', 'Unknown')
        importance_dist[imp] = importance_dist.get(imp, 0) + 1

    print("\n重要性分布:")
    for imp, count in sorted(importance_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {imp}: {count}条")


if __name__ == "__main__":
    main()