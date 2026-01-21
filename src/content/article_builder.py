#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章构建模块

负责将事件数据转换为适合公众号发布的文章结构
包含事件排序、分类、信息裁剪和去重表达等逻辑
"""

import logging
from typing import List, Dict, Tuple
from datetime import datetime

from .article_schema import ArticleEvent, DailyArticle, MarketSignals, WatchDirections


logger = logging.getLogger(__name__)


class ArticleBuilder:
    """文章构建器"""
    
    def __init__(self):
        self.max_events = 8  # 最多展示8个核心事件（增加数量以丰富内容）
        self.min_importance = "Low"  # 最低重要性级别（降低阈值包含更多事件）
    
    def build(self, events: List[Dict]) -> DailyArticle:
        """
        构建每日文章
        
        Args:
            events: 事件列表，包含decision信息
            
        Returns:
            DailyArticle: 构建完成的每日文章
        """
        try:
            logger.info("开始构建公众号文章")
            
            # 1. 过滤和排序事件
            filtered_events = self._filter_and_sort_events(events)
            
            # 2. 转换为ArticleEvent对象
            article_events = self._convert_to_article_events(filtered_events)
            
            # 3. 生成市场信号汇总
            market_signals = self._generate_market_signals(article_events)
            
            # 4. 生成值得关注方向
            watch_directions = self._generate_watch_directions(article_events)
            
            # 5. 生成头条标题
            headline = self._generate_headline(article_events)
            
            # 6. 生成市场概览
            market_overview = self._generate_market_overview(
                article_events, market_signals, watch_directions
            )
            
            # 7. 构建最终文章
            article = DailyArticle(
                date=datetime.now().strftime("%Y-%m-%d"),
                headline=headline,
                events=article_events,
                market_overview=market_overview
            )
            
            logger.info(f"文章构建完成，包含 {len(article_events)} 个事件")
            return article
            
        except Exception as e:
            logger.error(f"文章构建失败: {e}")
            raise
    
    def _filter_and_sort_events(self, events: List[Dict]) -> List[Dict]:
        """过滤和排序事件"""
        # 过滤：保留所有事件（包括Low重要性）以丰富内容
        filtered = events.copy()
        
        # 排序：按重要性（High > Medium）和新闻数量排序
        filtered.sort(key=lambda x: (
            self._importance_score(x.get("decision", {}).get("importance", "Low")),
            x.get("news_count", 0)
        ), reverse=True)
        
        # 限制数量
        return filtered[:self.max_events]
    
    def _importance_score(self, importance: str) -> int:
        """重要性评分"""
        importance_map = {"High": 3, "Medium": 2, "Low": 1}
        return importance_map.get(importance, 1)
    
    def _convert_to_article_events(self, events: List[Dict]) -> List[ArticleEvent]:
        """转换为ArticleEvent对象"""
        article_events = []
        
        for i, event in enumerate(events):
            decision = event.get("decision", {})
            
            article_event = ArticleEvent(
                title=self._generate_event_title(event, i),
                summary=event.get("summary", ""),
                signal=decision.get("signal", "Neutral"),
                importance=decision.get("importance", "Medium"),
                risks=self._extract_risks(event),
                companies=self._extract_companies(event),
                news_count=event.get("news_count", 0),
                sources=event.get("sources", []),
                news_list=event.get("news_list", []),  # 传递新闻列表信息
                event_id=event.get("event_id")
            )
            article_events.append(article_event)
        
        return article_events
    
    def _generate_event_title(self, event: Dict, index: int) -> str:
        """生成事件标题"""
        # 使用emoji序号
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        emoji = emoji_numbers[index] if index < len(emoji_numbers) else "🔹"
        
        title = event.get("representative_title", event.get("summary", ""))
        # 简化标题，避免过长
        if len(title) > 50:
            title = title[:47] + "..."
        
        return f"{emoji} {title}"
    
    def _extract_risks(self, event: Dict) -> List[str]:
        """提取风险信息"""
        risks = []
        signal = event.get("decision", {}).get("signal", "Neutral")
        
        if signal == "Risk":
            # 从新闻内容中提取风险关键词
            for news in event.get("news_list", []):
                content = news.get("content", "").lower()
                if any(risk_word in content for risk_word in ["risk", "warning", "caution", "concern"]):
                    risks.append("存在潜在风险")
                    break
        
        return risks[:3]  # 最多3个风险点
    
    def _extract_companies(self, event: Dict) -> List[str]:
        """提取公司信息"""
        companies = set()
        
        for news in event.get("news_list", []):
            news_companies = news.get("companies", [])
            if news_companies:
                companies.update(news_companies)
        
        return list(companies)[:5]  # 最多5个公司
    
    def _generate_market_signals(self, events: List[ArticleEvent]) -> MarketSignals:
        """生成市场信号汇总"""
        positive_signals = []
        neutral_signals = []
        risk_signals = []
        
        for event in events:
            if event.signal == "Positive":
                positive_signals.append(event.title.replace("🔹", "").strip())
            elif event.signal == "Risk":
                risk_signals.append(event.title.replace("🔹", "").strip())
            else:
                neutral_signals.append(event.title.replace("🔹", "").strip())
        
        return MarketSignals(positive_signals, neutral_signals, risk_signals)
    
    def _generate_watch_directions(self, events: List[ArticleEvent]) -> WatchDirections:
        """生成值得关注方向"""
        directions = []
        
        # 根据事件类型推断关注方向
        high_importance_events = [e for e in events if e.importance == "High"]
        
        if any("AI" in e.title or "GPT" in e.title for e in high_importance_events):
            directions.append("模型商业化")
        
        if any("GPU" in e.title or "芯片" in e.title for e in high_importance_events):
            directions.append("算力供应链")
        
        if any("大厂" in e.title or "创业" in e.title for e in high_importance_events):
            directions.append("大厂 vs 创业公司")
        
        # 默认方向
        if not directions:
            directions = ["AI技术创新", "算力基础设施", "应用场景落地"]
        
        reasoning = "基于今日重要事件的技术方向和商业模式判断"
        return WatchDirections(directions, reasoning)
    
    def _generate_headline(self, events: List[ArticleEvent]) -> str:
        """生成头条标题"""
        if not events:
            return "今日 AI 投资要点速览"
        
        # 使用最重要的事件作为头条
        main_event = events[0]
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        if main_event.importance == "High":
            return f"今日 AI 投资要点速览 | {date_str}"
        else:
            return f"AI 投资观察日报 | {date_str}"
    
    def _generate_market_overview(self, events: List[ArticleEvent], 
                                market_signals: MarketSignals,
                                watch_directions: WatchDirections) -> str:
        """生成市场概览"""
        total_events = len(events)
        high_count = len([e for e in events if e.importance == "High"])
        positive_count = len([e for e in events if e.signal == "Positive"])
        
        overview = f"今日共追踪到 {total_events} 个重要事件，其中 {high_count} 个为高重要性事件。"
        
        if positive_count > 0:
            overview += f"市场整体呈现 {positive_count} 个积极信号。"
        
        return overview