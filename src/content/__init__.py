#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章生成模块

将AI投资事件数据转换为适合公众号发布的文章格式
包含文章结构定义、构建逻辑和渲染输出功能
"""

from .article_schema import ArticleEvent, DailyArticle, MarketSignals, WatchDirections
from .article_builder import ArticleBuilder
from .article_renderer import MarkdownRenderer


__all__ = [
    # 数据结构
    "ArticleEvent",
    "DailyArticle", 
    "MarketSignals",
    "WatchDirections",
    
    # 核心组件
    "ArticleBuilder",
    "MarkdownRenderer",
]


# 模块版本信息
__version__ = "1.0.0"
__author__ = "AI Invest Demo Team"
__description__ = "公众号文章生成模块"