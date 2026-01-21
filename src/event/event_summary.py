"""
事件摘要生成模块

该模块负责对聚类后的新闻事件生成摘要和分析。
"""

from typing import List, Dict, Any
from datetime import datetime
import json

from .event_config import SUMMARY_MAX_LENGTH, SUMMARY_MIN_LENGTH


class EventSummarizer:
    """事件摘要生成器"""
    
    def __init__(self):
        """初始化事件摘要生成器"""
        pass
    
    def generate_event_keywords(self, news_cluster: List[Dict[str, Any]]) -> List[str]:
        """
        生成事件关键词
        
        Args:
            news_cluster: 同一事件的新闻列表
            
        Returns:
            List[str]: 事件关键词列表
        """
        if not news_cluster:
            return []
        
        # 简单的关键词提取逻辑（实际实现中可以使用更复杂的NLP技术）
        keywords = set()
        
        for news in news_cluster:
            title = news.get('title', '').lower()
            content = news.get('content', '').lower()
            
            # 提取公司名称、产品名称等关键词
            # 这里使用简单的规则，实际中可以集成命名实体识别
            words = title.split() + content.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    keywords.add(word)
        
        return list(keywords)[:10]  # 返回前10个关键词
    
    def generate_event_summary(self, news_cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成事件摘要
        
        Args:
            news_cluster: 同一事件的新闻列表
            
        Returns:
            Dict: 事件摘要信息
        """
        if not news_cluster:
            return {}
        
        # 提取事件基本信息
        titles = [news.get('title', '') for news in news_cluster]
        sources = [news.get('source', '') for news in news_cluster]
        dates = [news.get('date', '') for news in news_cluster]
        
        # 生成事件摘要
        event_summary = {
            "event_id": f"event_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "news_count": len(news_cluster),
            "sources": list(set(sources)),
            "date_range": {
                "earliest": min(dates) if dates else "",
                "latest": max(dates) if dates else ""
            },
            "keywords": self.generate_event_keywords(news_cluster),
            "representative_title": titles[0] if titles else "",
            "summary": self._generate_text_summary(news_cluster),
            "news_list": news_cluster
        }
        
        return event_summary
    
    def _generate_text_summary(self, news_cluster: List[Dict[str, Any]]) -> str:
        """
        生成文本摘要
        
        Args:
            news_cluster: 新闻列表
            
        Returns:
            str: 文本摘要
        """
        if not news_cluster:
            return ""
        
        # 简单的摘要生成逻辑（实际实现中可以集成AI摘要模型）
        titles = [news.get('title', '') for news in news_cluster]
        
        if len(titles) == 1:
            return titles[0]
        else:
            main_title = titles[0]
            additional_count = len(titles) - 1
            return f"{main_title}（另有{additional_count}条相关报道）"
    
    def summarize_events(self, news_clusters: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        对多个新闻聚类生成事件摘要
        
        Args:
            news_clusters: 新闻聚类列表
            
        Returns:
            List[Dict]: 事件摘要列表
        """
        events = []
        
        for i, cluster in enumerate(news_clusters):
            event_summary = self.generate_event_summary(cluster)
            if event_summary:
                events.append(event_summary)
        
        # 按新闻数量排序（新闻数量多的事件更重要）
        events.sort(key=lambda x: x.get('news_count', 0), reverse=True)
        
        return events