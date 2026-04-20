"""
数据清洗与结构化抽取模块
负责原始新闻数据的清洗、转换和结构化处理
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    DASHSCOPE_API_KEY, API_BASE_URL, MODEL_NAME, MAX_TOKENS, TEMPERATURE,
    RAW_NEWS_FILE, STRUCTURED_NEWS_FILE, BATCH_SIZE, PROMPTS_DIR
)


class DataProcessor:
    """数据处理类，负责数据清洗和结构化抽取"""

    def __init__(self):
        """初始化数据处理模块"""
        if not DASHSCOPE_API_KEY:
            raise ValueError("请设置DASHSCOPE_API_KEY")

        # 使用 OpenAI 兼容接口连接阿里云百炼
        self.client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=API_BASE_URL
        )
        self.extraction_prompt = self._load_prompt("extraction_prompt.txt")

    def _load_prompt(self, filename: str) -> str:
        """加载Prompt模板"""
        prompt_path = PROMPTS_DIR / filename
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_raw_news(self, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """加载原始新闻数据"""
        if file_path is None:
            file_path = RAW_NEWS_FILE

        print(f"📂 加载原始数据: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            news_list = json.load(f)

        print(f"✅ 成功加载 {len(news_list)} 条新闻")
        return news_list

    def clean_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单条新闻数据"""
        cleaned = {}

        # 清洗ID
        cleaned['id'] = news.get('id', self._generate_id(news))

        # 清洗标题
        cleaned['title'] = news.get('title', '').strip()
        if not cleaned['title']:
            raise ValueError("新闻标题不能为空")

        # 清洗内容
        cleaned['content'] = news.get('content', '').strip()
        if not cleaned['content']:
            cleaned['content'] = cleaned['title']  # 如果没有内容，使用标题

        # 清洗来源
        cleaned['source_name'] = news.get('source_name', 'Unknown').strip()
        cleaned['source_url'] = news.get('source_url', '').strip()

        # 清洗时间
        cleaned['publish_time'] = self._normalize_time(news.get('publish_time'))

        return cleaned

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

    def extract_structured_data(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM提取结构化数据"""
        # 准备Prompt
        prompt = self.extraction_prompt.format(
            title=news['title'],
            content=news['content'],
            source_name=news['source_name'],
            source_url=news['source_url'],
            publish_time=news['publish_time']
        )

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
            response_text = response.choices[0].message.content

            # 提取JSON部分（处理可能的Markdown代码块）
            json_str = self._extract_json(response_text)

            structured_data = json.loads(json_str)

            # 验证并填充缺失字段
            structured_data = self._validate_and_fill(structured_data, news)

            return structured_data

        except Exception as e:
            print(f"⚠️ 处理新闻 '{news['title'][:30]}...' 时出错: {str(e)}")
            # 返回基础结构
            return self._create_fallback_structure(news, str(e))

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