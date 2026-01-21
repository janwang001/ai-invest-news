#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全流程测试脚本

从 normalize_news 开始，模拟 200 条 RSS 搜索数据，走完所有流程。
Mock 日期设为 2026-06-06 以便区分测试数据。

版本: v2 - 更新 mock 数据以验证 update 流程
"""

import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# 添加 src 目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Mock 数据生成器
# ============================================

# AI 投资新闻的主题模板
NEWS_TEMPLATES = [
    # 融资类
    {
        "title_template": "{company} 完成 {amount} 美元 {round} 轮融资",
        "content_template": "{company} 宣布完成 {amount} 美元 {round} 轮融资，由 {investor} 领投。此次融资将用于 {purpose}。公司估值达到 {valuation} 美元。",
        "category": "funding",
        "signal": "Positive"
    },
    {
        "title_template": "{company} 获得 {amount} 美元投资，加速 AI 商业化",
        "content_template": "{company} 今日宣布获得 {amount} 美元投资，投资方为 {investor}。公司 CEO 表示将利用这笔资金加速 {product} 的商业化进程，预计年底前将实现 {target}。",
        "category": "funding",
        "signal": "Positive"
    },
    # 产品发布类
    {
        "title_template": "{company} 发布全新 {product}，性能提升 {percent}%",
        "content_template": "{company} 正式发布最新一代 {product}，相比上一代产品性能提升 {percent}%。新产品采用 {technology} 技术，将在 {region} 市场率先上市，售价 {price} 美元。",
        "category": "product",
        "signal": "Positive"
    },
    {
        "title_template": "{company} 推出企业级 AI {product}，瞄准 {market} 市场",
        "content_template": "{company} 宣布推出面向企业的 AI {product}，主打 {feature} 功能。该产品已与 {partner} 达成合作，预计将覆盖 {coverage} 家企业客户。",
        "category": "product",
        "signal": "Positive"
    },
    # 芯片硬件类
    {
        "title_template": "{company} 新款 {chip} 芯片开始量产，算力提升 {percent}%",
        "content_template": "{company} 宣布其新款 {chip} AI 芯片已开始量产，相比前代产品算力提升 {percent}%，能效比提升 {efficiency}%。首批芯片将供应给 {customer}。",
        "category": "chip",
        "signal": "Positive"
    },
    {
        "title_template": "GPU 供应紧张：{company} 预计 {chip} 交货周期延长至 {weeks} 周",
        "content_template": "由于 AI 需求激增，{company} 表示其 {chip} 系列产品的交货周期已延长至 {weeks} 周。分析师预计这一情况将持续到 {quarter} 季度末。",
        "category": "chip",
        "signal": "Neutral"
    },
    # 收购合并类
    {
        "title_template": "{acquirer} 宣布以 {amount} 美元收购 AI 初创公司 {target}",
        "content_template": "{acquirer} 今日宣布将以 {amount} 美元收购 AI 初创公司 {target}。此次收购将帮助 {acquirer} 增强在 {field} 领域的技术能力。交易预计于 {quarter} 季度完成。",
        "category": "acquisition",
        "signal": "Positive"
    },
    {
        "title_template": "{company} 与 {partner} 达成战略合作，共同开发 {product}",
        "content_template": "{company} 与 {partner} 宣布达成战略合作协议，双方将共同开发 {product}。合作涉及技术、市场和供应链等多个层面，预计投入 {amount} 美元。",
        "category": "partnership",
        "signal": "Positive"
    },
    # 财报业绩类
    {
        "title_template": "{company} Q{quarter} 财报超预期，AI 收入增长 {percent}%",
        "content_template": "{company} 公布 Q{quarter} 财报，营收 {revenue} 美元，同比增长 {growth}%，其中 AI 相关业务收入增长 {percent}%。公司上调全年业绩指引至 {guidance} 美元。",
        "category": "earnings",
        "signal": "Positive"
    },
    {
        "title_template": "{company} AI 业务承压，Q{quarter} 利润下滑 {percent}%",
        "content_template": "{company} 发布 Q{quarter} 财报显示，受市场竞争加剧影响，公司净利润同比下滑 {percent}%。管理层表示将加大 AI 研发投入，预计下季度情况将有所改善。",
        "category": "earnings",
        "signal": "Risk"
    },
    # 监管政策类
    {
        "title_template": "{region} 出台 AI 新规：{regulation}",
        "content_template": "{region} 政府今日发布 AI 监管新规，主要内容包括 {regulation}。新规将于 {date} 起正式实施，预计将影响 {company} 等公司在该地区的业务。",
        "category": "regulation",
        "signal": "Risk"
    },
    {
        "title_template": "{region} 加大 AI 芯片出口管制，{company} 受影响",
        "content_template": "{region} 宣布进一步收紧 AI 芯片出口管制措施，限制向 {target_region} 出口先进 AI 芯片。{company} 表示正在评估新规对业务的影响。",
        "category": "regulation",
        "signal": "Risk"
    },
    # 技术突破类
    {
        "title_template": "{company} 发布 {model} 模型，在 {benchmark} 上创新纪录",
        "content_template": "{company} 发布最新 AI 模型 {model}，在 {benchmark} 基准测试中达到 {score} 分，刷新行业纪录。该模型参数量为 {params}，训练成本约 {cost} 美元。",
        "category": "research",
        "signal": "Positive"
    },
    {
        "title_template": "{company} 开源 {model}，推动 AI 民主化",
        "content_template": "{company} 宣布开源其 {model} 模型，允许开发者免费使用和修改。该模型在 {benchmark} 测试中表现优异，已获得 {downloads} 次下载。",
        "category": "research",
        "signal": "Positive"
    },
    # 行业动态类
    {
        "title_template": "AI 行业报告：{year} 年市场规模将达 {amount} 美元",
        "content_template": "根据最新行业报告，全球 AI 市场规模预计在 {year} 年达到 {amount} 美元，年复合增长率为 {cagr}%。{segment} 领域增长最快，预计占比将达 {percent}%。",
        "category": "industry",
        "signal": "Neutral"
    },
    {
        "title_template": "{company} CEO：AI 将在 {years} 年内改变 {industry}",
        "content_template": "{company} CEO {name} 在最新采访中表示，AI 技术将在 {years} 年内彻底改变 {industry} 行业的运营方式。他预计公司在该领域的投入将达到 {amount} 美元。",
        "category": "industry",
        "signal": "Neutral"
    },
    # 人事变动类
    {
        "title_template": "{company} 任命 {name} 为首席 AI 官",
        "content_template": "{company} 宣布任命前 {prev_company} 高管 {name} 为公司首席 AI 官。{name} 将负责领导公司的 AI 战略和技术研发工作。",
        "category": "personnel",
        "signal": "Neutral"
    },
    # 市场竞争类
    {
        "title_template": "{company} 与 {competitor} 展开 AI {product} 价格战",
        "content_template": "{company} 宣布将其 AI {product} 价格下调 {percent}%，此举被视为对 {competitor} 近期降价的回应。分析师认为价格战将加速行业整合。",
        "category": "competition",
        "signal": "Risk"
    },
    # 数据中心基础设施
    {
        "title_template": "{company} 投资 {amount} 美元建设 AI 数据中心",
        "content_template": "{company} 宣布将在 {region} 投资 {amount} 美元建设新的 AI 数据中心。该数据中心预计于 {year} 年投入运营，将配备 {gpus} 块 GPU。",
        "category": "infrastructure",
        "signal": "Positive"
    },
    # 应用落地类
    {
        "title_template": "{company} AI 助手日活用户突破 {users} 万",
        "content_template": "{company} 公布其 AI 助手产品数据，日活跃用户已突破 {users} 万，月活用户达到 {mau} 万。用户平均使用时长为 {minutes} 分钟。",
        "category": "application",
        "signal": "Positive"
    },
]

# 公司列表 (v2 更新: 新增更多公司)
COMPANIES = [
    "OpenAI", "Google DeepMind", "Anthropic", "Microsoft", "Meta", "NVIDIA",
    "AMD", "Intel", "Apple", "Amazon", "Alibaba", "ByteDance", "Baidu",
    "Tencent", "Huawei", "xAI", "Mistral AI", "Cohere", "Stability AI",
    "Midjourney", "Runway", "Inflection AI", "Character.AI", "Adept AI",
    "Scale AI", "Databricks", "Snowflake", "Palantir", "C3.ai", "SambaNova",
    "Cerebras", "Groq", "Tesla", "IBM", "Oracle", "Salesforce", "Adobe",
    "Qualcomm", "Broadcom", "TSMC", "Samsung", "SK Hynix",
    # v2 新增公司
    "DeepSeek", "Zhipu AI", "Moonshot AI", "Minimax", "01.AI", "Perplexity",
    "Reka AI", "Together AI", "Anyscale", "Hugging Face", "Lightmatter"
]

# 投资机构
INVESTORS = [
    "红杉资本", "Andreessen Horowitz", "软银愿景基金", "Tiger Global",
    "Benchmark", "Accel", "General Catalyst", "Lightspeed Venture Partners",
    "Index Ventures", "Founders Fund", "Khosla Ventures", "GV",
    "Microsoft Ventures", "Google Ventures", "NVIDIA Ventures"
]

# 新闻来源
NEWS_SOURCES = [
    "TechCrunch", "VentureBeat AI", "The Verge", "Wired", "Ars Technica",
    "Bloomberg Technology", "Reuters Technology", "CNBC Technology",
    "The Information", "MIT Technology Review", "IEEE Spectrum",
    "Synced Review", "Analytics India Magazine", "MarkTechPost",
    "SemiAnalysis", "Tom's Hardware", "EE Times", "Hacker News"
]

# 产品名称
PRODUCTS = [
    "GPT-5", "Gemini Ultra", "Claude 4", "Llama 4", "Stable Diffusion 4",
    "H200 GPU", "MI400 AI 芯片", "Gaudi 3", "神经网络处理器",
    "企业版 Copilot", "AI 代码助手", "智能客服系统", "自动驾驶套件",
    "AI 视频生成器", "多模态 AI 平台", "AI 搜索引擎", "智能分析平台"
]

# 地区
REGIONS = ["美国", "欧盟", "中国", "日本", "韩国", "印度", "新加坡", "英国"]


def generate_mock_content(template: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    根据模板生成 mock 新闻内容

    Args:
        template: 新闻模板
        index: 新闻索引

    Returns:
        Dict: mock 新闻数据
    """
    company = random.choice(COMPANIES)
    company2 = random.choice([c for c in COMPANIES if c != company])
    investor = random.choice(INVESTORS)
    source = random.choice(NEWS_SOURCES)
    product = random.choice(PRODUCTS)
    region = random.choice(REGIONS)

    # 随机数据
    amount = random.choice(["5000万", "1亿", "2.5亿", "5亿", "10亿", "20亿", "50亿", "100亿"])
    round_name = random.choice(["A", "B", "C", "D", "E", "Pre-IPO"])
    percent = random.randint(15, 200)
    quarter = random.randint(1, 4)
    weeks = random.randint(12, 36)
    year = random.randint(2025, 2030)
    users = random.randint(100, 5000)
    gpus = random.randint(10000, 100000)

    # 替换模板中的占位符
    title = template["title_template"].format(
        company=company, amount=amount, round=round_name,
        percent=percent, product=product, region=region,
        chip=random.choice(["H200", "B200", "MI400", "Gaudi 3"]),
        acquirer=company, target=company2, partner=company2,
        quarter=quarter, weeks=weeks, year=year,
        model=random.choice(["GPT-5", "Gemini 2", "Claude 4", "Llama 4"]),
        benchmark=random.choice(["MMLU", "HumanEval", "GSM8K", "HellaSwag"]),
        market=random.choice(["医疗", "金融", "教育", "制造业"]),
        competitor=company2, users=users, name=f"John_{index}",
        regulation=random.choice(["数据安全要求", "算法透明度要求", "AI 伦理准则"]),
        industry=random.choice(["医疗", "金融", "制造", "零售", "物流"]),
        years=random.randint(3, 10)
    )

    content = template["content_template"].format(
        company=company, amount=amount, round=round_name,
        investor=investor, purpose=random.choice(["技术研发", "市场拓展", "人才招聘", "基础设施建设"]),
        valuation=random.choice(["10亿", "50亿", "100亿", "500亿"]),
        product=product, percent=percent, technology=random.choice(["Transformer", "扩散模型", "多模态", "强化学习"]),
        region=region, price=random.randint(100, 10000),
        feature=random.choice(["智能分析", "自动化处理", "实时监控", "预测建模"]),
        partner=company2, coverage=random.randint(100, 10000),
        chip=random.choice(["H200", "B200", "MI400", "Gaudi 3"]),
        efficiency=random.randint(20, 80),
        customer=random.choice(["Microsoft", "Google", "Amazon", "Meta"]),
        weeks=weeks, quarter=quarter,
        acquirer=company, target=company2,
        field=random.choice(["计算机视觉", "自然语言处理", "推荐系统", "机器人"]),
        revenue=random.choice(["100亿", "200亿", "500亿", "1000亿"]),
        growth=random.randint(10, 100),
        guidance=random.choice(["500亿", "800亿", "1200亿"]),
        regulation=random.choice(["数据本地化存储", "算法备案", "内容审核"]),
        date=f"2025年{random.randint(1, 12)}月{random.randint(1, 28)}日",
        target_region=random.choice(["中国", "俄罗斯", "中东"]),
        model=random.choice(["GPT-5", "Gemini 2", "Claude 4", "Llama 4"]),
        benchmark=random.choice(["MMLU", "HumanEval", "GSM8K"]),
        score=random.randint(85, 99),
        params=random.choice(["1万亿", "5000亿", "2000亿"]),
        cost=random.choice(["5000万", "1亿", "5亿"]),
        downloads=random.randint(10000, 1000000),
        cagr=random.randint(15, 45),
        segment=random.choice(["生成式AI", "计算机视觉", "NLP", "机器学习平台"]),
        name=f"CEO_{index}",
        prev_company=company2,
        competitor=company2,
        year=year,
        gpus=gpus,
        users=users,
        mau=users * random.randint(3, 10),
        minutes=random.randint(5, 60),
        years=random.randint(3, 10),
        industry=random.choice(["医疗", "金融", "制造", "零售"])
    )

    # 使用固定的 Mock 日期: 2026-06-06
    base_date = datetime(2026, 6, 6)
    random_days = random.randint(0, 7)
    news_date = base_date - timedelta(days=random_days)

    return {
        "title": f"[Mock-v2-{index}] {title}",
        "content": content,
        "source": source,
        "date": news_date.strftime("%Y-%m-%d"),
        "url": f"https://mock-news-v2.example.com/article/{index}",
        "published_at": news_date.isoformat(),
        "mock_category": template["category"],
        "mock_signal": template["signal"]
    }


def generate_mock_rss_data(count: int = 200) -> List[Dict[str, Any]]:
    """
    生成 mock RSS 搜索数据

    Args:
        count: 生成的新闻数量

    Returns:
        List[Dict]: mock 新闻列表
    """
    # v2: 使用不同的随机种子生成不同的数据
    random.seed(20260606)
    logger.info(f"开始生成 {count} 条 mock RSS 数据 (v2 版本)...")

    news_list = []
    for i in range(1, count + 1):
        template = random.choice(NEWS_TEMPLATES)
        news = generate_mock_content(template, i)
        news_list.append(news)

    logger.info(f"生成完成，共 {len(news_list)} 条新闻")

    # 统计类别分布
    category_stats = {}
    for news in news_list:
        cat = news.get("mock_category", "unknown")
        category_stats[cat] = category_stats.get(cat, 0) + 1

    logger.info(f"类别分布: {category_stats}")

    return news_list


def mock_fetch_article(news: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock 原文抓取：生成更详细的内容

    Args:
        news: 新闻数据

    Returns:
        Dict: 添加了抓取内容的新闻
    """
    # 生成更长的内容（模拟网页抓取）
    fetched_content = news["content"] + "\n\n"

    # 添加更多细节
    fetched_content += "【详细报道】\n"
    fetched_content += f"本报道来源于 {news['source']}，发布时间为 {news['date']}。\n\n"

    # 添加一些数字和引用
    fetched_content += f"据悉，此次事件涉及金额约 ${random.randint(100, 1000)}万美元。"
    fetched_content += "行业分析师表示：\"这是一个重要的里程碑，将对行业产生深远影响。\"\n\n"

    # 添加更多背景信息
    fetched_content += f"背景信息：该公司成立于 {random.randint(2010, 2023)} 年，"
    fetched_content += f"目前员工规模约 {random.randint(100, 10000)} 人，"
    fetched_content += f"年营收约 ${random.randint(10, 500)} 亿美元。"

    news["fetched_content"] = fetched_content
    news["fetched_title"] = news["title"]
    news["fetch_stats"] = {
        "status_code": 200,
        "content_length": len(fetched_content),
        "fetch_time_ms": random.randint(100, 2000)
    }

    return news


def run_full_flow_test():
    """
    运行完整流程测试
    """
    from search.search_result_process import normalize_news, SearchResultProcessor
    from selector.news_selector import NewsSelectorPipeline
    from selector.selector_config import TOP_K_SELECT
    from event.event_pipeline import EventPipeline
    from event.decision import EventDecisionPipeline
    from content import ArticleBuilder, MarkdownRenderer
    from webapp_exporter import export_to_webapp

    logger.info("=" * 60)
    logger.info("开始全流程测试（从 normalize_news 开始）")
    logger.info("=" * 60)

    stats = {}

    # ============================================
    # 第零步：生成 200 条 Mock RSS 数据
    # ============================================
    logger.info("\n第零步：生成 200 条 Mock RSS 数据...")
    raw_news = generate_mock_rss_data(200)
    stats["mock_data_count"] = len(raw_news)

    # ============================================
    # 第二步：规范化新闻（从这里开始是正式流程）
    # ============================================
    logger.info("\n第二步：规范化新闻数据...")
    news_list, normalize_stats = normalize_news(raw_news, max_items=200)
    logger.info(f"规范化完成，共 {len(news_list)} 条有效新闻")
    stats["normalize_stats"] = normalize_stats

    if not news_list:
        logger.error("规范化后无有效新闻，测试终止")
        return None, stats

    # ============================================
    # 第三步：原文抓取（Mock）
    # ============================================
    logger.info("\n第三步：原文抓取（Mock）...")
    fetch_stats = {"total": 0, "success": 0, "failed": 0}

    for news in news_list:
        fetch_stats["total"] += 1
        try:
            mock_fetch_article(news)
            fetch_stats["success"] += 1
        except Exception as e:
            fetch_stats["failed"] += 1
            logger.error(f"Mock 抓取失败: {e}")

    stats["fetch_stats"] = fetch_stats
    logger.info(f"Mock 抓取完成: 成功 {fetch_stats['success']}/{fetch_stats['total']}")

    # ============================================
    # 第四步：流程处理（去重→合并）
    # ============================================
    logger.info("\n第四步：去重与合并...")
    processor = SearchResultProcessor(similarity_threshold=0.6)
    processed_news, pipeline_stats = processor.process_search_results(news_list)
    logger.info(f"处理完成，输出 {len(processed_news)} 条新闻")
    stats["pipeline_stats"] = pipeline_stats

    if not processed_news:
        logger.error("处理后无有效新闻，测试终止")
        return None, stats

    # ============================================
    # 第五步：轻量化特征抽取（简化版 Mock）
    # ============================================
    logger.info("\n第五步：轻量化特征抽取（Mock）...")
    light_stats = {"total": 0, "success": 0}

    for news in processed_news:
        light_stats["total"] += 1
        content = news.get("fetched_content", news.get("content", ""))

        # Mock 轻量化特征
        news["light_features"] = {
            "content_length": len(content),
            "has_numbers": bool(random.random() > 0.3),  # 70% 概率有数字
            "has_quote": bool(random.random() > 0.5),     # 50% 概率有引用
            "company_count": random.randint(1, 5),
            "signal_term_count": random.randint(0, 8)
        }
        light_stats["success"] += 1

    stats["light_features_stats"] = light_stats
    logger.info(f"轻量化特征抽取完成: {light_stats['success']}/{light_stats['total']}")

    # ============================================
    # 第六步：新闻选择（评分→排序→选择）
    # ============================================
    logger.info("\n第六步：新闻选择...")
    selector = NewsSelectorPipeline(top_k=TOP_K_SELECT)
    final_news, select_stats = selector.select_news(processed_news)
    logger.info(f"选择完成，输出 {len(final_news)} 条新闻")
    stats["select_stats"] = select_stats

    if not final_news:
        logger.error("选择后无有效新闻，测试终止")
        return None, stats

    # ============================================
    # 第七步：投资信息抽取（Mock LLM 结果）
    # ============================================
    logger.info("\n第七步：投资信息抽取（Mock LLM）...")
    extract_stats = {"total": 0, "success": 0}

    for news in final_news:
        extract_stats["total"] += 1

        # Mock 投资信息
        news["investment_info"] = {
            "core_thesis": f"关于 {news.get('title', '')[:30]} 的投资分析",
            "market_impact": random.choice(["积极影响", "中性影响", "需要观察"]),
            "risk_factors": [
                random.choice(["市场竞争", "技术风险", "监管风险", "执行风险"]),
                random.choice(["估值过高", "盈利能力", "现金流", "人才流失"])
            ],
            "time_horizon": random.choice(["短期", "中期", "长期"]),
            "related_tickers": random.sample(["NVDA", "MSFT", "GOOGL", "META", "AMZN", "AMD", "INTC"], k=random.randint(1, 3)),
            "confidence_level": random.choice(["高", "中", "低"])
        }
        news["ai_summary"] = f"这是一条关于 AI 行业的重要新闻。{news['content'][:100]}..."
        extract_stats["success"] += 1

    stats["investment_extract_stats"] = extract_stats
    logger.info(f"投资信息抽取完成: {extract_stats['success']}/{extract_stats['total']}")

    # ============================================
    # 第八步：事件分析（嵌入→聚类→摘要）
    # ============================================
    logger.info("\n第八步：事件分析...")
    try:
        event_pipeline = EventPipeline()
        events, event_stats = event_pipeline.analyze_events(final_news)
        logger.info(f"事件分析完成，检测到 {len(events)} 个事件")
        stats["event_stats"] = event_stats
    except Exception as e:
        logger.error(f"事件分析失败: {e}", exc_info=True)
        # 如果事件分析失败，创建 mock 事件
        events = []
        for i in range(min(5, len(final_news))):
            events.append({
                "representative_title": final_news[i].get("title", f"Mock 事件 {i + 1}"),
                "summary": final_news[i].get("ai_summary", "这是一个 Mock 事件摘要"),
                "news_count": random.randint(1, 5),
                "sources": [final_news[i].get("source", "Mock Source")],
                "companies": random.sample(COMPANIES[:10], k=random.randint(1, 3)),
                "news_indices": [i]
            })
        stats["event_stats"] = {"mock": True, "events_count": len(events)}

    # ============================================
    # 第九步：事件决策
    # ============================================
    logger.info("\n第九步：事件决策...")
    try:
        decision_pipeline = EventDecisionPipeline()
        events_with_decision, decision_stats = decision_pipeline.decide_with_stats(events)
        logger.info(f"事件决策完成，为 {len(events_with_decision)} 个事件生成决策")
        stats["decision_stats"] = decision_stats
        events = events_with_decision
    except Exception as e:
        logger.error(f"事件决策失败: {e}", exc_info=True)
        # Mock 决策
        for event in events:
            event["decision"] = {
                "importance": random.choice(["High", "Medium", "Low"]),
                "signal": random.choice(["Positive", "Neutral", "Risk"]),
                "action": random.choice(["Watch", "Hold", "Avoid"])
            }
        stats["decision_stats"] = {"mock": True}

    # ============================================
    # 第十步：公众号文章生成
    # ============================================
    logger.info("\n第十步：公众号文章生成...")
    try:
        article_builder = ArticleBuilder()
        article = article_builder.build(events)

        renderer = MarkdownRenderer()
        article_content = renderer.render(article)

        # 保存文章
        output_dir = os.path.join(PROJECT_ROOT, "output")
        os.makedirs(output_dir, exist_ok=True)

        # 使用固定的 Mock 日期
        date_str = "20260606"
        filename = f"mock_ai_invest_article_{date_str}.md"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(article_content)

        logger.info(f"公众号文章已保存到: {file_path}")
        stats["article_stats"] = {"success": True, "file_path": file_path}
    except Exception as e:
        logger.error(f"公众号文章生成失败: {e}", exc_info=True)
        stats["article_stats"] = {"error": str(e)}

    # ============================================
    # 第十一步：H5 应用数据导出
    # ============================================
    logger.info("\n第十一步：H5 应用数据导出...")

    # 构建结果数据（使用固定的 Mock 日期）
    mock_date = "2026-06-06"
    result = {
        "date": mock_date,
        "news": final_news,
        "events": events
    }

    try:
        export_result = export_to_webapp(result, stats)

        if export_result.get("success"):
            logger.info("H5 应用数据导出成功!")
            logger.info(f"  数据文件: {export_result.get('data_file')}")
            logger.info(f"  索引文件: {export_result.get('index_file')}")
            stats["webapp_export_stats"] = {
                "success": True,
                "data_file": export_result.get("data_file"),
                "index_file": export_result.get("index_file")
            }
        else:
            logger.error(f"H5 应用数据导出失败: {export_result.get('error')}")
            stats["webapp_export_stats"] = {"success": False, "error": export_result.get("error")}
    except Exception as e:
        logger.error(f"H5 应用数据导出异常: {e}", exc_info=True)
        stats["webapp_export_stats"] = {"error": str(e)}

    return result, stats


def main():
    """主函数"""
    try:
        result, stats = run_full_flow_test()

        print("\n" + "=" * 60)
        print("全流程测试完成")
        print("=" * 60)

        if result:
            print(f"\n日期: {result.get('date')}")
            print(f"最终新闻数量: {len(result.get('news', []))}")
            print(f"事件数量: {len(result.get('events', []))}")

            print("\n【事件列表】")
            for i, event in enumerate(result.get("events", [])[:5], 1):
                print(f"\n事件 {i}:")
                print(f"  标题: {event.get('representative_title', 'N/A')[:60]}...")
                print(f"  新闻数量: {event.get('news_count', 0)}")
                decision = event.get("decision", {})
                if decision:
                    print(f"  决策: {decision.get('importance')} | {decision.get('signal')} | {decision.get('action')}")

        print("\n【流程统计】")
        print(f"Mock 数据: {stats.get('mock_data_count', 0)} 条")
        print(f"规范化后: {sum(stats.get('normalize_stats', {}).values())} 条")

        pipeline_stats = stats.get("pipeline_stats", {})
        if pipeline_stats:
            print(f"去重后: {pipeline_stats.get('step1_dedup', {}).get('kept_count', 0)} 条")
            print(f"合并后: {pipeline_stats.get('step2_merge', {}).get('output_count', 0)} 条")

        print(f"选择后: {stats.get('select_stats', {}).get('output_count', 0)} 条")
        print(f"事件数: {stats.get('event_stats', {}).get('valid_events', 0)} 个")

        webapp_stats = stats.get("webapp_export_stats", {})
        if webapp_stats.get("success"):
            print(f"\n✅ H5 应用数据已导出:")
            print(f"  数据文件: {webapp_stats.get('data_file')}")
            print(f"  索引文件: {webapp_stats.get('index_file')}")
            print(f"\n🌐 请访问 http://localhost:8080 查看测试结果")

        logger.info("=" * 60)
        logger.info("测试完成")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
