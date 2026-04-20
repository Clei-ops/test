"""
分析器模块
负责热点识别、趋势分析和数据统计
"""

import json
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import STRUCTURED_NEWS_FILE


class NewsAnalyzer:
    """新闻分析器，负责热点识别和趋势分析"""

    def __init__(self, news_list: List[Dict[str, Any]] = None):
        """初始化分析器"""
        self.news_list = news_list or []

    def load_structured_news(self, file_path: Path = None) -> List[Dict[str, Any]]:
        """加载结构化新闻数据"""
        if file_path is None:
            file_path = STRUCTURED_NEWS_FILE

        print(f"📂 加载结构化数据: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            self.news_list = json.load(f)

        print(f"✅ 成功加载 {len(self.news_list)} 条新闻")
        return self.news_list

    def get_overall_statistics(self) -> Dict[str, Any]:
        """获取整体统计信息"""
        if not self.news_list:
            return {}

        # 来源统计
        sources = Counter()
        source_types = Counter()
        regions = Counter()

        for news in self.news_list:
            source = news.get('source', {})
            sources[source.get('name', 'Unknown')] += 1
            source_types[source.get('type', 'Unknown')] += 1
            regions[source.get('region', 'Unknown')] += 1

        # 时间统计
        dates = []
        for news in self.news_list:
            try:
                time_str = news.get('publishTime', '')
                if time_str:
                    # 提取日期部分
                    date = time_str.split('T')[0]
                    dates.append(date)
            except Exception:
                pass

        date_distribution = Counter(dates)

        # 分类统计
        categories = Counter()
        secondary_categories = Counter()
        for news in self.news_list:
            cat = news.get('category', {})
            categories[cat.get('primary', 'Unknown')] += 1
            if cat.get('secondary'):
                secondary_categories[f"{cat.get('primary')}/{cat.get('secondary')}"] += 1

        # 情感统计
        sentiments = Counter()
        for news in self.news_list:
            sentiment = news.get('analysis', {}).get('sentiment', 'Unknown')
            sentiments[sentiment] += 1

        # 重要性统计
        importance_levels = Counter()
        for news in self.news_list:
            importance = news.get('analysis', {}).get('importance', 'Unknown')
            importance_levels[importance] += 1

        return {
            'total_count': len(self.news_list),
            'sources': dict(sources.most_common(10)),
            'source_types': dict(source_types),
            'regions': dict(regions),
            'date_distribution': dict(sorted(date_distribution.items())),
            'categories': dict(categories.most_common()),
            'secondary_categories': dict(secondary_categories.most_common(10)),
            'sentiment_distribution': dict(sentiments),
            'importance_distribution': dict(importance_levels)
        }

    def identify_hotspots(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """识别热点事件"""
        if not self.news_list:
            return []

        # 根据重要性和关键词热度评分
        scored_news = []
        for news in self.news_list:
            score = 0

            # 重要性权重
            importance = news.get('analysis', {}).get('importance', 'medium')
            importance_weights = {'high': 3, 'medium': 2, 'low': 1}
            score += importance_weights.get(importance, 1)

            # 影响级别权重
            impact_level = news.get('impact', {}).get('level', 'company')
            impact_weights = {'industry': 3, 'company': 2, 'product': 1, 'technology': 2}
            score += impact_weights.get(impact_level, 1)

            # 实体数量权重（更多实体意味着更受关注）
            entities = news.get('entities', {})
            entity_count = (
                len(entities.get('companies', [])) +
                len(entities.get('products', [])) +
                len(entities.get('technologies', []))
            )
            score += min(entity_count * 0.2, 1)  # 最多加1分

            scored_news.append({
                'news': news,
                'score': score
            })

        # 按分数排序
        scored_news.sort(key=lambda x: x['score'], reverse=True)

        # 返回Top N热点
        hotspots = []
        for item in scored_news[:top_n]:
            news = item['news']
            hotspots.append({
                'id': news.get('id'),
                'title': news.get('title'),
                'summary': news.get('analysis', {}).get('summary', ''),
                'score': item['score'],
                'importance': news.get('analysis', {}).get('importance'),
                'impact_level': news.get('impact', {}).get('level'),
                'key_entities': {
                    'companies': news.get('entities', {}).get('companies', [])[:3],
                    'products': news.get('entities', {}).get('products', [])[:3]
                },
                'category': news.get('category', {}).get('primary'),
                'publish_time': news.get('publishTime', '')
            })

        return hotspots

    def analyze_entities(self) -> Dict[str, Any]:
        """分析实体热度"""
        companies = Counter()
        products = Counter()
        technologies = Counter()
        people = Counter()

        for news in self.news_list:
            entities = news.get('entities', {})

            # 统计公司（根据重要性加权）
            importance = news.get('analysis', {}).get('importance', 'medium')
            weight = {'high': 3, 'medium': 2, 'low': 1}.get(importance, 1)

            for company in entities.get('companies', []):
                companies[company] += weight

            for product in entities.get('products', []):
                products[product] += weight

            for tech in entities.get('technologies', []):
                technologies[tech] += weight

            for person in entities.get('people', []):
                people[person] += weight

        return {
            'top_companies': dict(companies.most_common(10)),
            'top_products': dict(products.most_common(10)),
            'top_technologies': dict(technologies.most_common(10)),
            'top_people': dict(people.most_common(5))
        }

    def analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        # 按分类分析趋势
        category_trends = defaultdict(list)
        for news in self.news_list:
            primary_cat = news.get('category', {}).get('primary', 'Unknown')
            date = news.get('publishTime', '').split('T')[0] if news.get('publishTime') else 'Unknown'
            category_trends[primary_cat].append(date)

        # 计算技术关键词趋势
        tech_evolution = []
        tech_timeline = defaultdict(set)
        for news in self.news_list:
            date = news.get('publishTime', '').split('T')[0] if news.get('publishTime') else 'Unknown'
            for tech in news.get('entities', {}).get('technologies', []):
                tech_timeline[tech].add(date)

        # 找出最早出现和最近出现的技术
        for tech, dates in tech_timeline.items():
            if len(dates) >= 1:
                sorted_dates = sorted(dates)
                tech_evolution.append({
                    'technology': tech,
                    'first_seen': sorted_dates[0],
                    'last_seen': sorted_dates[-1],
                    'frequency': len(dates)
                })

        tech_evolution.sort(key=lambda x: x['frequency'], reverse=True)

        # 公司活跃度趋势
        company_activities = defaultdict(list)
        for news in self.news_list:
            date = news.get('publishTime', '').split('T')[0] if news.get('publishTime') else 'Unknown'
            for company in news.get('entities', {}).get('companies', []):
                company_activities[company].append(date)

        company_trends = []
        for company, dates in company_activities.items():
            company_trends.append({
                'company': company,
                'activity_count': len(dates),
                'dates': sorted(dates)
            })
        company_trends.sort(key=lambda x: x['activity_count'], reverse=True)

        return {
            'category_trends': {k: dict(Counter(v)) for k, v in category_trends.items()},
            'tech_evolution': tech_evolution[:10],
            'company_activity_trends': company_trends[:10]
        }

    def analyze_sentiment(self) -> Dict[str, Any]:
        """分析情感分布"""
        sentiment_by_category = defaultdict(lambda: Counter())
        sentiment_by_company = defaultdict(lambda: Counter())

        for news in self.news_list:
            sentiment = news.get('analysis', {}).get('sentiment', 'neutral')
            category = news.get('category', {}).get('primary', 'Unknown')

            # 按分类统计情感
            sentiment_by_category[category][sentiment] += 1

            # 按公司统计情感
            for company in news.get('entities', {}).get('companies', []):
                sentiment_by_company[company][sentiment] += 1

        # 计算各公司的情感得分
        company_sentiment_scores = {}
        for company, sentiment_counter in sentiment_by_company.items():
            total = sum(sentiment_counter.values())
            if total > 0:
                score = (
                    sentiment_counter.get('positive', 0) * 1 +
                    sentiment_counter.get('neutral', 0) * 0 +
                    sentiment_counter.get('negative', 0) * -1
                ) / total
                company_sentiment_scores[company] = {
                    'score': round(score, 2),
                    'distribution': dict(sentiment_counter)
                }

        return {
            'sentiment_by_category': {k: dict(v) for k, v in sentiment_by_category.items()},
            'company_sentiment_scores': dict(sorted(
                company_sentiment_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )[:10])
        }

    def analyze_risk_opportunity(self) -> Dict[str, Any]:
        """分析风险与机会"""
        risks = []
        opportunities = []
        risk_by_category = Counter()
        opportunity_by_category = Counter()
        affected_entities_risk = Counter()
        affected_entities_opportunity = Counter()

        for news in self.news_list:
            ro = news.get('risk_opportunity', {})
            ro_type = ro.get('type', 'neutral')
            ro_category = ro.get('category', '')
            ro_description = ro.get('description', '')
            ro_entities = ro.get('affected_entities', [])
            ro_suggestion = ro.get('suggestion', '')
            importance = news.get('analysis', {}).get('importance', 'medium')

            item = {
                'title': news.get('title', ''),
                'category': ro_category,
                'description': ro_description,
                'affected_entities': ro_entities,
                'suggestion': ro_suggestion,
                'importance': importance,
                'type': ro_type
            }

            if ro_type == 'risk':
                risks.append(item)
                if ro_category:
                    risk_by_category[ro_category] += 1
                for entity in ro_entities:
                    affected_entities_risk[entity] += 1
            elif ro_type == 'opportunity':
                opportunities.append(item)
                if ro_category:
                    opportunity_by_category[ro_category] += 1
                for entity in ro_entities:
                    affected_entities_opportunity[entity] += 1

        # 按重要性排序
        importance_order = {'high': 0, 'medium': 1, 'low': 2}
        risks.sort(key=lambda x: importance_order.get(x.get('importance', 'medium'), 1))
        opportunities.sort(key=lambda x: importance_order.get(x.get('importance', 'medium'), 1))

        return {
            'risks': risks[:10],  # Top 10 风险
            'opportunities': opportunities[:10],  # Top 10 机会
            'risk_by_category': dict(risk_by_category.most_common(10)),
            'opportunity_by_category': dict(opportunity_by_category.most_common(10)),
            'affected_entities_risk': dict(affected_entities_risk.most_common(10)),
            'affected_entities_opportunity': dict(affected_entities_opportunity.most_common(10)),
            'risk_count': len(risks),
            'opportunity_count': len(opportunities)
        }

    def generate_analysis_report(self) -> Dict[str, Any]:
        """生成完整分析报告"""
        print("\n🔍 开始数据分析...")

        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_overall_statistics(),
            'hotspots': self.identify_hotspots(),
            'entities': self.analyze_entities(),
            'trends': self.analyze_trends(),
            'sentiment_analysis': self.analyze_sentiment(),
            'risk_opportunity': self.analyze_risk_opportunity()
        }

        print("✅ 分析完成")
        return report


def main():
    """分析器主函数"""
    analyzer = NewsAnalyzer()

    # 加载数据
    analyzer.load_structured_news()

    # 生成分析报告
    report = analyzer.generate_analysis_report()

    # 打印关键信息
    print("\n" + "="*50)
    print("📊 分析报告摘要")
    print("="*50)

    print(f"\n📈 整体统计:")
    stats = report['statistics']
    print(f"  新闻总数: {stats['total_count']}")
    print(f"  来源分布: {stats['sources']}")
    print(f"  分类分布: {stats['categories']}")

    print(f"\n🔥 热点事件 Top 5:")
    for i, hotspot in enumerate(report['hotspots'], 1):
        print(f"  {i}. {hotspot['title'][:40]}...")
        print(f"     重要性: {hotspot['importance']}, 评分: {hotspot['score']}")

    print(f"\n🏢 活跃公司 Top 5:")
    for i, (company, count) in enumerate(list(report['entities']['top_companies'].items())[:5], 1):
        print(f"  {i}. {company}: {count}次提及")

    print(f"\n💻 热门技术 Top 5:")
    for i, (tech, count) in enumerate(list(report['entities']['top_technologies'].items())[:5], 1):
        print(f"  {i}. {tech}: {count}次提及")

    # 保存报告
    output_path = Path(__file__).parent.parent / 'output' / 'analysis_report.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 分析报告已保存: {output_path}")


if __name__ == "__main__":
    main()