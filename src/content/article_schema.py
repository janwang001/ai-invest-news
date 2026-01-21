#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章数据结构定义模块

定义文章事件和每日文章的数据结构，用于生成投资资讯公众号文章
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class ArticleEvent:
    """文章事件数据结构"""
    title: str
    summary: str
    signal: str  # Positive / Neutral / Risk
    importance: str  # High / Medium / Low
    risks: List[str]
    companies: List[str]
    news_count: int
    sources: List[str]
    news_list: List[Dict] = field(default_factory=list)  # 新闻列表，包含标题、链接、重要性等信息
    event_id: Optional[str] = None


@dataclass
class DailyArticle:
    """每日文章数据结构"""
    date: str
    headline: str
    events: List[ArticleEvent]
    market_overview: str
    disclaimer: str = "本文仅用于信息整理与行业研究，不构成投资建议"
    
    def __post_init__(self):
        """后初始化处理"""
        if not self.date:
            self.date = datetime.now().strftime("%Y-%m-%d")


@dataclass
class MarketSignals:
    """市场信号汇总数据结构"""
    positive_signals: List[str]
    neutral_signals: List[str]
    risk_signals: List[str]


@dataclass
class WatchDirections:
    """值得关注方向数据结构"""
    directions: List[str]
    reasoning: str