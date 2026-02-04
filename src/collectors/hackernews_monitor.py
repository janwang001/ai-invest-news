#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacker News 首页监控

监控HN首页Top Stories中的AI相关热门讨论:
- 使用官方HN API (无需认证)
- 筛选AI/ML相关帖子
- 分析评论热度和情绪

HN首页 = 技术社区风向标
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class HackerNewsMonitor:
    """Hacker News首页监控器"""

    def __init__(self):
        # HN官方API
        self.api_base = "https://hacker-news.firebaseio.com/v0"

        # AI相关关键词
        self.ai_keywords = [
            "ai", "gpt", "llm", "chatgpt", "openai", "anthropic", "claude",
            "gemini", "llama", "mistral", "transformer", "neural", "deep learning",
            "machine learning", "ml", "artificial intelligence", "agi",
            "diffusion", "stable diffusion", "midjourney", "dall-e",
            "embedding", "vector", "rag", "agent", "langchain",
            "nvidia", "cuda", "gpu", "tpu", "inference",
        ]

        # 高权重关键词（涉及商业/投资）
        self.investment_keywords = [
            "funding", "raised", "valuation", "ipo", "acquisition",
            "billion", "million", "revenue", "profit", "layoff",
            "regulation", "antitrust", "ftc", "lawsuit",
            "release", "launch", "announce", "partnership",
        ]

        # 热度阈值
        self.thresholds = {
            "min_score": 50,           # 最小分数
            "min_comments": 20,        # 最小评论数
            "hot_score": 200,          # 热门阈值
            "hot_comments": 100,       # 热门评论数
        }

        self.headers = {
            "User-Agent": "AI-Investment-Monitor/1.0"
        }

    def fetch_top_stories(self, limit: int = 100) -> List[int]:
        """
        获取首页Top Stories的ID列表

        Args:
            limit: 获取数量

        Returns:
            story ID列表
        """
        try:
            url = f"{self.api_base}/topstories.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:limit]
        except Exception as e:
            logger.error(f"获取HN首页失败: {e}")
            return []

    def fetch_story(self, story_id: int) -> Optional[Dict]:
        """
        获取单个story详情

        Args:
            story_id: story ID

        Returns:
            story详情
        """
        try:
            url = f"{self.api_base}/item/{story_id}.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"获取story {story_id}失败: {e}")
            return None

    def fetch_ai_stories(self, hours: int = 24) -> List[Dict]:
        """
        获取AI相关的热门stories

        Args:
            hours: 时间范围

        Returns:
            筛选后的story列表
        """
        try:
            # 获取首页stories
            story_ids = self.fetch_top_stories(limit=100)
            if not story_ids:
                logger.warning("未获取到HN首页stories")
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()

            ai_stories = []

            for story_id in story_ids:
                try:
                    story = self.fetch_story(story_id)
                    if not story:
                        continue

                    # 检查时间
                    story_time = story.get("time", 0)
                    if story_time < cutoff_timestamp:
                        continue

                    # 检查是否AI相关
                    title = story.get("title", "").lower()
                    url = story.get("url", "").lower()

                    if not self._is_ai_related(title, url):
                        continue

                    # 检查热度
                    score = story.get("score", 0)
                    comments = story.get("descendants", 0)

                    if score < self.thresholds["min_score"]:
                        continue

                    # 计算优先级
                    priority = self._calculate_priority(score, comments, title)

                    # 提取信号
                    signal = self._extract_signal(title)

                    processed = {
                        "id": story_id,
                        "title": story.get("title", ""),
                        "url": story.get("url", ""),
                        "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                        "score": score,
                        "comments": comments,
                        "author": story.get("by", ""),
                        "time": datetime.fromtimestamp(story_time).strftime("%Y-%m-%d %H:%M"),
                        "source": "Hacker News",
                        "priority": priority,
                        "investment_signal": signal,
                        "is_hot": score >= self.thresholds["hot_score"] or comments >= self.thresholds["hot_comments"],
                    }

                    ai_stories.append(processed)
                    time.sleep(0.1)  # API礼貌延迟

                except Exception as e:
                    logger.debug(f"处理story {story_id}失败: {e}")
                    continue

            # 按优先级和分数排序
            ai_stories.sort(
                key=lambda x: (
                    0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                    -x["score"]
                )
            )

            logger.info(f"HN: 发现 {len(ai_stories)} 条AI相关热门讨论")
            return ai_stories[:20]  # 最多返回20条

        except Exception as e:
            logger.error(f"获取HN AI stories失败: {e}")
            return []

    def _is_ai_related(self, title: str, url: str) -> bool:
        """判断是否AI相关"""
        text = f"{title} {url}".lower()

        for keyword in self.ai_keywords:
            if keyword in text:
                return True

        return False

    def _calculate_priority(self, score: int, comments: int, title: str) -> str:
        """计算优先级"""
        title_lower = title.lower()

        # P0: 超热门 或 投资相关关键词
        if score >= 500 or comments >= 300:
            return "P0"

        for keyword in self.investment_keywords:
            if keyword in title_lower:
                if score >= 100:
                    return "P0"

        # P1: 热门
        if score >= self.thresholds["hot_score"] or comments >= self.thresholds["hot_comments"]:
            return "P1"

        # P2: 一般
        return "P2"

    def _extract_signal(self, title: str) -> str:
        """提取投资信号"""
        title_lower = title.lower()

        # 正面信号
        positive_keywords = [
            "launch", "release", "announce", "funding", "raised",
            "breakthrough", "milestone", "growth", "success",
        ]

        # 负面信号
        negative_keywords = [
            "layoff", "shut down", "cancel", "fail", "lawsuit",
            "investigation", "breach", "hack", "vulnerable",
        ]

        for kw in positive_keywords:
            if kw in title_lower:
                return "Positive"

        for kw in negative_keywords:
            if kw in title_lower:
                return "Negative"

        return "Neutral"

    def generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        now = datetime.now()
        return [
            {
                "id": 39001234,
                "title": "OpenAI announces GPT-5 with reasoning capabilities",
                "url": "https://openai.com/blog/gpt5",
                "hn_url": "https://news.ycombinator.com/item?id=39001234",
                "score": 1250,
                "comments": 567,
                "author": "pg",
                "time": now.strftime("%Y-%m-%d %H:%M"),
                "source": "Hacker News",
                "priority": "P0",
                "investment_signal": "Positive",
                "is_hot": True,
            },
            {
                "id": 39001235,
                "title": "Anthropic raises $2B at $15B valuation",
                "url": "https://techcrunch.com/anthropic-funding",
                "hn_url": "https://news.ycombinator.com/item?id=39001235",
                "score": 890,
                "comments": 234,
                "author": "dang",
                "time": (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                "source": "Hacker News",
                "priority": "P0",
                "investment_signal": "Positive",
                "is_hot": True,
            },
            {
                "id": 39001236,
                "title": "Show HN: I built an open-source LLM inference engine",
                "url": "https://github.com/example/llm-engine",
                "hn_url": "https://news.ycombinator.com/item?id=39001236",
                "score": 320,
                "comments": 89,
                "author": "builder",
                "time": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
                "source": "Hacker News",
                "priority": "P1",
                "investment_signal": "Neutral",
                "is_hot": True,
            },
            {
                "id": 39001237,
                "title": "EU AI Act enforcement begins in Q3 2026",
                "url": "https://europa.eu/ai-act-update",
                "hn_url": "https://news.ycombinator.com/item?id=39001237",
                "score": 156,
                "comments": 112,
                "author": "eutech",
                "time": (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
                "source": "Hacker News",
                "priority": "P1",
                "investment_signal": "Neutral",
                "is_hot": True,
            },
        ]


def test_hackernews_monitor():
    """测试HN监控器"""
    print("=" * 60)
    print("Hacker News 监控器测试")
    print("=" * 60)

    monitor = HackerNewsMonitor()

    # 测试数据
    print("\n测试1: 测试数据生成")
    test_stories = monitor.generate_test_data()
    print(f"  生成 {len(test_stories)} 条测试stories")

    for story in test_stories:
        print(f"\n  [{story['priority']}] {story['title'][:50]}...")
        print(f"    ⬆️ {story['score']} | 💬 {story['comments']} | {'🔥' if story['is_hot'] else ''}")
        print(f"    信号: {story['investment_signal']}")

    # 测试AI相关判断
    print("\n测试2: AI相关性判断")
    test_cases = [
        ("OpenAI announces GPT-5", "https://openai.com", True),
        ("My weekend project", "https://github.com/me", False),
        ("LLM inference optimization", "https://arxiv.org", True),
        ("New JavaScript framework", "https://js.dev", False),
    ]

    for title, url, expected in test_cases:
        result = monitor._is_ai_related(title, url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {title} → {result} (期望: {expected})")

    # 测试真实API（可能失败）
    print("\n测试3: 真实API获取（可能需要等待）")
    try:
        stories = monitor.fetch_ai_stories(hours=72)
        print(f"  获取到 {len(stories)} 条AI相关stories")

        for story in stories[:3]:
            print(f"\n    [{story['priority']}] {story['title'][:50]}...")
            print(f"      ⬆️ {story['score']} | 💬 {story['comments']}")

    except Exception as e:
        print(f"  API获取失败: {e}")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_hackernews_monitor()
