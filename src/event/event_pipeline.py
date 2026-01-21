"""
事件分析流程模块

该模块负责整合事件分析的完整流程：嵌入→聚类→摘要生成。
"""

import logging
from typing import List, Dict, Any, Tuple

from .embedding import TextEmbedder
from .clustering import NewsClusterer
from .event_summary import EventSummarizer
from .event_config import EVENT_DETECTION_THRESHOLD, MIN_EVENT_SIZE

logger = logging.getLogger(__name__)


class EventPipeline:
    """事件分析流程管理器"""
    
    def __init__(self):
        """初始化事件分析流程"""
        self.embedder = TextEmbedder()
        self.clusterer = NewsClusterer()
        self.summarizer = EventSummarizer()
    
    def analyze_events(self, news_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        执行完整的事件分析流程
        
        Args:
            news_list: 新闻列表
            
        Returns:
            Tuple[List[Dict], Dict]: 事件摘要列表和流程统计信息
        """
        logger.info("开始事件分析流程")
        
        if not news_list:
            logger.warning("新闻列表为空，跳过事件分析")
            return [], {"total_news": 0, "events_detected": 0}
        
        stats = {"total_news": len(news_list)}
        
        try:
            # 第一步：文本嵌入
            logger.info("第一步：文本嵌入...")
            embeddings = self.embedder.embed_news(news_list)
            logger.info(f"文本嵌入完成，生成 {embeddings.shape[0]} 个嵌入向量")
            stats["embedding_completed"] = True
            
            # 第二步：新闻聚类
            logger.info("第二步：新闻聚类...")
            news_clusters = self.clusterer.cluster_news(news_list, embeddings)
            logger.info(f"新闻聚类完成，检测到 {len(news_clusters)} 个事件")
            stats["clusters_detected"] = len(news_clusters)
            
            # 过滤小规模事件
            filtered_clusters = [
                cluster for cluster in news_clusters 
                if len(cluster) >= MIN_EVENT_SIZE
            ]
            logger.info(f"过滤后保留 {len(filtered_clusters)} 个有效事件（最小规模: {MIN_EVENT_SIZE}）")
            stats["valid_events"] = len(filtered_clusters)
            
            # 第三步：事件摘要生成
            logger.info("第三步：事件摘要生成...")
            events = self.summarizer.summarize_events(filtered_clusters)
            logger.info(f"事件摘要生成完成，生成 {len(events)} 个事件摘要")
            stats["events_summarized"] = len(events)
            
            # 添加详细统计信息
            if events:
                total_news_in_events = sum(event.get('news_count', 0) for event in events)
                stats["total_news_in_events"] = total_news_in_events
                stats["coverage_rate"] = total_news_in_events / len(news_list)
                
                # 事件规模分布
                event_sizes = [event.get('news_count', 0) for event in events]
                stats["avg_event_size"] = sum(event_sizes) / len(event_sizes)
                stats["max_event_size"] = max(event_sizes)
                stats["min_event_size"] = min(event_sizes)
            
            logger.info("事件分析流程完成")
            return events, stats
            
        except Exception as e:
            logger.error(f"事件分析流程失败: {e}", exc_info=True)
            stats["error"] = str(e)
            return [], stats
    
    def get_event_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取事件统计信息
        
        Args:
            events: 事件列表
            
        Returns:
            Dict: 事件统计信息
        """
        if not events:
            return {"total_events": 0}
        
        stats = {
            "total_events": len(events),
            "total_news": sum(event.get('news_count', 0) for event in events),
            "avg_news_per_event": sum(event.get('news_count', 0) for event in events) / len(events),
            "sources_coverage": len(set(
                source for event in events 
                for source in event.get('sources', [])
            )),
            "keywords_distribution": {}
        }
        
        # 关键词分布统计
        all_keywords = []
        for event in events:
            all_keywords.extend(event.get('keywords', []))
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        stats["top_keywords"] = keyword_counts.most_common(10)
        
        return stats