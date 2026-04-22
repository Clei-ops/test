"""
错误处理工具模块
提供统一的错误处理、日志记录和降级策略
"""

import json
import logging
import traceback
from typing import Any, Callable, Optional, TypeVar, Dict
from functools import wraps
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_news_analyzer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorHandler:
    """错误处理器类"""

    @staticmethod
    def safe_load_json(file_path: Path, default: Any = None) -> Any:
        """安全加载JSON文件"""
        try:
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return default if default is not None else []

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"成功加载文件: {file_path}")
                return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误 {file_path}: {e}")
            return default if default is not None else []
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
            return default if default is not None else []

    @staticmethod
    def safe_save_json(file_path: Path, data: Any) -> bool:
        """安全保存JSON文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def safe_load_text(file_path: Path, default: str = "") -> str:
        """安全加载文本文件"""
        try:
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return default

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
            return default

    @staticmethod
    def safe_save_text(file_path: Path, content: str) -> bool:
        """安全保存文本文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"成功保存文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def safe_get(data: dict, *keys, default=None):
        """安全获取嵌套字典中的值"""
        try:
            result = data
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key, default)
                else:
                    return default
            return result
        except Exception:
            return default


def retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """重试装饰器"""
    import time

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"函数 {func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"函数 {func.__name__} 执行失败，已达最大重试次数: {e}")
            raise last_exception
        return wrapper
    return decorator


def handle_errors(default_return=None, log_traceback: bool = True):
    """错误处理装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_traceback:
                    logger.error(f"函数 {func.__name__} 发生错误: {e}\n{traceback.format_exc()}")
                else:
                    logger.error(f"函数 {func.__name__} 发生错误: {e}")
                return default_return
        return wrapper
    return decorator


class FallbackStrategy:
    """降级策略类"""

    @staticmethod
    def get_default_news_structure(news: dict) -> dict:
        """获取默认的新闻结构（LLM失败时的降级结构）"""
        return {
            'id': news.get('id', f"news_{hash(str(news)) % 1000000}"),
            'title': news.get('title', '无标题'),
            'content': news.get('content', news.get('title', '')),
            'source': {
                'name': news.get('source_name', news.get('source', {}).get('name', 'Unknown')),
                'url': news.get('source_url', news.get('source', {}).get('url', '')),
                'type': 'media',
                'region': 'global'
            },
            'publishTime': news.get('publish_time', news.get('publishTime', '')),
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
                'summary': news.get('content', '')[:200] if news.get('content') else ''
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
            '_fallback': True
        }

    @staticmethod
    def get_default_analysis_report() -> dict:
        """获取默认的分析报告结构"""
        return {
            'generated_at': '',
            'statistics': {
                'total_count': 0,
                'sources': {},
                'categories': {},
                'sentiment_distribution': {},
                'importance_distribution': {}
            },
            'hotspots': [],
            'entities': {
                'top_companies': {},
                'top_products': {},
                'top_technologies': {},
                'top_people': {}
            },
            'trends': {
                'category_trends': {},
                'tech_evolution': [],
                'company_activity_trends': []
            },
            'sentiment_analysis': {
                'sentiment_by_category': {},
                'company_sentiment_scores': {}
            },
            'risk_opportunity': {
                'risks': [],
                'opportunities': [],
                'risk_by_category': {},
                'opportunity_by_category': {},
                'affected_entities_risk': {},
                'affected_entities_opportunity': {},
                'risk_count': 0,
                'opportunity_count': 0
            }
        }


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_news(news: dict) -> tuple:
        """验证新闻数据是否有效"""
        if not news:
            return False, "新闻数据为空"

        if not news.get('title'):
            return False, "新闻标题为空"

        return True, None

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """清理字符串"""
        if not text:
            return ""
        text = ''.join(char for char in str(text) if ord(char) >= 32 or char in '\n\t')
        return text[:max_length].strip()

    @staticmethod
    def ensure_list(value: Any) -> list:
        """确保返回列表"""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (str, int, float, bool)):
            return [value]
        try:
            return list(value)
        except Exception:
            return []