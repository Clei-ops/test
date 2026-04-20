"""
报告生成模块
负责生成Markdown格式的分析报告
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    STRUCTURED_NEWS_FILE, DAILY_REPORT_FILE, OUTPUT_DIR, PROMPTS_DIR,
    DASHSCOPE_API_KEY, API_BASE_URL, MODEL_NAME, MAX_TOKENS, TEMPERATURE
)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ReportGenerator:
    """报告生成器"""

    def __init__(self, use_llm: bool = True):
        """初始化报告生成器

        Args:
            use_llm: 是否使用LLM生成报告（如果False，将使用模板生成）
        """
        self.use_llm = use_llm and HAS_OPENAI and DASHSCOPE_API_KEY
        if self.use_llm:
            self.client = OpenAI(
                api_key=DASHSCOPE_API_KEY,
                base_url=API_BASE_URL
            )
            self.analysis_prompt = self._load_prompt("analysis_prompt.txt")

    def _load_prompt(self, filename: str) -> str:
        """加载Prompt模板"""
        prompt_path = PROMPTS_DIR / filename
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_data(self) -> List[Dict[str, Any]]:
        """加载结构化数据"""
        with open(STRUCTURED_NEWS_FILE, 'r', encoding='utf-8') as f:
            news_list = json.load(f)
        return news_list

    def generate_report_with_llm(self, news_list: List[Dict[str, Any]],
                                  analysis_data: Dict[str, Any]) -> str:
        """使用LLM生成报告"""
        # 准备Prompt
        news_summary = []
        for i, news in enumerate(news_list[:20], 1):  # 限制数量避免超长
            news_summary.append(f"""
{i}. {news.get('title', 'N/A')}
   - 来源: {news.get('source', {}).get('name', 'Unknown')}
   - 分类: {news.get('category', {}).get('primary', 'N/A')}
   - 情感: {news.get('analysis', {}).get('sentiment', 'neutral')}
   - 重要性: {news.get('analysis', {}).get('importance', 'medium')}
   - 摘要: {news.get('analysis', {}).get('summary', 'N/A')}
   - 公司: {', '.join(news.get('entities', {}).get('companies', [])[:3]) or 'N/A'}
   - 技术: {', '.join(news.get('entities', {}).get('technologies', [])[:3]) or 'N/A'}
""")

        prompt = self.analysis_prompt.format(
            structured_news='\n'.join(news_summary)
        )

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS * 2  # 报告需要更多token
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"⚠️ LLM生成报告失败: {str(e)}")
            print("📝 使用模板生成报告...")
            return self.generate_report_with_template(news_list, analysis_data)

    def generate_report_with_template(self, news_list: List[Dict[str, Any]],
                                       analysis_data: Dict[str, Any]) -> str:
        """使用模板生成报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        stats = analysis_data.get('statistics', {})
        hotspots = analysis_data.get('hotspots', [])
        entities = analysis_data.get('entities', {})
        sentiment = analysis_data.get('sentiment_analysis', {})

        report_lines = []

        # 标题
        report_lines.append(f"# AI舆情分析日报 - {today}")
        report_lines.append("")
        report_lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"> 数据源: {len(news_list)} 条新闻")
        report_lines.append("")

        # 整体概况
        report_lines.append("## 📊 整体概况")
        report_lines.append("")
        report_lines.append(f"本日采集AI领域新闻 **{stats.get('total_count', 0)}** 条。")
        report_lines.append("")

        # 来源分布
        report_lines.append("### 新闻来源分布")
        report_lines.append("")
        sources = stats.get('sources', {})
        for source, count in list(sources.items())[:5]:
            report_lines.append(f"- {source}: {count}条")
        report_lines.append("")

        # 分类分布
        report_lines.append("### 分类分布")
        report_lines.append("")
        categories = stats.get('categories', {})
        for cat, count in categories.items():
            percentage = (count / stats.get('total_count', 1) * 100)
            report_lines.append(f"- {cat}: {count}条 ({percentage:.1f}%)")
        report_lines.append("")

        # 热点事件
        report_lines.append("## 🔥 今日热点")
        report_lines.append("")

        for i, hotspot in enumerate(hotspots, 1):
            report_lines.append(f"### {i}. {hotspot.get('title', 'N/A')}")
            report_lines.append("")
            report_lines.append(f"- **重要性**: {hotspot.get('importance', 'Unknown')}")
            report_lines.append(f"- **影响级别**: {hotspot.get('impact_level', 'Unknown')}")
            report_lines.append(f"- **分类**: {hotspot.get('category', 'Unknown')}")
            report_lines.append(f"- **摘要**: {hotspot.get('summary', 'N/A')}")
            companies = hotspot.get('key_entities', {}).get('companies', [])
            if companies:
                report_lines.append(f"- **相关公司**: {', '.join(companies)}")
            report_lines.append("")

        # 实体分析
        report_lines.append("## 🏢 实体分析")
        report_lines.append("")

        # 活跃公司
        report_lines.append("### 活跃公司 TOP 10")
        report_lines.append("")
        report_lines.append("| 排名 | 公司 | 提及次数 |")
        report_lines.append("|:----:|:-----|:--------:|")
        for i, (company, count) in enumerate(list(entities.get('top_companies', {}).items())[:10], 1):
            report_lines.append(f"| {i} | {company} | {count} |")
        report_lines.append("")

        # 热门技术
        report_lines.append("### 热门技术 TOP 10")
        report_lines.append("")
        report_lines.append("| 排名 | 技术 | 提及次数 |")
        report_lines.append("|:----:|:-----|:--------:|")
        for i, (tech, count) in enumerate(list(entities.get('top_technologies', {}).items())[:10], 1):
            report_lines.append(f"| {i} | {tech} | {count} |")
        report_lines.append("")

        # 热门产品
        products = entities.get('top_products', {})
        if products:
            report_lines.append("### 热门产品 TOP 5")
            report_lines.append("")
            for product, count in list(products.items())[:5]:
                report_lines.append(f"- {product}: {count}次提及")
            report_lines.append("")

        # 情感分析
        report_lines.append("## 💭 情感与影响分析")
        report_lines.append("")

        # 整体情感分布
        sentiment_dist = stats.get('sentiment_distribution', {})
        total_sentiment = sum(sentiment_dist.values())
        report_lines.append("### 整体情感分布")
        report_lines.append("")
        for s, count in sentiment_dist.items():
            emoji = {'positive': '😊', 'negative': '😟', 'neutral': '😐'}.get(s, '❓')
            percentage = (count / total_sentiment * 100) if total_sentiment > 0 else 0
            report_lines.append(f"- {emoji} {s}: {count}条 ({percentage:.1f}%)")
        report_lines.append("")

        # 公司情感得分
        company_sentiment = sentiment.get('company_sentiment_scores', {})
        if company_sentiment:
            report_lines.append("### 公司情感指数 TOP 5")
            report_lines.append("")
            report_lines.append("| 公司 | 情感得分 | 正面 | 中性 | 负面 |")
            report_lines.append("|:-----|:--------:|:----:|:----:|:----:|")
            for company, data in list(company_sentiment.items())[:5]:
                dist = data.get('distribution', {})
                report_lines.append(
                    f"| {company} | {data.get('score', 0)} | "
                    f"{dist.get('positive', 0)} | {dist.get('neutral', 0)} | {dist.get('negative', 0)} |"
                )
            report_lines.append("")

        # 趋势洞察
        report_lines.append("## 🔮 趋势洞察")
        report_lines.append("")

        # 技术趋势
        tech_evolution = analysis_data.get('trends', {}).get('tech_evolution', [])
        if tech_evolution:
            report_lines.append("### 技术热度趋势")
            report_lines.append("")
            for tech_info in tech_evolution[:5]:
                tech = tech_info.get('technology', 'Unknown')
                freq = tech_info.get('frequency', 0)
                report_lines.append(f"- **{tech}** - 出现{freq}次")
            report_lines.append("")

        # 公司活跃度
        company_trends = analysis_data.get('trends', {}).get('company_activity_trends', [])
        if company_trends:
            report_lines.append("### 公司活跃度")
            report_lines.append("")
            for company_info in company_trends[:5]:
                company = company_info.get('company', 'Unknown')
                count = company_info.get('activity_count', 0)
                report_lines.append(f"- **{company}** - {count}次动态")
            report_lines.append("")

        # 风险与机会分析
        risk_opportunity = analysis_data.get('risk_opportunity', {})
        risks = risk_opportunity.get('risks', [])
        opportunities = risk_opportunity.get('opportunities', [])

        if risks or opportunities:
            report_lines.append("## ⚠️ 风险与机会提示")
            report_lines.append("")

            # 风险提示
            if risks:
                report_lines.append("### 🔴 风险预警")
                report_lines.append("")

                # 风险分类统计
                risk_by_cat = risk_opportunity.get('risk_by_category', {})
                if risk_by_cat:
                    cat_names = {
                        'regulatory_risk': '监管风险',
                        'competitive_risk': '竞争风险',
                        'technical_risk': '技术风险',
                        'market_risk': '市场风险'
                    }
                    report_lines.append("**风险类型分布：**")
                    for cat, count in risk_by_cat.items():
                        cat_name = cat_names.get(cat, cat)
                        report_lines.append(f"- {cat_name}: {count}条")
                    report_lines.append("")

                # 高风险事件
                report_lines.append("**主要风险事件：**")
                report_lines.append("")
                for i, risk in enumerate(risks[:5], 1):
                    title = risk.get('title', 'N/A')
                    category = risk.get('category', '')
                    description = risk.get('description', 'N/A')
                    entities = risk.get('affected_entities', [])
                    suggestion = risk.get('suggestion', '')
                    importance = risk.get('importance', 'medium')

                    importance_icon = {'high': '🔥', 'medium': '⚠️', 'low': '📌'}.get(importance, '⚠️')
                    imp_text = {'high': '高', 'medium': '中', 'low': '低'}.get(importance, '中')

                    report_lines.append(f"{i}. {importance_icon} **{title}**")
                    report_lines.append(f"   - 类型: {category}")
                    report_lines.append(f"   - 描述: {description}")
                    if entities:
                        report_lines.append(f"   - 受影响实体: {', '.join(entities[:3])}")
                    if suggestion:
                        report_lines.append(f"   - 建议: {suggestion}")
                    report_lines.append("")
            else:
                report_lines.append("### 🔴 风险预警")
                report_lines.append("")
                report_lines.append("本日暂无明显风险事件。")
                report_lines.append("")

            # 机会提示
            if opportunities:
                report_lines.append("### 🟢 投资机会")
                report_lines.append("")

                # 机会分类统计
                opp_by_cat = risk_opportunity.get('opportunity_by_category', {})
                if opp_by_cat:
                    cat_names = {
                        'investment_opportunity': '投资机会',
                        'business_opportunity': '商业机会',
                        'partnership_opportunity': '合作机会',
                        'technology_opportunity': '技术机会'
                    }
                    report_lines.append("**机会类型分布：**")
                    for cat, count in opp_by_cat.items():
                        cat_name = cat_names.get(cat, cat)
                        report_lines.append(f"- {cat_name}: {count}条")
                    report_lines.append("")

                # 高机会事件
                report_lines.append("**主要机会事件：**")
                report_lines.append("")
                for i, opp in enumerate(opportunities[:5], 1):
                    title = opp.get('title', 'N/A')
                    category = opp.get('category', '')
                    description = opp.get('description', 'N/A')
                    entities = opp.get('affected_entities', [])
                    suggestion = opp.get('suggestion', '')
                    importance = opp.get('importance', 'medium')

                    importance_icon = {'high': '💎', 'medium': '💡', 'low': '📌'}.get(importance, '💡')
                    imp_text = {'high': '高', 'medium': '中', 'low': '低'}.get(importance, '中')

                    report_lines.append(f"{i}. {importance_icon} **{title}**")
                    report_lines.append(f"   - 类型: {category}")
                    report_lines.append(f"   - 描述: {description}")
                    if entities:
                        report_lines.append(f"   - 相关实体: {', '.join(entities[:3])}")
                    if suggestion:
                        report_lines.append(f"   - 建议: {suggestion}")
                    report_lines.append("")
            else:
                report_lines.append("### 🟢 投资机会")
                report_lines.append("")
                report_lines.append("本日暂无明显投资机会。")
                report_lines.append("")

            # 受影响实体汇总
            affected_risk = risk_opportunity.get('affected_entities_risk', {})
            affected_opp = risk_opportunity.get('affected_entities_opportunity', {})

            if affected_risk or affected_opp:
                report_lines.append("### 📊 受影响实体汇总")
                report_lines.append("")

                if affected_risk:
                    report_lines.append("**风险相关实体：**")
                    for entity, count in list(affected_risk.items())[:5]:
                        report_lines.append(f"- {entity}: 涉及{count}次风险")
                    report_lines.append("")

                if affected_opp:
                    report_lines.append("**机会相关实体：**")
                    for entity, count in list(affected_opp.items())[:5]:
                        report_lines.append(f"- {entity}: 涉及{count}次机会")
                    report_lines.append("")

        # 关键摘要
        report_lines.append("## 📌 关键摘要")
        report_lines.append("")
        report_lines.append("本日AI领域重要事件总结：")
        report_lines.append("")

        for i, hotspot in enumerate(hotspots[:3], 1):
            title = hotspot.get('title', 'N/A')
            summary = hotspot.get('summary', 'N/A')
            report_lines.append(f"{i}. **{title}**")
            report_lines.append(f"   {summary}")
            report_lines.append("")

        # 页脚
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*本报告由AI舆情分析系统自动生成（阿里云百炼 qwen-plus）*")

        return '\n'.join(report_lines)

    def generate_report(self) -> str:
        """生成报告主函数"""
        print("\n📝 开始生成报告...")

        # 加载数据
        news_list = self.load_data()

        # 加载分析数据
        analysis_path = OUTPUT_DIR / 'analysis_report.json'
        if analysis_path.exists():
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        else:
            # 如果没有分析数据，生成基础分析
            from analyzer import NewsAnalyzer
            analyzer = NewsAnalyzer(news_list)
            analysis_data = analyzer.generate_analysis_report()

        # 生成报告
        if self.use_llm:
            report = self.generate_report_with_llm(news_list, analysis_data)
        else:
            report = self.generate_report_with_template(news_list, analysis_data)

        # 保存报告
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(DAILY_REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 报告已生成: {DAILY_REPORT_FILE}")

        return report


def main():
    """报告生成器主函数"""
    # 尝试使用LLM，如果失败则使用模板
    generator = ReportGenerator(use_llm=True)
    report = generator.generate_report()

    print("\n" + "="*50)
    print("📄 报告内容预览")
    print("="*50)
    # 打印前50行
    lines = report.split('\n')
    for line in lines[:50]:
        print(line)
    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)")


if __name__ == "__main__":
    main()