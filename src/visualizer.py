"""
可视化模块
使用前端marked.js渲染Markdown，精美渐变背景+白色卡片设计
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from collections import Counter

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import STRUCTURED_NEWS_FILE, OUTPUT_DIR, VISUALIZATION_FILE, DAILY_REPORT_FILE


class NewsVisualizer:
    """新闻可视化生成器"""

    def __init__(self):
        self.news_list = []
        self.analysis_data = {}

    def load_data(self) -> None:
        with open(STRUCTURED_NEWS_FILE, 'r', encoding='utf-8') as f:
            self.news_list = json.load(f)

        analysis_path = OUTPUT_DIR / 'analysis_report.json'
        if analysis_path.exists():
            with open(analysis_path, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)

        print(f"📂 加载 {len(self.news_list)} 条新闻数据")

    def load_markdown_report(self) -> str:
        if DAILY_REPORT_FILE.exists():
            with open(DAILY_REPORT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        return "# 暂无报告\n\n请先运行报告生成模块。"

    def generate_comprehensive_html(self) -> str:
        # 统计数据
        categories = Counter()
        sentiments = Counter()
        importance = Counter()
        companies = Counter()
        technologies = Counter()
        sources = Counter()
        date_dist = Counter()

        for news in self.news_list:
            categories[news.get('category', {}).get('primary', 'Unknown')] += 1
            sentiments[news.get('analysis', {}).get('sentiment', 'neutral')] += 1
            importance[news.get('analysis', {}).get('importance', 'medium')] += 1
            sources[news.get('source', {}).get('name', 'Unknown')] += 1
            date = news.get('publishTime', '').split('T')[0]
            if date:
                date_dist[date] += 1
            for company in news.get('entities', {}).get('companies', []):
                companies[company] += 1
            for tech in news.get('entities', {}).get('technologies', []):
                technologies[tech] += 1

        md_report = self.load_markdown_report()
        hotspots = self.analysis_data.get('hotspots', [])

        # 转义Markdown内容用于JavaScript
        import json as json_module
        md_report_escaped = json_module.dumps(md_report)

        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI舆情分析日报</title>
    <!-- marked.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }}

        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}

        /* 头部 */
        header {{
            text-align: center;
            color: white;
            padding: 40px 20px;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        header p {{ font-size: 1.1em; opacity: 0.9; }}

        /* 导航 */
        .nav-tabs {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin: 25px 0;
            flex-wrap: wrap;
        }}

        .nav-tab {{
            padding: 12px 28px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s;
        }}

        .nav-tab:hover {{ background: rgba(255,255,255,0.3); }}

        .nav-tab.active {{
            background: white;
            color: #667eea;
            border-color: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}

        /* 内容区 */
        .content-section {{ display: none; animation: fadeIn 0.4s ease; }}
        .content-section.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        /* 卡片 */
        .card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 5px 25px rgba(0,0,0,0.1);
        }}

        .card h2 {{
            font-size: 1.4em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #667eea;
        }}

        /* 统计卡片 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}

        .stat-box {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 25px rgba(0,0,0,0.1);
        }}

        .stat-box .number {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stat-box .label {{ color: #888; margin-top: 8px; }}

        /* Markdown样式 - 白底清晰版 */
        .md-content {{
            font-size: 16px;
            line-height: 1.9;
            color: #333;
            word-wrap: break-word;
            white-space: normal;
        }}

        .md-content h1 {{
            font-size: 2em;
            font-weight: bold;
            color: #1a1a2e;
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}

        .md-content h2 {{
            font-size: 1.6em;
            font-weight: 700;
            color: #1a1a2e;
            margin: 28px 0 18px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }}

        .md-content h3 {{
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
            margin: 22px 0 14px;
        }}

        .md-content h4 {{
            font-size: 1.15em;
            font-weight: 600;
            color: #333;
            margin: 18px 0 12px;
        }}

        .md-content p {{
            margin: 0 0 16px;
            line-height: 1.9;
            word-wrap: break-word;
        }}

        .md-content ul, .md-content ol {{
            margin: 0 0 16px;
            padding-left: 2em;
        }}

        .md-content li {{
            margin: 8px 0;
            line-height: 1.7;
        }}

        .md-content strong {{
            font-weight: 600;
            color: #111;
        }}

        .md-content blockquote {{
            margin: 16px 0;
            padding: 12px 20px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            color: #555;
        }}

        .md-content code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 90%;
        }}

        .md-content pre {{
            background: #2d3436;
            color: #dfe6e9;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
        }}

        .md-content pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}

        .md-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }}

        .md-content table th {{
            background: #667eea;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }}

        .md-content table td {{
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
        }}

        .md-content table tr:nth-child(even) {{ background: #fafafa; }}
        .md-content table tr:hover {{ background: #f0f4ff; }}

        .md-content hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 25px 0;
        }}

        .md-content a {{
            color: #667eea;
            text-decoration: none;
        }}

        .md-content a:hover {{ text-decoration: underline; }}

        /* 条形图 */
        .bar-container {{ margin: 10px 0; }}
        .bar-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 14px;
            color: #555;
        }}
        .bar {{
            background: #f0f0f0;
            border-radius: 8px;
            height: 28px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: 8px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.6s ease;
        }}

        /* 热点卡片 */
        .hotspot-card {{
            background: #f8f9ff;
            border-left: 4px solid #667eea;
            padding: 18px;
            margin-bottom: 12px;
            border-radius: 0 10px 10px 0;
        }}
        .hotspot-card h4 {{ font-size: 1.05em; color: #333; margin-bottom: 8px; }}
        .hotspot-card .meta {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }}
        .hotspot-card .tag {{
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .hotspot-card .tag.high {{ background: #e74c3c; }}
        .hotspot-card .tag.medium {{ background: #f39c12; }}

        /* 数据表格 */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .data-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        .data-table tr:nth-child(even) {{ background: #fafafa; }}
        .data-table tr:hover {{ background: #f0f4ff; }}

        /* 图表网格 */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}

        /* 页脚 */
        footer {{
            text-align: center;
            color: white;
            padding: 30px;
            opacity: 0.9;
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            header h1 {{ font-size: 1.8em; }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI舆情分析日报</h1>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {len(self.news_list)} 条新闻</p>
        </header>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection('overview')">📊 概览</button>
            <button class="nav-tab" onclick="showSection('risk')">⚠️ 风险与机会</button>
            <button class="nav-tab" onclick="showSection('report')">📄 报告</button>
            <button class="nav-tab" onclick="showSection('charts')">📈 图表</button>
            <button class="nav-tab" onclick="showSection('data')">📋 数据</button>
        </div>

        <div id="overview" class="content-section active">
            <div class="stats-grid">
                <div class="stat-box"><div class="number">{len(self.news_list)}</div><div class="label">📰 新闻</div></div>
                <div class="stat-box"><div class="number">{len(sources)}</div><div class="label">📡 来源</div></div>
                <div class="stat-box"><div class="number">{len(companies)}</div><div class="label">🏢 公司</div></div>
                <div class="stat-box"><div class="number">{len(technologies)}</div><div class="label">💻 技术</div></div>
            </div>
            <div class="card"><h2>🔥 热点</h2>{self._generate_hotspots_html(hotspots)}</div>
            <div class="card"><h2>📊 统计</h2>
                <div class="charts-grid">
                    <div><h3 style="margin-bottom:15px;color:#555;">分类</h3>{self._generate_bars_html(dict(categories.most_common(6)))}</div>
                    <div><h3 style="margin-bottom:15px;color:#555;">情感</h3>{self._generate_bars_html(dict(sentiments.most_common()), True)}</div>
                </div>
            </div>
        </div>

        <div id="risk" class="content-section">
            {self._generate_risk_opportunity_section()}
        </div>

        <div id="report" class="content-section">
            <div class="card">
                <div id="md-container" class="md-content">
                    <p style="text-align:center;color:#888;padding:50px;">加载中...</p>
                </div>
            </div>
        </div>

        <div id="charts" class="content-section">
            <div class="card"><h2>📊 分类分布</h2>{self._generate_bars_html(dict(categories.most_common(10)))}</div>
            <div class="card"><h2>💭 情感分析</h2>{self._generate_bars_html(dict(sentiments.most_common()), True)}</div>
            <div class="card"><h2>🎯 重要性</h2>{self._generate_bars_html(dict(importance.most_common()), False, True)}</div>
            <div class="card"><h2>🏢 公司 TOP10</h2>{self._generate_bars_html(dict(companies.most_common(10)))}</div>
            <div class="card"><h2>💻 技术 TOP10</h2>{self._generate_bars_html(dict(technologies.most_common(10)))}</div>
            <div class="card"><h2>📰 来源</h2>{self._generate_bars_html(dict(sources.most_common(10)))}</div>
            <div class="card"><h2>📅 时间</h2>{self._generate_timeline_html(dict(sorted(date_dist.items())))}</div>
        </div>

        <div id="data" class="content-section">
            <div class="card">
                <h2>📋 数据列表</h2>
                <div style="overflow-x:auto;">
                    <table class="data-table">
                        <thead><tr><th>标题</th><th>来源</th><th>分类</th><th>重要性</th><th>情感</th><th>时间</th></tr></thead>
                        <tbody>{self._generate_table_rows()}</tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer><p>AI舆情分析日报系统 © {datetime.now().year}</p></footer>
    </div>

    <script>
        const mdContent = {md_report_escaped};

        marked.setOptions({{ breaks: true, gfm: true }});

        function renderMarkdown() {{
            const container = document.getElementById('md-container');
            if (container && typeof marked !== 'undefined') {{
                container.innerHTML = marked.parse(mdContent);
            }}
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', renderMarkdown);
        }} else {{
            renderMarkdown();
        }}

        function showSection(id) {{
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

        return html_content

    def _generate_bars_html(self, data: dict, sentiment: bool = False, importance: bool = False) -> str:
        if not data:
            return "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"
        max_val = max(data.values())
        parts = []
        for label, value in data.items():
            pct = (value / max_val * 100) if max_val else 0
            display = label
            if sentiment:
                display = {'positive': '😊 正面', 'neutral': '😐 中性', 'negative': '😟 负面'}.get(label, label)
            elif importance:
                display = {'high': '🔥 高', 'medium': '📊 中', 'low': '📌 低'}.get(label, label)
            parts.append(f'<div class="bar-container"><div class="bar-label"><span>{display}</span><span>{value}</span></div><div class="bar"><div class="bar-fill" style="width:{max(pct,5)}%"></div></div></div>')
        return '\n'.join(parts)

    def _generate_hotspots_html(self, hotspots: list) -> str:
        if not hotspots:
            return "<p style='color:#888;text-align:center;padding:20px;'>暂无</p>"
        parts = []
        for i, h in enumerate(hotspots, 1):
            title = h.get('title', 'N/A')
            summary = h.get('summary', 'N/A')
            imp = h.get('importance', 'medium')
            cat = h.get('category', 'N/A')
            comps = h.get('key_entities', {}).get('companies', [])
            imp_text = {'high': '🔥 高', 'medium': '📊 中', 'low': '📌 低'}.get(imp, imp)
            comp_html = f'<p style="color:#666;font-size:13px;margin-top:6px;">公司: {", ".join(comps[:3])}</p>' if comps else ''
            parts.append(f'''<div class="hotspot-card">
                <h4>{i}. {title[:50]}{'...' if len(title)>50 else ''}</h4>
                <div class="meta"><span class="tag {imp}">{imp_text}</span><span class="tag">{cat}</span></div>
                <p style="color:#555;margin:8px 0 0;">{summary}</p>{comp_html}
            </div>''')
        return '\n'.join(parts)

    def _generate_timeline_html(self, date_dist: dict) -> str:
        if not date_dist:
            return "<p style='color:#888;text-align:center;padding:20px;'>暂无</p>"
        max_val = max(date_dist.values())
        parts = ['<div style="display:grid;gap:8px;">']
        for date, count in sorted(date_dist.items()):
            pct = (count / max_val * 100) if max_val else 0
            parts.append(f'''<div style="display:flex;align-items:center;gap:12px;">
                <span style="min-width:90px;color:#666;font-size:13px;">{date}</span>
                <div style="flex:1;background:#f0f0f0;height:22px;border-radius:11px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:11px;"></div>
                </div>
                <span style="min-width:30px;text-align:right;font-weight:bold;color:#333;">{count}</span>
            </div>''')
        parts.append('</div>')
        return '\n'.join(parts)

    def _generate_risk_opportunity_section(self) -> str:
        """生成风险与机会模块"""
        ro_data = self.analysis_data.get('risk_opportunity', {})

        risks = ro_data.get('risks', [])
        opportunities = ro_data.get('opportunities', [])
        risk_by_cat = ro_data.get('risk_by_category', {})
        opp_by_cat = ro_data.get('opportunity_by_category', {})
        entities_risk = ro_data.get('affected_entities_risk', {})
        entities_opp = ro_data.get('affected_entities_opportunity', {})
        risk_count = ro_data.get('risk_count', 0)
        opp_count = ro_data.get('opportunity_count', 0)

        # 统计数字卡片
        stats_html = f'''
        <div class="stats-grid">
            <div class="stat-box" style="background: linear-gradient(135deg, #fff5f5, #fff);">
                <div class="number" style="color: #e74c3c;">⚠️ {risk_count}</div>
                <div class="label">风险事件</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #f0fff4, #fff);">
                <div class="number" style="color: #27ae60;">💡 {opp_count}</div>
                <div class="label">机会事件</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(risk_by_cat)}</div>
                <div class="label">风险类型</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(opp_by_cat)}</div>
                <div class="label">机会类型</div>
            </div>
        </div>
        '''

        # 风险和机会并排展示
        risks_html = self._generate_risk_cards(risks[:8], is_risk=True)
        opportunities_html = self._generate_risk_cards(opportunities[:8], is_risk=False)

        # 分类分布
        risk_dist_html = self._generate_bars_html(risk_by_cat) if risk_by_cat else "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"
        opp_dist_html = self._generate_bars_html(opp_by_cat) if opp_by_cat else "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"

        # 受影响实体
        entities_risk_html = self._generate_entity_bars(entities_risk, is_risk=True) if entities_risk else "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"
        entities_opp_html = self._generate_entity_bars(entities_opp, is_risk=False) if entities_opp else "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"

        return f'''
        {stats_html}

        <div class="charts-grid" style="margin-top:20px;">
            <div class="card">
                <h2>⚠️ 风险事件</h2>
                {risks_html}
            </div>
            <div class="card">
                <h2>💡 机会事件</h2>
                {opportunities_html}
            </div>
        </div>

        <div class="charts-grid" style="margin-top:20px;">
            <div class="card">
                <h2>📊 风险类型分布</h2>
                {risk_dist_html}
            </div>
            <div class="card">
                <h2>📊 机会类型分布</h2>
                {opp_dist_html}
            </div>
        </div>

        <div class="charts-grid" style="margin-top:20px;">
            <div class="card">
                <h2>🏢 受风险影响的实体</h2>
                {entities_risk_html}
            </div>
            <div class="card">
                <h2>🏢 受机会影响的实体</h2>
                {entities_opp_html}
            </div>
        </div>
        '''

    def _generate_risk_cards(self, items: list, is_risk: bool = True) -> str:
        """生成风险或机会卡片"""
        if not items:
            return "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"

        icon = "⚠️" if is_risk else "💡"
        border_color = "#e74c3c" if is_risk else "#27ae60"
        bg_color = "#fff5f5" if is_risk else "#f0fff4"

        parts = []
        for i, item in enumerate(items, 1):
            title = item.get('title', 'N/A')[:60]
            category = item.get('category', 'N/A')
            description = item.get('description', '')[:150]
            entities = item.get('affected_entities', [])
            suggestion = item.get('suggestion', '')
            importance = item.get('importance', 'medium')

            imp_emoji = {'high': '🔥', 'medium': '📊', 'low': '📌'}.get(importance, '📊')
            entities_html = f'<div style="margin-top:8px;"><span style="color:#888;font-size:12px;">影响实体: </span>{", ".join(entities[:5])}</div>' if entities else ''
            suggestion_html = f'<div style="margin-top:8px;padding:8px;background:#fff;border-radius:6px;font-size:13px;"><strong>💡 建议:</strong> {suggestion[:200]}</div>' if suggestion else ''

            parts.append(f'''
            <div style="background:{bg_color};border-left:4px solid {border_color};padding:15px;margin-bottom:12px;border-radius:0 10px 10px 0;">
                <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                    <h4 style="font-size:1em;color:#333;margin:0;flex:1;">{icon} {title}</h4>
                    <span style="background:{border_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;margin-left:10px;">{imp_emoji} {importance}</span>
                </div>
                <div style="color:#666;font-size:13px;">{description}</div>
                <div style="margin-top:6px;"><span style="background:#eee;padding:2px 8px;border-radius:10px;font-size:11px;color:#555;">{category}</span></div>
                {entities_html}
                {suggestion_html}
            </div>
            ''')

        return '\n'.join(parts)

    def _generate_entity_bars(self, entities: dict, is_risk: bool = True) -> str:
        """生成受影响实体的条形图"""
        if not entities:
            return "<p style='color:#888;text-align:center;padding:20px;'>暂无数据</p>"

        max_val = max(entities.values())
        color = "#e74c3c" if is_risk else "#27ae60"
        parts = []

        for entity, count in list(entities.items())[:10]:
            pct = (count / max_val * 100) if max_val else 0
            parts.append(f'''
            <div style="margin:8px 0;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                    <span style="color:#333;">{entity}</span>
                    <span style="color:#666;">{count}</span>
                </div>
                <div style="background:#f0f0f0;height:20px;border-radius:10px;overflow:hidden;">
                    <div style="width:{max(pct,5)}%;height:100%;background:{color};border-radius:10px;"></div>
                </div>
            </div>
            ''')

        return '\n'.join(parts)

    def _generate_table_rows(self) -> str:
        parts = []
        for news in self.news_list:
            title = news.get('title', 'N/A')
            source = news.get('source', {}).get('name', 'Unknown')
            cat = news.get('category', {}).get('primary', 'N/A')
            imp = news.get('analysis', {}).get('importance', 'medium')
            sent = news.get('analysis', {}).get('sentiment', 'neutral')
            time = news.get('publishTime', '').split('T')[0]
            imp_e = {'high': '🔥', 'medium': '📊', 'low': '📌'}.get(imp, '📊')
            sent_e = {'positive': '😊', 'neutral': '😐', 'negative': '😟'}.get(sent, '😐')
            parts.append(f'<tr><td>{title[:35]}{"..." if len(title)>35 else ""}</td><td>{source}</td><td>{cat}</td><td>{imp_e} {imp}</td><td>{sent_e} {sent}</td><td>{time}</td></tr>')
        return '\n'.join(parts)

    def generate_visualization(self) -> str:
        print("\n📈 生成可视化页面...")
        self.load_data()
        html = self.generate_comprehensive_html()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(VISUALIZATION_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 已生成: {VISUALIZATION_FILE}")
        return html


if __name__ == "__main__":
    NewsVisualizer().generate_visualization()