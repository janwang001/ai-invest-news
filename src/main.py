#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI投资新闻分析主程序

集成搜索、处理、选择、事件分析和投资信息抽取的完整流程。
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, List

from search import SearchPipeline
from search.search_result_process import normalize_news
from selector.news_selector import NewsSelectorPipeline
from search.rss_config import MAX_NORMALIZED_ITEMS
from selector.selector_config import TOP_K_SELECT
from event.event_pipeline import EventPipeline
from event.decision import EventDecisionPipeline
from content import ArticleBuilder, MarkdownRenderer
from fetch import ArticleFetcher, InvestmentExtractor, LightFeaturesExtractor
from webapp_exporter import export_to_webapp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_ai_news(hours: int = 24) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    生成 AI 投资新闻分析结果。

    完整流程（11步）：
    1. 搜索最近新闻（使用SearchPipeline）
    2. 规范化新闻数据
    3. 原文抓取（ArticleFetcher）
    4. 处理搜索结果（去重→合并相似新闻）
    5. 轻量化特征抽取（LightFeaturesExtractor）
    6. 新闻选择（质量评分→排序→选择前k）
    7. 投资信息抽取（InvestmentExtractor，使用LLM）
    8. 事件分析（嵌入→聚类→摘要生成）
    9. 事件决策（重要性评估→信号分类→动作映射）
    10. 公众号文章生成（事件排序→分类→渲染）
    11. H5应用数据导出（JSON格式）

    Args:
        hours: 搜索的时间范围（小时），默认 24 小时

    Returns:
        tuple: (result_dict, stats_dict)
            - result_dict: 包含日期、新闻列表和事件列表的字典
            - stats_dict: 包含各阶段的统计信息
    """
    logger.info("=" * 50)
    logger.info("开始生成 AI 投资新闻")
    logger.info("=" * 50)

    stats = {}  # 整体统计信息
    result = {"date": datetime.now().strftime("%Y-%m-%d"), "news": []}

    try:
        # ============================================
        # 第一步：使用SearchPipeline搜索最近新闻
        # ============================================
        logger.info("第一步：使用SearchPipeline搜索最近新闻...")
        pipeline = SearchPipeline(hours=hours)
        raw_news, search_stats = pipeline.search_recent_ai_news()
        logger.info(f"搜索完成，获取 {len(raw_news)} 条原始新闻")
        stats["search_stats"] = search_stats

        # ============================================
        # 第二步：规范化新闻
        # ============================================
        logger.info("第二步：规范化新闻数据...")
        news_list, normalize_stats = normalize_news(raw_news, max_items=MAX_NORMALIZED_ITEMS)
        logger.info(f"规范化完成，共 {len(news_list)} 条有效新闻（最大限制: {MAX_NORMALIZED_ITEMS} 条）")
        stats["normalize_stats"] = normalize_stats

        if not news_list:
            logger.warning("未获得有效新闻，返回空结果")
            return result, stats

        # ============================================
        # 第三步：原文抓取（提前抓取，供后续步骤使用）
        # ============================================
        logger.info("第三步：原文抓取（ArticleFetcher）...")
        news_list = _fetch_articles(news_list, stats)

        # ============================================
        # 第四步：流程处理（去重→合并）
        # ============================================
        logger.info("第四步：使用SearchPipeline处理搜索结果（去重→合并相似新闻）...")
        # 注意：skip_normalize=True，因为第二步已经规范化过了，避免丢失第三步添加的字段
        processed_news, pipeline_stats = pipeline.process_results(news_list, skip_normalize=True)
        logger.info(f"流程处理完成，输出 {len(processed_news)} 条新闻")
        stats["pipeline_stats"] = pipeline_stats

        if not processed_news:
            logger.warning("流程处理后无有效新闻，返回空结果")
            return result, stats

        # ============================================
        # 第五步：轻量化特征抽取（不用LLM）
        # ============================================
        logger.info("第五步：轻量化特征抽取（LightFeaturesExtractor）...")
        processed_news = _extract_light_features(processed_news, stats)

        # ============================================
        # 第六步：新闻选择（质量评分→排序→选择前k）
        # ============================================
        logger.info("第六步：新闻选择（质量评分→排序→选择前k）...")
        selector = NewsSelectorPipeline(top_k=TOP_K_SELECT)
        final_news, select_stats = selector.select_news(processed_news)
        logger.info(f"选择完成，输出 {len(final_news)} 条新闻")
        stats["select_stats"] = select_stats

        if not final_news:
            logger.warning("选择后无有效新闻，返回空结果")
            return result, stats

        # ============================================
        # 第七步：投资信息抽取（使用LLM）
        # ============================================
        logger.info("第七步：投资信息抽取（InvestmentExtractor，使用LLM）...")
        final_news = _extract_investment_info(final_news, stats)

        # ============================================
        # 第八步：事件分析（嵌入→聚类→摘要）
        # ============================================
        logger.info("第八步：事件分析流程（嵌入→聚类→摘要）...")
        events = _analyze_events(final_news, stats)

        # ============================================
        # 第九步：事件决策（重要性评估→信号分类→动作映射）
        # ============================================
        logger.info("第九步：事件决策流程（重要性评估→信号分类→动作映射）...")
        events = _make_decisions(events, stats)

        # ============================================
        # 第十步：公众号文章生成（事件排序→分类→渲染）
        # ============================================
        logger.info("第十步：公众号文章生成流程（事件排序→分类→渲染）...")
        _generate_article(events, stats)

        # 添加事件分析结果到最终输出
        if events:
            result["events"] = events
            result["news"] = final_news
            logger.info(f"已将 {len(events)} 个事件分析结果添加到最终输出")

        # ============================================
        # 第十一步：H5应用数据导出
        # ============================================
        logger.info("第十一步：H5应用数据导出...")
        _export_webapp_data(result, stats)

        return result, stats

    except Exception as e:
        logger.error(f"生成 AI 新闻失败: {e}", exc_info=True)
        raise


def _fetch_articles(news_list: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    第三步：原文抓取

    Args:
        news_list: 新闻列表
        stats: 统计信息字典

    Returns:
        带有抓取内容的新闻列表
    """
    try:
        fetcher = ArticleFetcher()
        fetch_stats = {"total": 0, "success": 0, "failed": 0}

        for news in news_list:
            url = news.get("url", "")
            if not url:
                continue

            fetch_stats["total"] += 1

            # 抓取原文
            fetch_result = fetcher.fetch(url)
            if fetch_result and fetch_result.content:
                fetch_stats["success"] += 1
                # 将抓取的内容存储到新闻中
                news["fetched_content"] = fetch_result.content
                news["fetched_title"] = fetch_result.title
                news["fetch_stats"] = fetch_result.stats
            else:
                fetch_stats["failed"] += 1
                news["fetched_content"] = ""

        stats["fetch_stats"] = fetch_stats
        logger.info(
            f"原文抓取完成: 总计 {fetch_stats['total']} 条，"
            f"成功 {fetch_stats['success']} 条，"
            f"失败 {fetch_stats['failed']} 条"
        )
    except Exception as e:
        logger.error(f"原文抓取失败: {e}", exc_info=True)
        stats["fetch_stats"] = {"error": str(e)}

    return news_list


def _extract_light_features(news_list: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    第五步：轻量化特征抽取

    Args:
        news_list: 新闻列表
        stats: 统计信息字典

    Returns:
        带有轻量化特征的新闻列表
    """
    try:
        extractor = LightFeaturesExtractor()
        light_stats = {"total": 0, "success": 0, "failed": 0}

        for news in news_list:
            # 优先使用抓取的内容，其次使用原始内容
            content = news.get("fetched_content", news.get("content", ""))
            title = news.get("title", "")

            if not content:
                continue

            light_stats["total"] += 1

            # 提取轻量化特征
            features = extractor.extract(content, title)
            if features.extraction_success:
                light_stats["success"] += 1
                news["light_features"] = features.to_dict()
            else:
                light_stats["failed"] += 1
                news["light_features"] = {}

        stats["light_features_stats"] = light_stats
        logger.info(
            f"轻量化特征抽取完成: 总计 {light_stats['total']} 条，"
            f"成功 {light_stats['success']} 条，"
            f"失败 {light_stats['failed']} 条"
        )
    except Exception as e:
        logger.error(f"轻量化特征抽取失败: {e}", exc_info=True)
        stats["light_features_stats"] = {"error": str(e)}

    return news_list


def _extract_investment_info(news_list: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    第七步：投资信息抽取（使用LLM）

    Args:
        news_list: 新闻列表
        stats: 统计信息字典

    Returns:
        带有投资信息的新闻列表
    """
    try:
        extractor = InvestmentExtractor()
        extract_stats = {"total": 0, "success": 0, "failed": 0}

        for news in news_list:
            # 优先使用抓取的内容
            content = news.get("fetched_content", news.get("content", ""))
            url = news.get("url", "")
            title = news.get("title", "")

            if not content:
                continue

            extract_stats["total"] += 1

            # 投资信息抽取
            extract_result = extractor.extract(content, url, title, save_to_disk=False)
            if extract_result and extract_result.success and extract_result.investment_info:
                extract_stats["success"] += 1
                news["investment_info"] = extract_result.investment_info.to_dict()
                news["ai_summary"] = extract_result.investment_info.ai_summary
            else:
                extract_stats["failed"] += 1

        stats["investment_extract_stats"] = extract_stats
        logger.info(
            f"投资信息抽取完成: 总计 {extract_stats['total']} 条，"
            f"成功 {extract_stats['success']} 条，"
            f"失败 {extract_stats['failed']} 条"
        )
    except Exception as e:
        logger.error(f"投资信息抽取失败: {e}", exc_info=True)
        stats["investment_extract_stats"] = {"error": str(e)}

    return news_list


def _analyze_events(news_list: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    第八步：事件分析

    Args:
        news_list: 新闻列表
        stats: 统计信息字典

    Returns:
        事件列表
    """
    events = []
    try:
        event_pipeline = EventPipeline()
        events, event_stats = event_pipeline.analyze_events(news_list)
        logger.info(f"事件分析完成，检测到 {len(events)} 个事件")
        stats["event_stats"] = event_stats
    except Exception as e:
        logger.error(f"事件分析失败: {e}", exc_info=True)
        stats["event_stats"] = {"error": str(e)}

    return events


def _make_decisions(events: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    第九步：事件决策

    Args:
        events: 事件列表
        stats: 统计信息字典

    Returns:
        带决策的事件列表
    """
    try:
        decision_pipeline = EventDecisionPipeline()
        events_with_decision, decision_stats = decision_pipeline.decide_with_stats(events)
        logger.info(f"事件决策完成，为 {len(events_with_decision)} 个事件生成决策")
        stats["decision_stats"] = decision_stats
        return events_with_decision
    except Exception as e:
        logger.error(f"事件决策失败: {e}", exc_info=True)
        stats["decision_stats"] = {"error": str(e)}
        return events


def _generate_article(events: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
    """
    第十步：公众号文章生成

    Args:
        events: 事件列表
        stats: 统计信息字典
    """
    try:
        article_builder = ArticleBuilder()
        article = article_builder.build(events)
        logger.info(f"公众号文章构建完成，包含 {len(article.events)} 个事件")

        # 渲染为Markdown格式
        renderer = MarkdownRenderer()
        article_content = renderer.render(article)
        logger.info("公众号文章渲染完成")

        # 保存文章内容到文件
        article_file_path = _save_article_to_file(article_content)
        logger.info(f"公众号文章已保存到: {article_file_path}")

        stats["article_stats"] = {
            "total_events": len(article.events),
            "article_generated": True,
            "file_path": article_file_path
        }
    except Exception as e:
        logger.error(f"公众号文章生成失败: {e}", exc_info=True)
        stats["article_stats"] = {"error": str(e)}


def _save_article_to_file(article_content: str) -> str:
    """
    保存公众号文章到文件

    Args:
        article_content: 文章内容（Markdown格式）

    Returns:
        str: 保存的文件路径
    """
    import os

    # 创建output目录
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"ai_invest_article_{date_str}.md"
    file_path = os.path.join(output_dir, filename)

    # 保存文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(article_content)

    return file_path


def _export_webapp_data(result: Dict[str, Any], stats: Dict[str, Any]) -> None:
    """
    第十一步：H5应用数据导出

    Args:
        result: 分析结果
        stats: 统计信息字典
    """
    try:
        export_result = export_to_webapp(result, stats)
        if export_result.get("success"):
            logger.info(f"H5应用数据导出成功: {export_result.get('data_file')}")
            stats["webapp_export_stats"] = {
                "success": True,
                "data_file": export_result.get("data_file"),
                "index_file": export_result.get("index_file"),
            }
        else:
            logger.warning(f"H5应用数据导出失败: {export_result.get('error')}")
            stats["webapp_export_stats"] = {
                "success": False,
                "error": export_result.get("error"),
            }
    except Exception as e:
        logger.error(f"H5应用数据导出失败: {e}", exc_info=True)
        stats["webapp_export_stats"] = {"error": str(e)}


def main():
    """主函数"""
    try:
        result, stats = generate_ai_news(hours=24)

        print("\n" + "=" * 50)
        print("AI 投资新闻分析结果")
        print("=" * 50)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 输出统计信息
        print("\n" + "=" * 50)
        print("数据源统计信息")
        print("=" * 50)

        search_stats = stats.get("search_stats", {})

        # 获取源详情和分类统计
        source_classification = search_stats.get("source_classification", {})

        print("\n【源分类统计】")
        if source_classification:
            valid_count = len(source_classification.get("valid_sources", []))
            expired_count = len(source_classification.get("expired_sources", []))
            invalid_count = len(source_classification.get("invalid_sources", []))

            print(f"✓ 有效源（有搜索结果且有未过期新闻）: {valid_count} 个")
            if valid_count > 0:
                for source in source_classification.get("valid_sources", []):
                    print(f"    - {source}")

            print(f"\n⏱ 过期源（有搜索结果但都是过期新闻）: {expired_count} 个")
            if expired_count > 0:
                for source in source_classification.get("expired_sources", []):
                    print(f"    - {source}")

            print(f"\n✗ 无效源（没有搜索结果）: {invalid_count} 个")
            if invalid_count > 0:
                invalid_list = source_classification.get("invalid_sources", [])
                if len(invalid_list) <= 5:
                    for source in invalid_list:
                        print(f"    - {source}")
                else:
                    for source in invalid_list[:5]:
                        print(f"    - {source}")
                    print(f"    ... 及其他 {len(invalid_list) - 5} 个源")

        print("\n【搜索阶段统计】")
        total_found = 0
        total_fetched = 0
        sources_detail = search_stats.get("sources", {})
        for source, stat in sources_detail.items():
            if isinstance(stat, dict):
                print(f"\n{source}:")
                print(f"  总找到: {stat['total_found']} 条")
                print(f"  有效获取: {stat['valid_fetched']} 条")
                print(f"  跳过(无时间): {stat['skipped_no_time']} 条")
                print(f"  跳过(过期): {stat['skipped_too_old']} 条")
                total_found += stat['total_found']
                total_fetched += stat['valid_fetched']

        print(f"\n搜索总计: 找到 {total_found} 条，有效获取 {total_fetched} 条")

        normalize_stats = stats.get("normalize_stats", {})
        print("\n【规范化阶段统计】")
        for source, count in normalize_stats.items():
            print(f"{source}: {count} 条")

        total_output = sum(normalize_stats.values()) if normalize_stats else 0
        print(f"\n最终输出: {total_output} 条（最大限制: {MAX_NORMALIZED_ITEMS} 条）")

        # 显示原文抓取统计
        fetch_stats = stats.get("fetch_stats", {})
        if fetch_stats and not fetch_stats.get("error"):
            print("\n【原文抓取统计】")
            print(f"总计: {fetch_stats.get('total', 0)} 条")
            print(f"成功: {fetch_stats.get('success', 0)} 条")
            print(f"失败: {fetch_stats.get('failed', 0)} 条")

        # 显示流程处理统计（去重→合并）
        pipeline_stats = stats.get("pipeline_stats", {})
        if pipeline_stats:
            print("\n【流程处理统计（去重→合并）】")
            print(f"输入（规范化后的新闻）: {pipeline_stats.get('input_count', 0)} 条")

            step1 = pipeline_stats.get('step1_dedup', {})
            if step1:
                print(f"去重后: {step1.get('kept_count', 0)} 条（移除: {step1.get('removed_count', 0)} 条）")

            step2 = pipeline_stats.get('step2_merge', {})
            if step2:
                print(f"合并后: {step2.get('output_count', 0)} 条（合并: {step2.get('merged_count', 0)} 条）")

        # 显示轻量化特征统计
        light_stats = stats.get("light_features_stats", {})
        if light_stats and not light_stats.get("error"):
            print("\n【轻量化特征抽取统计】")
            print(f"总计: {light_stats.get('total', 0)} 条")
            print(f"成功: {light_stats.get('success', 0)} 条")
            print(f"失败: {light_stats.get('failed', 0)} 条")

        # 显示新闻选择统计（评分→排序→选择）
        select_stats = stats.get("select_stats", {})
        if select_stats:
            print("\n【新闻选择统计（评分→排序→选择）】")
            print(f"输入（去重合并后的新闻）: {select_stats.get('input_count', 0)} 条")
            print(f"带轻量化特征: {select_stats.get('light_features_count', 0)} 条")
            print(f"输出（选择前k条）: {select_stats.get('output_count', 0)} 条（最多: {select_stats.get('top_k', 5)} 条）")

        # 显示投资信息抽取统计
        invest_stats = stats.get("investment_extract_stats", {})
        if invest_stats and not invest_stats.get("error"):
            print("\n【投资信息抽取统计（LLM）】")
            print(f"总计: {invest_stats.get('total', 0)} 条")
            print(f"成功: {invest_stats.get('success', 0)} 条")
            print(f"失败: {invest_stats.get('failed', 0)} 条")

        # 显示事件分析统计（嵌入→聚类→摘要）
        event_stats = stats.get("event_stats", {})
        if event_stats and not event_stats.get("error"):
            print("\n【事件分析统计（嵌入→聚类→摘要）】")
            print(f"输入新闻总数: {event_stats.get('total_news', 0)} 条")
            print(f"检测到聚类数量: {event_stats.get('clusters_detected', 0)} 个")
            print(f"有效事件数量: {event_stats.get('valid_events', 0)} 个")
            print(f"生成事件摘要: {event_stats.get('events_summarized', 0)} 个")

            if event_stats.get('total_news_in_events', 0) > 0:
                coverage_rate = event_stats.get('coverage_rate', 0) * 100
                print(f"事件覆盖率: {coverage_rate:.1f}%")

        # 显示事件决策统计
        decision_stats = stats.get("decision_stats", {})
        if decision_stats and not decision_stats.get("error"):
            print("\n【事件决策统计】")
            print(f"输入事件总数: {decision_stats.get('total_events', 0)} 个")
            success_rate = decision_stats.get('success_rate', 0) * 100
            print(f"决策成功率: {success_rate:.1f}%")

            # 显示分布
            importance_dist = decision_stats.get('importance_distribution', {})
            if importance_dist:
                print(f"重要性分布: {importance_dist}")

            signal_dist = decision_stats.get('signal_distribution', {})
            if signal_dist:
                print(f"信号分布: {signal_dist}")

            action_dist = decision_stats.get('action_distribution', {})
            if action_dist:
                print(f"动作分布: {action_dist}")

        # 显示最终结果中的事件信息
        if result.get("events"):
            print("\n【事件分析结果】")
            events = result.get("events", [])
            print(f"共检测到 {len(events)} 个事件：")
            for i, event in enumerate(events, 1):
                print(f"\n事件 {i}:")
                print(f"  标题: {event.get('representative_title', 'N/A')}")
                print(f"  新闻数量: {event.get('news_count', 0)} 条")
                print(f"  来源: {', '.join(event.get('sources', []))}")
                decision = event.get('decision', {})
                if decision:
                    print(f"  决策: {decision.get('importance', 'N/A')} / {decision.get('signal', 'N/A')} / {decision.get('action', 'N/A')}")

        logger.info("=" * 50)
        logger.info("程序执行成功")
        logger.info("=" * 50)

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        print(f"错误: {e}")
        exit(1)
    except RuntimeError as e:
        logger.error(f"运行时错误: {e}")
        print(f"错误: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        print(f"错误: {e}")
        exit(1)


if __name__ == "__main__":
    main()
