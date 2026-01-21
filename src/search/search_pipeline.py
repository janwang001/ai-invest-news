#!/usr/bin/env python3
"""
SearchPipeline - 搜索结果处理流程管道类

该类统一管理RSS搜索、结果处理和统计分析的完整流程。
"""

import feedparser
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

# 当作为模块导入时使用相对导入，直接运行时使用绝对导入
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from search.rss_config import RSS_SOURCES, MAX_ITEMS_PER_SOURCE, SEARCH_HOURS, MAX_NORMALIZED_ITEMS
    from search.search_result_process import SearchResultProcessor
else:
    from .rss_config import RSS_SOURCES, MAX_ITEMS_PER_SOURCE, SEARCH_HOURS, MAX_NORMALIZED_ITEMS
    from .search_result_process import SearchResultProcessor


class SearchPipeline:
    """搜索结果处理流程管道类"""
    
    def __init__(self, hours: int = SEARCH_HOURS, max_items_per_source: int = MAX_ITEMS_PER_SOURCE):
        """
        初始化搜索管道
        
        Args:
            hours: 搜索的时间范围（小时），默认 24 小时
            max_items_per_source: 每个源最大条数，默认 20 条
        """
        self.hours = hours
        self.max_items_per_source = max_items_per_source
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger
    
    def search_recent_ai_news(self) -> Tuple[List[Dict], Dict]:
        """
        搜索指定时间内的最近 AI 相关新闻。
        
        Returns:
            tuple: (news_list, stats_dict)
                - news_list: 包含新闻信息的字典列表
                - stats_dict: 统计信息，包含每个源的获取条数和源分类统计
        """
        self.logger.info(f"开始搜索最近 {self.hours} 小时的 AI 新闻，每个源最多 {self.max_items_per_source} 条")
        
        results = []
        source_stats = {}  # 统计每个源的条数
        
        # 源分类统计
        source_classification = {
            "valid_sources": [],      # 有效源：有搜索结果，且有没过期的新闻
            "expired_sources": [],    # 过期源：有搜索结果，但都是过期的新闻
            "invalid_sources": []     # 无效源：没有搜索结果
        }
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.hours)
        self.logger.info(f"时间截断点（UTC）: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"当前时间（UTC）: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")

        for source in RSS_SOURCES:
            self.logger.info(f"正在从 {source['name']} 获取 RSS 源...")
            self.logger.debug(f"RSS URL: {source['url']}")
            
            source_stats[source['name']] = {
                "total_found": 0,
                "valid_fetched": 0,
                "skipped_no_time": 0,
                "skipped_too_old": 0
            }
            
            try:
                feed = feedparser.parse(source["url"])
                
                # 检查 RSS 解析是否有错误
                if feed.bozo:
                    self.logger.warning(f"{source['name']} RSS 解析异常: {feed.bozo_exception}")
                
                if not feed.entries:
                    self.logger.warning(f"{source['name']} 没有找到任何条目")
                    source_stats[source['name']]["total_found"] = 0
                    source_classification["invalid_sources"].append(source['name'])
                    continue
                    
                source_stats[source['name']]["total_found"] = len(feed.entries)
                self.logger.info(f"从 {source['name']} 获取到 {len(feed.entries)} 条条目")
                
                valid_count = 0
                skipped_no_time = 0
                skipped_too_old = 0
                
                for idx, entry in enumerate(feed.entries, 1):
                    # 检查是否已经达到该源的最大条数
                    if valid_count >= self.max_items_per_source:
                        self.logger.debug(f"[{source['name']}] 已达最大条数限制 ({self.max_items_per_source})，停止处理")
                        break
                    
                    try:
                        # 检查是否有发布时间
                        if not hasattr(entry, "published_parsed") or not entry.published_parsed:
                            title = getattr(entry, 'title', '未知标题')
                            self.logger.debug(f"[{idx}] 跳过条目（无发布时间）: {title}")
                            skipped_no_time += 1
                            continue

                        published_time = datetime(
                                *entry.published_parsed[:6],
                                 tzinfo=timezone.utc
                        )
                        self.logger.debug(f"[{idx}] 条目时间: {published_time.strftime('%Y-%m-%d %H:%M:%S')}")

                        if published_time < cutoff_time:
                            title = entry.get("title", "未知标题")
                            self.logger.debug(f"[{idx}] 跳过过期条目 ({published_time.strftime('%Y-%m-%d %H:%M:%S')}): {title}")
                            skipped_too_old += 1
                            continue

                        news_item = {
                            "title": entry.get("title", "未知标题"),
                            "content": entry.get("summary", "无摘要"),
                            "source": source["name"],
                            "url": entry.get("link", ""),
                            "date": published_time.strftime("%Y-%m-%d %H:%M")
                        }
                        
                        results.append(news_item)
                        valid_count += 1
                        self.logger.info(f"[{idx}] ✓ 成功添加新闻: {news_item['title'][:50]}...")
                        
                    except Exception as e:
                        self.logger.error(f"[{idx}] 处理条目时出错: {e}", exc_info=True)
                        continue
                
                source_stats[source['name']]["valid_fetched"] = valid_count
                source_stats[source['name']]["skipped_no_time"] = skipped_no_time
                source_stats[source['name']]["skipped_too_old"] = skipped_too_old
                
                self.logger.info(f"{source['name']} 统计 - 有效: {valid_count}, 无时间: {skipped_no_time}, 过期: {skipped_too_old}")
                
                # 源分类：有效源 vs 过期源
                if valid_count > 0:
                    source_classification["valid_sources"].append(source['name'])
                elif skipped_too_old > 0:
                    # 有搜索结果但都过期
                    source_classification["expired_sources"].append(source['name'])
                        
            except Exception as e:
                self.logger.error(f"从 {source['name']} 获取 RSS 失败: {e}", exc_info=True)
                continue

        self.logger.info(f"搜索完成，共找到 {len(results)} 条新闻")
        
        # 补全源分类统计（可能存在既没搜到也没过期的源）
        all_source_names = {source['name'] for source in RSS_SOURCES}
        classified_sources = (set(source_classification["valid_sources"]) | 
                             set(source_classification["expired_sources"]) | 
                             set(source_classification["invalid_sources"]))
        unclassified = all_source_names - classified_sources
        source_classification["invalid_sources"].extend(list(unclassified))
        
        # 添加源分类统计到返回结果
        stats_with_classification = {
            "sources": source_stats,
            "source_classification": {
                "valid_sources": source_classification["valid_sources"],
                "expired_sources": source_classification["expired_sources"],
                "invalid_sources": source_classification["invalid_sources"]
            }
        }
        
        return results, stats_with_classification
    
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
            skip_normalize: 是否跳过规范化步骤（当输入已经规范化时设为True）
            
        Returns:
            tuple: (processed_news, pipeline_stats)
                - processed_news: 处理后的新闻列表
                - pipeline_stats: 包含各步骤的统计信息
        """
        self.logger.info("=" * 50)
        self.logger.info("开始搜索结果处理流程（规范化→去重→合并）")
        self.logger.info("=" * 50)
        
        pipeline_stats = {
            "input_count": len(raw_news),
            "step1_normalize": {},
            "step2_dedup": {},
            "step3_merge": {},
            "output_count": 0
        }
        
        try:
            # 使用SearchResultProcessor进行结果处理
            processor = SearchResultProcessor(max_items=max_normalized_items)
            
            # 步骤1：规范化（可选跳过）
            if skip_normalize:
                self.logger.info(f"\n【步骤1】规范化 - 已跳过（输入已规范化）: {len(raw_news)} 条")
                normalized_news = raw_news
                pipeline_stats["step1_normalize"] = {"skipped": True, "count": len(raw_news)}
            else:
                self.logger.info(f"\n【步骤1】规范化 - 输入: {len(raw_news)} 条")
                normalized_news, normalize_stats = processor.normalize_news(raw_news)
                pipeline_stats["step1_normalize"] = normalize_stats
                self.logger.info(f"规范化完成 - 输出: {len(normalized_news)} 条")
            
            if not normalized_news:
                self.logger.warning("规范化后无有效新闻")
                return [], pipeline_stats
            
            # 步骤2：去重
            self.logger.info(f"\n【步骤2】去重 - 输入: {len(normalized_news)} 条")
            dedup_news, dedup_stats = processor.deduplicate_news(normalized_news)
            pipeline_stats["step2_dedup"] = dedup_stats
            self.logger.info(f"去重完成 - 输出: {len(dedup_news)} 条，移除: {dedup_stats.get('removed_count', 0)} 条")
            
            if not dedup_news:
                self.logger.warning("去重后无有效新闻")
                return [], pipeline_stats
            
            # 步骤3：合并相似
            self.logger.info(f"\n【步骤3】合并相似 - 输入: {len(dedup_news)} 条")
            merged_news, merge_stats = processor.merge_similar_news(dedup_news)
            pipeline_stats["step3_merge"] = merge_stats
            self.logger.info(f"合并完成 - 输出: {len(merged_news)} 条，合并: {merge_stats.get('merged_count', 0)} 条")
            
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
            self.logger.info(f"去重后: {len(dedup_news)} 条（移除: {dedup_stats.get('removed_count', 0)} 条）")
            self.logger.info(f"合并后: {len(merged_news)} 条（合并: {merge_stats.get('merged_count', 0)} 条）")
            
            return merged_news, pipeline_stats
            
        except Exception as e:
            self.logger.error(f"处理流程失败: {e}", exc_info=True)
            raise
    
    def run_pipeline(self) -> Tuple[List[Dict], Dict]:
        """
        运行完整的搜索处理管道
        
        Returns:
            tuple: (processed_news, combined_stats)
                - processed_news: 处理后的新闻列表
                - combined_stats: 包含搜索和处理统计的完整统计信息
        """
        self.logger.info("=" * 50)
        self.logger.info("开始运行完整搜索处理管道")
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
        
        return processed_news, combined_stats


def main():
    """测试函数"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("开始SearchPipeline测试")
        logger.info("=" * 50)
        
        # 创建管道实例
        pipeline = SearchPipeline(hours=24, max_items_per_source=5)
        
        # 运行完整管道
        processed_news, stats = pipeline.run_pipeline()
        
        print(f"\n搜索到 {len(processed_news)} 条新闻\n")
        for idx, item in enumerate(processed_news[:3], 1):
            print(f"[{idx}] {item['title']}")
            print(f"    来源: {item['source']}")
        
        logger.info("=" * 50)
        logger.info("测试完成")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
