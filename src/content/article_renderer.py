#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章渲染模块

负责将文章数据转换为适合公众号发布的Markdown格式
支持emoji、标题分级、列表等公众号友好格式
"""

import logging
from datetime import datetime
from typing import List, Dict

from .article_schema import DailyArticle, ArticleEvent, MarketSignals, WatchDirections


logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Markdown渲染器"""
    
    def __init__(self):
        self.max_title_length = 50
        self.max_summary_length = 200
    
    def render(self, article: DailyArticle) -> str:
        """
        渲染文章为Markdown格式
        
        Args:
            article: 每日文章数据
            
        Returns:
            str: Markdown格式的文章内容
        """
        try:
            logger.info("开始渲染公众号文章")
            
            parts = []
            
            # 1. 标题部分
            parts.append(self._render_header(article))
            
            # 2. 一句话总览
            parts.append(self._render_overview(article))
            
            # 3. 核心事件部分
            parts.append(self._render_core_events(article.events))
            
            # 4. 市场信号汇总
            parts.append(self._render_market_signals(article.events))
            
            # 5. 值得关注方向
            parts.append(self._render_watch_directions(article.events))
            
            # 6. 免责声明
            parts.append(self._render_disclaimer(article))
            
            # 合并所有部分
            content = "\n\n".join(parts)
            
            logger.info("文章渲染完成")
            return content
            
        except Exception as e:
            logger.error(f"文章渲染失败: {e}")
            raise
    
    def _render_header(self, article: DailyArticle) -> str:
        """渲染标题部分"""
        header = f"# {article.headline}\n\n"
        
        # 一句话总览占位
        header += "*一句话总览（给忙人）*\n\n"
        
        return header
    
    def _render_overview(self, article: DailyArticle) -> str:
        """渲染一句话总览"""
        if not article.events:
            return "今日无重要AI投资事件，市场相对平静。"
        
        # 根据最重要的事件生成总览
        main_event = article.events[0]
        
        if main_event.importance == "High":
            if main_event.signal == "Positive":
                overview = f"🔥 **{main_event.title.replace('1️⃣', '').strip()}** 成为今日最大亮点，市场情绪积极。"
            elif main_event.signal == "Risk":
                overview = f"⚠️ **{main_event.title.replace('1️⃣', '').strip()}** 引发关注，需谨慎观察后续发展。"
            else:
                overview = f"📊 **{main_event.title.replace('1️⃣', '').strip()}** 值得重点关注，市场反应待观察。"
        else:
            overview = "今日AI投资市场整体平稳，多个技术领域有积极进展。"
        
        return f"---\n\n{overview}\n"
    
    def _render_core_events(self, events: List[ArticleEvent]) -> str:
        """渲染核心事件部分"""
        if not events:
            return "## 一、今日核心事件\n\n暂无重要事件。\n"
        
        content = "## 一、今日核心事件（3–5 条）\n\n"
        
        for event in events:
            content += self._render_single_event(event)
            content += "\n---\n\n"
        
        return content.rstrip("\n---\n\n") + "\n"
    
    def _render_single_event(self, event: ArticleEvent) -> str:
        """渲染单个事件"""
        content = f"### {event.title}\n\n"
        
        # 事件概述
        content += "- 📌 **事件概述**\n"
        summary = event.summary[:self.max_summary_length]
        if len(event.summary) > self.max_summary_length:
            summary += "..."
        content += f"  {summary}\n\n"
        
        # 关键信息拆解
        content += "- 🧠 **关键信息拆解**\n"
        content += f"  - 涉及公司：{', '.join(event.companies) if event.companies else '未明确'}\n"
        content += f"  - 信息来源：{', '.join(event.sources[:3]) if event.sources else '未明确'}\n"
        content += f"  - 相关新闻：{event.news_count}篇\n"
        
        # 添加重要性排名前5的文章标题和超链接
        if event.news_list:
            # 按新闻来源权威性和发布时间排序
            sorted_news = sorted(event.news_list, 
                               key=lambda x: self._get_news_importance_score(x), 
                               reverse=True)[:5]
            
            if sorted_news:
                content += "  - 重要文章：\n"
                for i, news in enumerate(sorted_news):
                    title = news.get("title", "")
                    url = news.get("url", "")
                    source = news.get("source", "未知来源")
                    if title and url:
                        # 简化标题，避免过长
                        if len(title) > 40:
                            title = title[:37] + "..."
                        content += f"    {i+1}. [{title}]({url}) - {source}\n"
        
        content += "\n"
        
        # 投资信号解读
        content += "- 💡 **投资信号解读**\n"
        signal_emoji = self._get_signal_emoji(event.signal)
        importance_text = self._get_importance_text(event.importance)
        content += f"  - 信号方向：{signal_emoji} {event.signal}\n"
        content += f"  - 重要性：{importance_text}\n\n"
        
        # 潜在风险
        content += "- ⚠️ **潜在风险**\n"
        if event.risks:
            for risk in event.risks:
                content += f"  - {risk}\n"
        else:
            content += "  - 暂无明确风险提示\n"
        
        return content
    
    def _render_market_signals(self, events: List[ArticleEvent]) -> str:
        """渲染市场信号汇总"""
        if not events:
            return ""
        
        # 统计信号分布
        positive_events = [e for e in events if e.signal == "Positive"]
        neutral_events = [e for e in events if e.signal == "Neutral"]
        risk_events = [e for e in events if e.signal == "Risk"]
        
        content = "## 二、市场信号汇总\n\n"
        
        # 正向信号
        if positive_events:
            content += "- **正向信号**：\n"
            for event in positive_events:
                title = event.title.replace("🔹", "").strip()
                content += f"  - ✅ {title}\n"
            content += "\n"
        
        # 中性观察
        if neutral_events:
            content += "- **中性观察**：\n"
            for event in neutral_events:
                title = event.title.replace("🔹", "").strip()
                content += f"  - 📊 {title}\n"
            content += "\n"
        
        # 风险提示
        if risk_events:
            content += "- **风险提示**：\n"
            for event in risk_events:
                title = event.title.replace("🔹", "").strip()
                content += f"  - ⚠️ {title}\n"
            content += "\n"
        
        return content
    
    def _render_watch_directions(self, events: List[ArticleEvent]) -> str:
        """渲染值得关注方向"""
        # 基于事件内容推断关注方向
        directions = []
        
        # 分析事件关键词
        all_titles = " ".join([e.title for e in events])
        
        if any(keyword in all_titles for keyword in ["GPT", "模型", "大语言"]):
            directions.append("模型商业化")
        
        if any(keyword in all_titles for keyword in ["GPU", "芯片", "算力"]):
            directions.append("算力供应链")
        
        if any(keyword in all_titles for keyword in ["创业", "初创", "大厂"]):
            directions.append("大厂 vs 创业公司")
        
        if not directions:
            directions = ["AI技术创新", "算力基础设施", "应用场景落地"]
        
        content = "## 三、今日值得持续关注的方向\n\n"
        
        for direction in directions:
            content += f"- {direction}\n"
        
        return content
    
    def _render_disclaimer(self, article: DailyArticle) -> str:
        """渲染免责声明"""
        return f"> {article.disclaimer}"
    
    def _get_signal_emoji(self, signal: str) -> str:
        """获取信号对应的emoji"""
        emoji_map = {
            "Positive": "✅",
            "Neutral": "📊", 
            "Risk": "⚠️"
        }
        return emoji_map.get(signal, "📊")
    
    def _get_importance_text(self, importance: str) -> str:
        """获取重要性描述文本"""
        text_map = {
            "High": "🔥 高重要性",
            "Medium": "📈 中等重要性", 
            "Low": "📊 一般关注"
        }
        return text_map.get(importance, "📊 一般关注")
    
    def _get_news_importance_score(self, news: Dict) -> float:
        """计算新闻重要性分数，基于来源权威性和发布时间"""
        score = 0.0
        
        # 来源权威性评分
        source = news.get("source", "").lower()
        source_scores = {
            "financial times": 10,
            "the wall street journal": 10,
            "bloomberg": 9,
            "reuters": 9,
            "techcrunch": 8,
            "the verge": 8,
            "hacker news": 7,
            "reddit": 5
        }
        
        for key, value in source_scores.items():
            if key in source:
                score += value
                break
        
        # 默认分数
        if score == 0:
            score = 6
        
        # 发布时间加分（越新分数越高）
        date_str = news.get("date", "")
        if date_str:
            try:
                # 解析日期格式：YYYY-MM-DD HH:MM
                news_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                now = datetime.now()
                hours_diff = (now - news_time).total_seconds() / 3600
                
                # 24小时内发布的新闻额外加分
                if hours_diff <= 24:
                    score += 2
                elif hours_diff <= 48:
                    score += 1
            except:
                pass
        
        return score