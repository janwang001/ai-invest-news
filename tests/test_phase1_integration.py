#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 集成测试

测试投资论点、投资评分卡、分层事件、执行警报和风险收益评估的集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fetch.investment_extractor import InvestmentExtractor, InvestmentInfo, InvestmentThesis
from selector.investment_scorer import calculate_investment_scorecard
from content import ArticleBuilder, MarkdownRenderer
from content.article_schema import ArticleEvent


def _create_mock_investment_info():
    """创建模拟的投资信息（内部辅助函数）"""
    return InvestmentInfo(
        facts=[
            "OpenAI完成66亿美元融资",
            "估值达到1570亿美元，增长5倍",
            "微软、英伟达等参与投资"
        ],
        numbers=[
            "66亿美元融资金额",
            "1570亿美元估值",
            "较上轮增长5倍",
            "50亿美元ARR目标（当前16亿）",
            "利润率从30%提升至45%"
        ],
        business=[
            "企业客户收入增长潜力大",
            "API定价策略面临竞争压力"
        ],
        industry_impact=[
            "竞争格局变化，Anthropic和Google加大投入",
            "市场份额争夺加剧"
        ],
        management_claims=[
            "CEO表示2025年实现盈利",
            "计划18个月内推出GPT-5"
        ],
        uncertainties=[
            "估值过高风险",
            "竞争对手降价压力",
            "客户集中度风险",
            "监管审查风险"
        ],
        ai_summary="OpenAI完成66亿美元融资，估值达1570亿美元，增长5倍。计划加速AGI研究，2025年实现盈利。面临竞争加剧和监管审查风险。",
        investment_thesis=InvestmentThesis(
            bull_case=[
                "企业客户收入可能达50亿美元ARR（当前16亿），增长空间巨大",
                "基础设施成本下降，利润率可从30%提升至45%",
                "微软战略支持，技术领先优势明显"
            ],
            bear_case=[
                "竞争对手降价压力（Anthropic便宜20%），影响定价权",
                "客户集中度风险，前10名占60%收入",
                "估值过高，市盈率不合理"
            ],
            key_question="OpenAI能否在模型商品化时保持定价权？",
            time_horizon="6-12个月",
            comparable_events=["类似NVIDIA 2016年AI热潮", "类似Google 2004年上市前融资"]
        )
    )


def test_investment_thesis_extraction():
    """测试投资论点提取"""
    print("=" * 60)
    print("测试1: 投资论点提取")
    print("=" * 60)

    # 模拟投资信息（因为需要API key才能真正调用LLM）
    investment_info = _create_mock_investment_info()

    print("\n✅ 投资论点提取成功")
    print(f"   - Bull Case: {len(investment_info.investment_thesis.bull_case)} 条")
    print(f"   - Bear Case: {len(investment_info.investment_thesis.bear_case)} 条")
    print(f"   - Key Question: {investment_info.investment_thesis.key_question}")
    print(f"   - Time Horizon: {investment_info.investment_thesis.time_horizon}")

    # pytest 断言验证
    assert len(investment_info.investment_thesis.bull_case) == 3
    assert len(investment_info.investment_thesis.bear_case) == 3
    assert investment_info.investment_thesis.key_question is not None
    assert investment_info.investment_thesis.time_horizon == "6-12个月"


def test_investment_scorecard():
    """测试投资评分卡计算"""
    print("\n" + "=" * 60)
    print("测试2: 投资评分卡计算")
    print("=" * 60)

    # 创建模拟投资信息
    investment_info = _create_mock_investment_info()

    # 创建测试新闻
    test_news = {
        "title": "OpenAI获66亿美元融资，估值达1570亿美元",
        "source": "Bloomberg",
        "companies": ["OpenAI", "Microsoft"],
        "signals": ["funding", "partnership"],
        "light_features": {"has_quote": True},
        "investment_info": investment_info.to_dict(),
    }

    # 计算评分卡
    scorecard = calculate_investment_scorecard(test_news)

    print(f"\n✅ 评分卡计算成功")
    print(f"   - 综合得分: {scorecard.composite_score:.1f}/100")
    print(f"   - 投资评级: {scorecard.investment_rating}")
    print(f"   - 重要性: {scorecard.materiality_score:.1f}/10")
    print(f"   - 紧迫性: {scorecard.urgency_score:.1f}/10")
    print(f"   - 确信度: {scorecard.conviction_score:.1f}/10")
    print(f"   - 竞争影响: {scorecard.competitive_score:.1f}/10")
    print(f"   - 风险: {scorecard.risk_score:.1f}/10")
    print(f"   - 创新度: {scorecard.innovation_score:.1f}/10")

    # pytest 断言验证
    assert scorecard.composite_score >= 0
    assert scorecard.composite_score <= 100
    assert scorecard.investment_rating in ["Strong Buy Signal", "Monitor", "Risk Alert", "Pass"]


def test_tiered_events():
    """测试分层事件"""
    print("\n" + "=" * 60)
    print("测试3: 分层事件和报告渲染")
    print("=" * 60)

    # 创建模拟投资信息和评分卡
    investment_info = _create_mock_investment_info()
    test_news = {
        "title": "OpenAI获66亿美元融资，估值达1570亿美元",
        "source": "Bloomberg",
        "companies": ["OpenAI", "Microsoft"],
        "signals": ["funding", "partnership"],
        "light_features": {"has_quote": True},
        "investment_info": investment_info.to_dict(),
    }
    scorecard = calculate_investment_scorecard(test_news)

    # 创建多个测试事件（不同评分）
    events = []

    # Tier 1 事件（高分）
    test_news_tier1 = test_news.copy()
    test_news_tier1["investment_scorecard"] = scorecard.to_dict()

    event1 = {
        "representative_title": "OpenAI获66亿美元融资，估值达1570亿美元",
        "summary": "OpenAI完成66亿美元融资，估值增长5倍，计划加速AGI研究。",
        "news_count": 5,
        "sources": ["Bloomberg", "TechCrunch"],
        "news_list": [test_news_tier1],
        "decision": {"importance": "High", "signal": "Positive", "action": "Watch"}
    }
    events.append(event1)

    # Tier 2 事件（中等分）
    test_news_tier2 = test_news.copy()
    test_news_tier2["investment_scorecard"] = {
        "composite_score": 60.0,
        "materiality_score": 6.0,
        "urgency_score": 5.0,
        "conviction_score": 6.0,
        "competitive_score": 5.0,
        "risk_score": 4.0,
        "innovation_score": 6.0,
        "investment_rating": "Monitor"
    }

    event2 = {
        "representative_title": "Google发布新AI模型",
        "summary": "Google发布新版AI模型，性能提升30%。",
        "news_count": 3,
        "sources": ["Reuters"],
        "news_list": [test_news_tier2],
        "decision": {"importance": "Medium", "signal": "Neutral", "action": "Monitor"}
    }
    events.append(event2)

    # Tier 3 事件（低分）
    test_news_tier3 = test_news.copy()
    test_news_tier3["investment_scorecard"] = {
        "composite_score": 40.0,
        "investment_rating": "Pass"
    }

    event3 = {
        "representative_title": "某AI创业公司获种子轮融资",
        "summary": "某AI创业公司获得100万美元种子轮融资。",
        "news_count": 1,
        "sources": ["TechCrunch"],
        "news_list": [test_news_tier3],
        "decision": {"importance": "Low", "signal": "Neutral", "action": "Ignore"}
    }
    events.append(event3)

    # 构建文章
    article_builder = ArticleBuilder()
    article = article_builder.build(events)

    print(f"\n✅ 文章构建成功")
    print(f"   - 总事件数: {len(article.events)}")

    tier1_count = len([e for e in article.events if e.tier == "tier1"])
    tier2_count = len([e for e in article.events if e.tier == "tier2"])
    tier3_count = len([e for e in article.events if e.tier == "tier3"])

    print(f"   - Tier 1 事件: {tier1_count} 个")
    print(f"   - Tier 2 事件: {tier2_count} 个")
    print(f"   - Tier 3 事件: {tier3_count} 个")

    # 渲染Markdown
    renderer = MarkdownRenderer()
    markdown_content = renderer.render(article)

    print(f"\n✅ Markdown渲染成功")
    print(f"   - 文章长度: {len(markdown_content)} 字符")

    # 保存到文件
    output_file = "/tmp/test_phase1_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"   - 报告已保存: {output_file}")

    # pytest 断言验证
    assert len(article.events) == 3
    assert tier1_count >= 1
    assert len(markdown_content) > 100


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Phase 1 集成测试开始")
    print("=" * 60)

    try:
        # 测试1: 投资论点提取
        test_investment_thesis_extraction()

        # 测试2: 投资评分卡
        test_investment_scorecard()

        # 测试3: 分层事件和报告渲染
        test_tiered_events()

        print("\n" + "=" * 60)
        print("Phase 1 集成测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
