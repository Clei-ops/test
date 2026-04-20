#!/usr/bin/env python3
"""
AI舆情分析日报系统 - 主程序入口
从每日AI新闻中提取结构化洞察
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processor import DataProcessor
from src.analyzer import NewsAnalyzer
from src.report_generator import ReportGenerator
from src.visualizer import NewsVisualizer
from config import RAW_NEWS_FILE, STRUCTURED_NEWS_FILE, DAILY_REPORT_FILE, VISUALIZATION_FILE


def run_full_pipeline(skip_extraction: bool = False, use_llm: bool = True):
    """运行完整处理流程

    Args:
        skip_extraction: 是否跳过结构化抽取（使用已有数据）
        use_llm: 是否使用LLM生成报告
    """
    print("=" * 60)
    print("🤖 AI舆情分析日报系统")
    print("=" * 60)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Step 1: 数据清洗与结构化抽取
    if not skip_extraction:
        print("\n" + "▶" * 20)
        print("Step 1: 数据清洗与结构化抽取")
        print("▶" * 20)

        processor = DataProcessor()

        # 加载原始数据
        raw_news = processor.load_raw_news()

        # 处理数据（分批处理）
        structured_news = processor.process_all_news(raw_news)

        # 保存结果
        processor.save_structured_news(structured_news)
    else:
        print("\n⏭️ 跳过数据抽取步骤，使用已有结构化数据")

    # Step 2: 数据分析
    print("\n" + "▶" * 20)
    print("Step 2: 数据分析与趋势识别")
    print("▶" * 20)

    analyzer = NewsAnalyzer()
    analyzer.load_structured_news()
    analysis_report = analyzer.generate_analysis_report()

    # 保存分析报告
    analysis_path = Path(__file__).parent / 'output' / 'analysis_report.json'
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, ensure_ascii=False, indent=2)
    print(f"💾 分析数据已保存: {analysis_path}")

    # Step 3: 报告生成
    print("\n" + "▶" * 20)
    print("Step 3: 分析报告生成")
    print("▶" * 20)

    report_generator = ReportGenerator(use_llm=use_llm)
    report = report_generator.generate_report()

    # Step 4: 可视化生成
    print("\n" + "▶" * 20)
    print("Step 4: 可视化页面生成")
    print("▶" * 20)

    visualizer = NewsVisualizer()
    visualizer.generate_visualization()

    # 完成
    print("\n" + "=" * 60)
    print("✅ 处理完成！")
    print("=" * 60)
    print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📁 输出文件:")
    print(f"  - 结构化数据: {STRUCTURED_NEWS_FILE}")
    print(f"  - 分析报告: {DAILY_REPORT_FILE}")
    print(f"  - 可视化页面: {VISUALIZATION_FILE}")
    print("\n💡 提示:")
    print("  - 在浏览器中打开 visualization.html 查看可视化图表")
    print("  - 使用 Markdown 阅读器查看 daily_report.md")
    print("=" * 60)


def run_extraction_only():
    """仅运行数据抽取"""
    print("=" * 60)
    print("🔄 数据清洗与结构化抽取")
    print("=" * 60)

    processor = DataProcessor()
    raw_news = processor.load_raw_news()
    structured_news = processor.process_all_news(raw_news)
    processor.save_structured_news(structured_news)

    print("\n✅ 数据抽取完成")


def run_analysis_only():
    """仅运行数据分析"""
    print("=" * 60)
    print("📊 数据分析与趋势识别")
    print("=" * 60)

    analyzer = NewsAnalyzer()
    analyzer.load_structured_news()
    report = analyzer.generate_analysis_report()

    # 保存报告
    analysis_path = Path(__file__).parent / 'output' / 'analysis_report.json'
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n✅ 分析完成")


def run_report_only(use_llm: bool = True):
    """仅生成报告"""
    print("=" * 60)
    print("📝 分析报告生成")
    print("=" * 60)

    generator = ReportGenerator(use_llm=use_llm)
    generator.generate_report()

    print("\n✅ 报告生成完成")


def run_visualization_only():
    """仅生成可视化"""
    print("=" * 60)
    print("📈 可视化页面生成")
    print("=" * 60)

    visualizer = NewsVisualizer()
    visualizer.generate_visualization()

    print("\n✅ 可视化生成完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI舆情分析日报系统 - 从每日AI新闻中提取结构化洞察",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整流程
  python main.py

  # 跳过数据抽取步骤（使用已有结构化数据）
  python main.py --skip-extraction

  # 仅运行数据抽取
  python main.py --extraction-only

  # 仅生成报告（使用模板，不调用LLM）
  python main.py --report-only --no-llm

  # 仅生成可视化
  python main.py --visualization-only
        """
    )

    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='跳过数据抽取步骤，使用已有的结构化数据'
    )

    parser.add_argument(
        '--extraction-only',
        action='store_true',
        help='仅运行数据清洗与结构化抽取'
    )

    parser.add_argument(
        '--analysis-only',
        action='store_true',
        help='仅运行数据分析'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        help='仅生成分析报告'
    )

    parser.add_argument(
        '--visualization-only',
        action='store_true',
        help='仅生成可视化页面'
    )

    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='不使用LLM生成报告（使用模板生成）'
    )

    args = parser.parse_args()

    # 检查API Key（如果需要LLM）
    if not args.no_llm and (args.extraction_only or not args.skip_extraction):
        import os
        # 检查阿里云百炼 API Key
        api_key = os.environ.get('DASHSCOPE_API_KEY', '')
        if not api_key:
            # 尝试从 config.py 获取
            try:
                from config import DASHSCOPE_API_KEY as config_key
                api_key = config_key
            except:
                pass

        if not api_key or api_key == 'your_api_key_here':
            print("⚠️ 警告: 未设置 DASHSCOPE_API_KEY")
            print("请在 config.py 中设置 API Key 或执行:")
            print("  export DASHSCOPE_API_KEY='your_api_key'")
            print("或使用 --no-llm 选项跳过LLM调用")
            return

    # 根据参数选择运行模式
    if args.extraction_only:
        run_extraction_only()
    elif args.analysis_only:
        run_analysis_only()
    elif args.report_only:
        run_report_only(use_llm=not args.no_llm)
    elif args.visualization_only:
        run_visualization_only()
    else:
        run_full_pipeline(
            skip_extraction=args.skip_extraction,
            use_llm=not args.no_llm
        )


if __name__ == "__main__":
    main()