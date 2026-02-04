#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SearchPipeline v2 - 支持并发和串行两种抓取模式

新特性:
- 支持并发RSS抓取（默认启用，性能提升60-80%）
- 兼容原有串行模式
- 统一的API接口
- 详细的性能统计
"""

import logging
from typing import List, Dict, Tuple

# 导入配置
try:
    from .rss_config import RSS_SOURCES, MAX_ITEMS_PER_SOURCE, SEARCH_HOURS, MAX_NORMALIZED_ITEMS
    from .search_result_process import SearchResultProcessor
    from .concurrent_rss_fetcher import ConcurrentRSSFetcher
except ImportError:
    from rss_config import RSS_SOURCES, MAX_ITEMS_PER_SOURCE, SEARCH_HOURS, MAX_NORMALIZED_ITEMS
    from search_result_process import SearchResultProcessor
    from concurrent_rss_fetcher import ConcurrentRSSFetcher


class SearchPipelineV2:
    """搜索结果处理流程管道类 v2 - 支持并发抓取"""

    def __init__(
        self,
        hours: int = SEARCH_HOURS,
        max_items_per_source: int = MAX_ITEMS_PER_SOURCE,
        use_concurrent: bool = True,  # 是否使用并发抓取
        max_concurrent: int = 10  # 最大并发数
    ):
        """
        初始化搜索管道

        Args:
            hours: 搜索的时间范围（小时），默认 24 小时
            max_items_per_source: 每个源最大条数，默认 20 条
            use_concurrent: 是否使用并发抓取（默认True）
            max_concurrent: 最大并发数（默认10）
        """
        self.hours = hours
        self.max_items_per_source = max_items_per_source
        self.use_concurrent = use_concurrent
        self.max_concurrent = max_concurrent
        self.logger = self._setup_logger()

        # 初始化抓取器
        if use_concurrent:
            self.logger.info("使用并发RSS抓取模式")
            self.fetcher = ConcurrentRSSFetcher(
                hours=hours,
                max_items_per_source=max_items_per_source,
                max_concurrent=max_concurrent
            )
        else:
            self.logger.info("使用串行RSS抓取模式")
            # 导入原始串行版本
            try:
                from .search_pipeline import SearchPipeline as SerialPipeline
            except ImportError:
                from search_pipeline import SearchPipeline as SerialPipeline
            self.fetcher = SerialPipeline(
                hours=hours,
                max_items_per_source=max_items_per_source
            )

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def search_recent_ai_news(self) -> Tuple[List[Dict], Dict]:
        """
        搜索指定时间内的最近 AI 相关新闻。

        Returns:
            tuple: (news_list, stats_dict)
        """
        self.logger.info(f"开始搜索最近 {self.hours} 小时的 AI 新闻")
        self.logger.info(f"抓取模式: {'并发' if self.use_concurrent else '串行'}")

        if self.use_concurrent:
            # 使用并发抓取
            return self.fetcher.fetch_rss_sync()
        else:
            # 使用串行抓取
            return self.fetcher.search_recent_ai_news()

    def process_results(
        self,
        raw_news: List[Dict],
        max_normalized_items: int = MAX_NORMALIZED_ITEMS,
        skip_normalize: bool = False
    ) -> Tuple[List[Dict], Dict]:
        """
        处理搜索结果：规范化 -> 去重 -> 合并相似

        Args:
            raw_news: 原始新闻列表
            max_normalized_items: 规范化输出的最大条数
            skip_normalize: 是否跳过规范化步骤

        Returns:
            tuple: (processed_news, pipeline_stats)
        """
        self.logger.info("=" * 50)
        self.logger.info("开始搜索结果处理流程")
        self.logger.info("=" * 50)

        pipeline_stats = {
            "input_count": len(raw_news),
            "step1_normalize": {},
            "step2_dedup": {},
            "step3_merge": {},
            "output_count": 0
        }

        try:
            processor = SearchResultProcessor(max_items=max_normalized_items)

            # 步骤1：规范化
            if skip_normalize:
                self.logger.info(f"【步骤1】规范化 - 已跳过: {len(raw_news)} 条")
                normalized_news = raw_news
                pipeline_stats["step1_normalize"] = {"skipped": True, "count": len(raw_news)}
            else:
                self.logger.info(f"【步骤1】规范化 - 输入: {len(raw_news)} 条")
                normalized_news, normalize_stats = processor.normalize_news(raw_news)
                pipeline_stats["step1_normalize"] = normalize_stats
                self.logger.info(f"规范化完成 - 输出: {len(normalized_news)} 条")

            if not normalized_news:
                self.logger.warning("规范化后无有效新闻")
                return [], pipeline_stats

            # 步骤2：去重
            self.logger.info(f"【步骤2】去重 - 输入: {len(normalized_news)} 条")
            dedup_news, dedup_stats = processor.deduplicate_news(normalized_news)
            pipeline_stats["step2_dedup"] = dedup_stats
            self.logger.info(
                f"去重完成 - 输出: {len(dedup_news)} 条，"
                f"移除: {dedup_stats.get('removed_count', 0)} 条"
            )

            if not dedup_news:
                self.logger.warning("去重后无有效新闻")
                return [], pipeline_stats

            # 步骤3：合并相似
            self.logger.info(f"【步骤3】合并相似 - 输入: {len(dedup_news)} 条")
            merged_news, merge_stats = processor.merge_similar_news(dedup_news)
            pipeline_stats["step3_merge"] = merge_stats
            self.logger.info(
                f"合并完成 - 输出: {len(merged_news)} 条，"
                f"合并: {merge_stats.get('merged_count', 0)} 条"
            )

            if not merged_news:
                self.logger.warning("合并后无有效新闻")
                return [], pipeline_stats

            pipeline_stats["output_count"] = len(merged_news)

            # 输出流程总结
            self.logger.info("=" * 50)
            self.logger.info("处理流程完成")
            self.logger.info("=" * 50)
            self.logger.info(f"原始输入: {pipeline_stats['input_count']} 条")
            if not skip_normalize:
                self.logger.info(f"规范化后: {len(normalized_news)} 条")
            self.logger.info(
                f"去重后: {len(dedup_news)} 条 "
                f"(移除: {dedup_stats.get('removed_count', 0)} 条)"
            )
            self.logger.info(
                f"合并后: {len(merged_news)} 条 "
                f"(合并: {merge_stats.get('merged_count', 0)} 条)"
            )

            return merged_news, pipeline_stats

        except Exception as e:
            self.logger.error(f"处理流程失败: {e}", exc_info=True)
            raise

    def run_pipeline(self) -> Tuple[List[Dict], Dict]:
        """
        运行完整的搜索处理管道

        Returns:
            tuple: (processed_news, combined_stats)
        """
        self.logger.info("=" * 50)
        self.logger.info("开始运行完整搜索处理管道 v2")
        self.logger.info("=" * 50)

        # 步骤1：搜索新闻
        raw_news, search_stats = self.search_recent_ai_news()

        if not raw_news:
            self.logger.warning("搜索阶段未找到任何新闻")
            return [], {"search": search_stats, "processing": {}}

        # 步骤2：处理结果
        processed_news, process_stats = self.process_results(raw_news)

        combined_stats = {
            "search": search_stats,
            "processing": process_stats
        }

        self.logger.info("=" * 50)
        self.logger.info("完整管道运行完成")
        self.logger.info("=" * 50)
        self.logger.info(f"搜索阶段: {len(raw_news)} 条新闻")
        self.logger.info(f"处理阶段: {len(processed_news)} 条最终结果")

        # 输出性能统计（如果使用并发模式）
        if self.use_concurrent and "performance" in search_stats:
            perf = search_stats["performance"]
            self.logger.info("=" * 50)
            self.logger.info("性能统计")
            self.logger.info("=" * 50)
            self.logger.info(f"总耗时: {perf['total_time']:.2f}s")
            self.logger.info(f"平均每源: {perf['avg_time_per_source']:.2f}s")
            self.logger.info(
                f"成功/失败: {perf['successful_fetches']}/{perf['failed_fetches']}"
            )

        return processed_news, combined_stats


def main():
    """测试函数"""
    import time

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("\n" + "=" * 70)
    print("SearchPipeline v2 测试 - 并发 vs 串行")
    print("=" * 70)

    # 测试1：并发模式
    print("\n【测试1】并发模式")
    print("-" * 70)
    start_time = time.time()
    pipeline_concurrent = SearchPipelineV2(
        hours=24,
        max_items_per_source=5,
        use_concurrent=True,
        max_concurrent=10
    )
    news_concurrent, stats_concurrent = pipeline_concurrent.run_pipeline()
    time_concurrent = time.time() - start_time

    print(f"\n✓ 并发模式完成")
    print(f"  - 耗时: {time_concurrent:.2f}s")
    print(f"  - 获取新闻: {len(news_concurrent)} 条")

    # 测试2：串行模式
    print("\n【测试2】串行模式")
    print("-" * 70)
    start_time = time.time()
    pipeline_serial = SearchPipelineV2(
        hours=24,
        max_items_per_source=5,
        use_concurrent=False
    )
    news_serial, stats_serial = pipeline_serial.run_pipeline()
    time_serial = time.time() - start_time

    print(f"\n✓ 串行模式完成")
    print(f"  - 耗时: {time_serial:.2f}s")
    print(f"  - 获取新闻: {len(news_serial)} 条")

    # 性能对比
    print("\n" + "=" * 70)
    print("性能对比结果")
    print("=" * 70)
    improvement = (time_serial - time_concurrent) / time_serial * 100
    speedup = time_serial / time_concurrent

    print(f"串行模式耗时: {time_serial:.2f}s")
    print(f"并发模式耗时: {time_concurrent:.2f}s")
    print(f"性能提升: {improvement:.1f}%")
    print(f"加速比: {speedup:.2f}x")
    print(f"节省时间: {time_serial - time_concurrent:.2f}s")

    # 显示前3条新闻
    print("\n获取的新闻示例（前3条）:")
    for idx, item in enumerate(news_concurrent[:3], 1):
        print(f"[{idx}] {item['title']}")
        print(f"    来源: {item['source']}")
        print()


if __name__ == "__main__":
    main()
