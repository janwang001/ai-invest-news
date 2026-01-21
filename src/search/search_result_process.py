#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索结果处理模块 - SearchResultProcessor类

集成去重、规范化、相似性判断、质量评分、排序选择等功能。
"""

import logging
from typing import List, Dict, Any, Optional, Tuple


class SearchResultProcessor:
    """搜索结果处理器类，统一管理搜索结果的处理流程"""
    
    # 配置常量
    REQUIRED_FIELDS = ["title", "content", "source", "date", "url"]
    SIMILARITY_THRESHOLD = 0.6
    
    def __init__(self, max_items: int = 10, similarity_threshold: float = 0.6):
        """
        初始化搜索结果处理器
        
        Args:
            max_items: 规范化输出的最大条数
            similarity_threshold: 相似度阈值（0-1）
        """
        self.max_items = max_items
        self.similarity_threshold = similarity_threshold
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
    
    def validate_news_item(self, item: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        验证并清理单条新闻项。
        
        Args:
            item: 新闻字典
            index: 条目索引
            
        Returns:
            验证通过的新闻字典，或 None 如果验证失败
        """
        if not isinstance(item, dict):
            self.logger.warning(f"[{index}] 条目不是字典类型: {type(item)}")
            return None
        
        try:
            # 检查必需字段
            missing_fields = [field for field in self.REQUIRED_FIELDS if field not in item]
            if missing_fields:
                self.logger.warning(f"[{index}] 缺少必需字段: {missing_fields}，标题: {item.get('title', '未知')}")
                return None
            
            # 检查字段非空
            for field in self.REQUIRED_FIELDS:
                if not item[field] or (isinstance(item[field], str) and not item[field].strip()):
                    self.logger.warning(f"[{index}] 字段为空或仅空格: {field}，标题: {item.get('title', '未知')}")
                    return None
            
            # 清理和验证必需字段
            validated_item = {
                "title": str(item["title"]).strip(),
                "content": str(item["content"]).strip(),
                "source": str(item["source"]).strip(),
                "date": str(item["date"]).strip(),
                "url": str(item["url"]).strip()
            }
            
            # 保留原有的额外字段（如 fetched_content, fetched_title, fetch_stats,
            # light_features, investment_info, ai_summary, investment_score 等）
            for key, value in item.items():
                if key not in validated_item:
                    validated_item[key] = value
            
            # 基本长度检查
            if len(validated_item["title"]) > 500:
                self.logger.warning(f"[{index}] 标题过长（{len(validated_item['title'])}字），已截断")
                validated_item["title"] = validated_item["title"][:500]
            
            if len(validated_item["content"]) > 2000:
                self.logger.warning(f"[{index}] 内容过长（{len(validated_item['content'])}字），已截断")
                validated_item["content"] = validated_item["content"][:2000]
            
            self.logger.debug(f"[{index}] ✓ 条目验证成功: {validated_item['title'][:50]}...")
            return validated_item
            
        except Exception as e:
            self.logger.error(f"[{index}] 验证条目时出错: {e}", exc_info=True)
            return None
    
    def normalize_news(self, raw_news: List[Dict[str, Any]]) -> Tuple[List[Dict], Dict]:
        """
        规范化新闻数据：控制数量 + 统一字段 + 数据验证，防止 Prompt 爆炸
        
        Args:
            raw_news: 原始新闻列表
            
        Returns:
            tuple: (normalized_list, stats_dict)
                - normalized_list: 规范化的新闻列表
                - stats_dict: 统计信息，包含每个源的最终条数
        """
        self.logger.info(f"【步骤1】规范化新闻数据 - 输入: {len(raw_news) if isinstance(raw_news, list) else 0} 条")
        
        # 输入验证
        if not isinstance(raw_news, list):
            self.logger.error(f"输入不是列表类型: {type(raw_news)}")
            raise TypeError(f"raw_news 应该是列表，但收到 {type(raw_news)}")
        
        if not raw_news:
            self.logger.warning("输入列表为空")
            return [], {}
        
        if self.max_items <= 0:
            self.logger.error(f"max_items 必须大于 0，但收到 {self.max_items}")
            raise ValueError(f"max_items 必须大于 0，但收到 {self.max_items}")
        
        normalized = []
        skipped_count = 0
        source_count = {}  # 统计每个源的最终条数
        
        # 只处理前 max_items 条
        for idx, item in enumerate(raw_news[:self.max_items], 1):
            try:
                validated_item = self.validate_news_item(item, idx)
                
                if validated_item:
                    normalized.append(validated_item)
                    source = validated_item["source"]
                    source_count[source] = source_count.get(source, 0) + 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                self.logger.error(f"处理第 {idx} 条新闻时出错: {e}", exc_info=True)
                skipped_count += 1
                continue
        
        self.logger.info(f"规范化完成 - 有效: {len(normalized)} 条，跳过: {skipped_count} 条")
        
        if not normalized:
            self.logger.warning("所有条目都被跳过，返回空列表")
        
        return normalized, source_count
    
    def deduplicate_news(self, news_list: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        去重新闻列表：基于标题和URL去重。
        
        Args:
            news_list: 新闻列表
            
        Returns:
            tuple: (dedup_news, dedup_stats)
                - dedup_news: 去重后的新闻列表
                - dedup_stats: 去重统计信息
        """
        self.logger.info(f"【步骤2】去重新闻数据 - 输入: {len(news_list)} 条")
        
        seen = set()
        result = []
        removed_count = 0

        for n in news_list:
            key = (n["title"].lower().strip(), n["url"])
            if key in seen:
                removed_count += 1
                self.logger.debug(f"重复检测: {n['title'][:50]}...")
                continue
            seen.add(key)
            result.append(n)

        dedup_stats = {
            "removed_count": removed_count,
            "kept_count": len(result),
            "input_count": len(news_list)
        }
        
        self.logger.info(f"去重完成 - 输入: {len(news_list)} 条，移除: {removed_count} 条，保留: {len(result)} 条")
        
        return result, dedup_stats
    
    def is_similar(self, title_a: str, title_b: str, threshold: float = None) -> bool:
        """
        判断两个标题是否相似（基于词集合重叠度）。
        
        Args:
            title_a: 第一个标题
            title_b: 第二个标题
            threshold: 相似度阈值（0-1），默认使用类实例的阈值
            
        Returns:
            bool: 是否相似
        """
        if threshold is None:
            threshold = self.similarity_threshold
            
        try:
            if not isinstance(title_a, str) or not isinstance(title_b, str):
                self.logger.debug(f"标题不是字符串类型")
                return False
            
            # 转换为小写并分割单词
            words_a = set(title_a.lower().split())
            words_b = set(title_b.lower().split())

            if not words_a or not words_b:
                return False

            # 计算词重叠率
            overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
            
            return overlap > threshold
            
        except Exception as e:
            self.logger.error(f"判断相似性时出错: {e}", exc_info=True)
            return False
    
    def merge_similar_news(self, news_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        合并相似的新闻，防止重复展示。
        
        按顺序遍历新闻列表，如果与已有新闻相似则跳过，否则添加。
        
        Args:
            news_list: 新闻字典列表
            
        Returns:
            tuple: (merged_list, stats_dict)
                - merged_list: 去重后的新闻列表
                - stats_dict: 统计信息，包含去重前后的数量和去重率
        """
        self.logger.info(f"【步骤3】合并相似新闻 - 输入: {len(news_list)} 条，阈值: {self.similarity_threshold}")
        
        if not isinstance(news_list, list):
            self.logger.error(f"输入不是列表类型: {type(news_list)}")
            raise TypeError(f"news_list 应该是列表，但收到 {type(news_list)}")
        
        if not (0 <= self.similarity_threshold <= 1):
            self.logger.error(f"阈值必须在 0-1 之间，但收到 {self.similarity_threshold}")
            raise ValueError(f"阈值必须在 0-1 之间，但收到 {self.similarity_threshold}")
        
        merged = []
        merged_count = 0  # 合并掉的新闻数
        
        try:
            for idx, news in enumerate(news_list, 1):
                try:
                    if not isinstance(news, dict):
                        self.logger.warning(f"[{idx}] 条目不是字典类型，跳过: {type(news)}")
                        continue
                    
                    if "title" not in news:
                        self.logger.warning(f"[{idx}] 条目缺少 title 字段，跳过")
                        continue
                    
                    title = str(news["title"])
                    found_similar = False
                    
                    # 检查是否与已有新闻相似
                    for m_idx, m in enumerate(merged, 1):
                        if self.is_similar(title, m["title"]):
                            self.logger.debug(f"[{idx}] 新闻与第 {m_idx} 条相似，跳过")
                            found_similar = True
                            merged_count += 1
                            break
                    
                    if not found_similar:
                        merged.append(news)
                        self.logger.debug(f"[{idx}] ✓ 添加新闻: {title[:50]}...")
                        
                except Exception as e:
                    self.logger.error(f"[{idx}] 处理条目时出错: {e}", exc_info=True)
                    continue
            
            stats = {
                "input_count": len(news_list),
                "output_count": len(merged),
                "merged_count": merged_count,
                "dedup_ratio": round(merged_count / len(news_list), 2) if news_list else 0
            }
            
            self.logger.info(f"合并完成 - 输入: {stats['input_count']} 条，输出: {stats['output_count']} 条，合并: {stats['merged_count']} 条")
            return merged, stats
            
        except Exception as e:
            self.logger.error(f"合并新闻时出错: {e}", exc_info=True)
            raise
    
    def process_search_results(self, raw_news: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        搜索结果处理的完整流程：去重 -> 合并相似。
        
        注意：输入的 raw_news 应该已经经过规范化，此函数专注于去重和合并处理
        质量评分和选择由单独的 news_select 函数处理
        
        Args:
            raw_news: 规范化后的新闻列表
            
        Returns:
            tuple: (processed_news, pipeline_stats)
                - processed_news: 处理后的新闻列表
                - pipeline_stats: 包含去重和合并的统计信息
        """
        self.logger.info("="*50)
        self.logger.info("开始搜索结果处理流程（去重→合并）")
        self.logger.info("="*50)
        
        pipeline_stats = {
            "input_count": len(raw_news),
            "step1_dedup": {},
            "step2_merge": {},
            "output_count": 0
        }
        
        try:
            # 步骤1：去重
            self.logger.info(f"\n【步骤1】去重 - 输入: {len(raw_news)} 条")
            dedup_news, dedup_stats = self.deduplicate_news(raw_news)
            pipeline_stats["step1_dedup"] = dedup_stats
            self.logger.info(f"去重完成 - 输出: {len(dedup_news)} 条，移除: {dedup_stats.get('removed_count', 0)} 条")
            
            if not dedup_news:
                self.logger.warning("去重后无有效新闻")
                return [], pipeline_stats
            
            # 步骤2：合并相似
            self.logger.info(f"\n【步骤2】合并相似 - 输入: {len(dedup_news)} 条")
            merged_news, merge_stats = self.merge_similar_news(dedup_news)
            pipeline_stats["step2_merge"] = merge_stats
            self.logger.info(f"合并完成 - 输出: {len(merged_news)} 条，合并: {merge_stats.get('merged_count', 0)} 条")
            
            if not merged_news:
                self.logger.warning("合并后无有效新闻")
                return [], pipeline_stats
            
            pipeline_stats["output_count"] = len(merged_news)
            
            # 输出流程总结
            self.logger.info("="*50)
            self.logger.info("处理流程完成")
            self.logger.info("="*50)
            self.logger.info(f"原始输入: {pipeline_stats['input_count']} 条")
            self.logger.info(f"去重后: {len(dedup_news)} 条（移除: {dedup_stats.get('removed_count', 0)} 条）")
            self.logger.info(f"合并后: {len(merged_news)} 条（合并: {merge_stats.get('merged_count', 0)} 条）")
            
            return merged_news, pipeline_stats
            
        except Exception as e:
            self.logger.error(f"处理流程失败: {e}", exc_info=True)
            raise


def normalize_news(raw_news: List[Dict[str, Any]], max_items: int = 10) -> Tuple[List[Dict], Dict]:
    """
    函数式接口：规范化新闻数据
    
    Args:
        raw_news: 原始新闻列表
        max_items: 规范化输出的最大条数
        
    Returns:
        tuple: (normalized_list, stats_dict)
    """
    processor = SearchResultProcessor(max_items=max_items)
    return processor.normalize_news(raw_news)


def deduplicate_news(news_list: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    函数式接口：去重新闻列表
    
    Args:
        news_list: 新闻列表
        
    Returns:
        tuple: (dedup_news, dedup_stats)
    """
    processor = SearchResultProcessor()
    return processor.deduplicate_news(news_list)


def merge_similar_news(news_list: List[Dict[str, Any]], threshold: float = 0.6) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    函数式接口：合并相似的新闻
    
    Args:
        news_list: 新闻字典列表
        threshold: 相似度阈值（0-1）
        
    Returns:
        tuple: (merged_list, stats_dict)
    """
    processor = SearchResultProcessor(similarity_threshold=threshold)
    return processor.merge_similar_news(news_list)


def process_search_results(raw_news: List[Dict], top_k: int = 5) -> Tuple[List[Dict], Dict]:
    """
    函数式接口：搜索结果处理的完整流程
    
    Args:
        raw_news: 规范化后的新闻列表
        top_k: 最终要选择的新闻数量
        
    Returns:
        tuple: (processed_news, pipeline_stats)
    """
    processor = SearchResultProcessor()
    return processor.process_search_results(raw_news)


def main():
    """测试函数"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("="*50)
        logger.info("开始SearchResultProcessor测试")
        logger.info("="*50)
        
        # 测试数据
        test_news = [
            {
                "title": "OpenAI 发布新的 GPT 模型",
                "content": "OpenAI 发布了最新的 GPT 模型，性能提升显著...",
                "source": "TechCrunch",
                "date": "2026-01-19",
                "url": "https://example.com/1"
            },
            {
                "title": "OpenAI 发布 GPT 新版本",  # 重复
                "content": "OpenAI 推出了新版 GPT，功能更强大...",
                "source": "MIT Technology Review",
                "date": "2026-01-19",
                "url": "https://example.com/2"
            },
            {
                "title": "OpenAI 发布 AI 模型",  # 相似
                "content": "OpenAI 发布了新的 AI 模型...",
                "source": "VentureBeat AI",
                "date": "2026-01-19",
                "url": "https://example.com/3"
            },
            {
                "title": "GPU 芯片价格下降",
                "content": "最近 GPU 芯片价格持续下降...",
                "source": "TechCrunch",
                "date": "2026-01-19",
                "url": "https://example.com/4"
            }
        ]
        
        # 使用SearchResultProcessor类
        processor = SearchResultProcessor(max_items=5, similarity_threshold=0.6)
        
        # 测试规范化
        normalized_news, normalize_stats = processor.normalize_news(test_news)
        print(f"规范化结果: {len(normalized_news)} 条新闻")
        
        # 测试完整流程
        processed_news, stats = processor.process_search_results(normalized_news)
        
        print("\n" + "="*50)
        print(f"处理结果（共 {len(processed_news)} 条）：")
        print("="*50)
        for idx, item in enumerate(processed_news, 1):
            print(f"\n[{idx}] {item['title']}")
            print(f"    来源: {item['source']}")
        
        print("\n" + "="*50)
        print("流程统计信息")
        print("="*50)
        print(f"原始输入: {stats['input_count']} 条")
        print(f"去重后: {stats['step1_dedup']['kept_count']} 条")
        print(f"合并后: {stats['step2_merge']['output_count']} 条")
        print(f"最终输出: {stats['output_count']} 条")
        
        logger.info("="*50)
        logger.info("测试完成")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
