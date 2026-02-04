#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大厂AI官方博客监控

监控AI巨头的官方博客，捕捉：
- 产品发布/更新
- 技术突破公告
- 战略合作
- 重大API变更

数据源:
- Google AI Blog (ai.googleblog.com)
- OpenAI Blog (openai.com/blog)
- Meta AI Blog (ai.meta.com/blog)
- Microsoft AI Blog (blogs.microsoft.com/ai)
- NVIDIA Blog (blogs.nvidia.com)
- Anthropic News (anthropic.com/news)
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BlogCollector:
    """大厂AI博客采集器"""

    def __init__(self):
        # 博客RSS源配置
        self.blog_sources = {
            "google_ai": {
                "name": "Google AI Blog",
                "company": "Google",
                "rss": "https://blog.google/technology/ai/rss/",
                "alt_rss": "https://ai.googleblog.com/feeds/posts/default",
                "priority_boost": 1.5,  # 优先级提升因子
            },
            "openai": {
                "name": "OpenAI Blog",
                "company": "OpenAI",
                "rss": "https://openai.com/blog/rss.xml",
                "alt_url": "https://openai.com/blog",
                "priority_boost": 2.0,  # 最高优先
            },
            "meta_ai": {
                "name": "Meta AI Blog",
                "company": "Meta",
                "rss": "https://ai.meta.com/blog/rss/",
                "alt_url": "https://ai.meta.com/blog/",
                "priority_boost": 1.5,
            },
            "microsoft_ai": {
                "name": "Microsoft AI Blog",
                "company": "Microsoft",
                "rss": "https://blogs.microsoft.com/ai/feed/",
                "priority_boost": 1.5,
            },
            "nvidia": {
                "name": "NVIDIA Blog",
                "company": "NVIDIA",
                "rss": "https://blogs.nvidia.com/feed/",
                "priority_boost": 1.3,
            },
            "anthropic": {
                "name": "Anthropic News",
                "company": "Anthropic",
                "rss": "https://www.anthropic.com/news/rss",
                "alt_url": "https://www.anthropic.com/news",
                "priority_boost": 1.8,
            },
            "deepmind": {
                "name": "DeepMind Blog",
                "company": "DeepMind",
                "rss": "https://www.deepmind.com/blog/rss.xml",
                "alt_url": "https://www.deepmind.com/blog",
                "priority_boost": 1.5,
            },
        }

        # P0触发关键词（产品发布、重大更新）
        self.p0_keywords = [
            # 产品发布
            "introducing", "announcing", "launch", "release", "unveil",
            "new model", "gpt-5", "gpt-4", "claude", "gemini", "llama",
            # 重大更新
            "major update", "breakthrough", "state-of-the-art",
            "now available", "general availability", "ga release",
            # API变更
            "api", "pricing", "rate limit", "deprecat",
            # 中文关键词
            "发布", "推出", "上线", "更新", "升级",
        ]

        # P1触发关键词（技术文章、研究）
        self.p1_keywords = [
            "research", "paper", "study", "benchmark",
            "performance", "capability", "safety", "alignment",
            "partnership", "collaboration", "integration",
        ]

        self.headers = {
            "User-Agent": "AI Investment News Monitor/1.0"
        }

    def fetch_all_blogs(self, hours: int = 24) -> List[Dict]:
        """
        获取所有博客的最新文章

        Args:
            hours: 时间范围（小时）

        Returns:
            博客文章列表
        """
        all_posts = []

        for source_id, config in self.blog_sources.items():
            try:
                posts = self._fetch_blog(source_id, config, hours)
                all_posts.extend(posts)
                time.sleep(0.5)  # 礼貌延迟
            except Exception as e:
                logger.error(f"获取 {config['name']} 失败: {e}")

        # 按优先级和时间排序
        all_posts.sort(
            key=lambda x: (
                0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                x["published"]
            ),
            reverse=True
        )

        logger.info(f"总计获取 {len(all_posts)} 篇博客文章")
        return all_posts

    def _fetch_blog(self, source_id: str, config: Dict, hours: int) -> List[Dict]:
        """获取单个博客的文章"""
        posts = []

        # 尝试RSS
        rss_url = config.get("rss")
        if rss_url:
            feed = feedparser.parse(rss_url)

            if feed.entries:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                for entry in feed.entries[:20]:  # 最多20篇
                    try:
                        # 解析时间
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                            published = datetime(*entry.updated_parsed[:6])
                        else:
                            published = datetime.now()

                        if published < cutoff_time:
                            continue

                        post = self._parse_entry(entry, config, published)
                        posts.append(post)

                    except Exception as e:
                        logger.debug(f"解析文章失败: {e}")
                        continue

                logger.info(f"{config['name']}: 获取到 {len(posts)} 篇文章")
            else:
                # RSS失败，尝试备用RSS
                alt_rss = config.get("alt_rss")
                if alt_rss:
                    return self._fetch_blog(
                        source_id,
                        {**config, "rss": alt_rss, "alt_rss": None},
                        hours
                    )
                logger.warning(f"{config['name']}: RSS feed为空")

        return posts

    def _parse_entry(self, entry, config: Dict, published: datetime) -> Dict:
        """解析RSS条目"""
        title = entry.title if hasattr(entry, 'title') else ""
        summary = entry.summary if hasattr(entry, 'summary') else ""
        link = entry.link if hasattr(entry, 'link') else ""

        # 清理HTML
        if summary:
            soup = BeautifulSoup(summary, 'html.parser')
            summary = soup.get_text(separator=' ', strip=True)[:500]

        # 计算优先级
        priority = self._calculate_priority(title, summary, config)

        # 提取投资信号
        signal = self._extract_signal(title, summary)

        return {
            "title": title,
            "summary": summary,
            "link": link,
            "published": published.strftime("%Y-%m-%d %H:%M"),
            "source": config["name"],
            "company": config["company"],
            "source_id": config.get("source_id", "blog"),
            "priority": priority,
            "investment_signal": signal,
            "content_type": self._detect_content_type(title, summary),
        }

    def _calculate_priority(self, title: str, summary: str, config: Dict) -> str:
        """计算文章优先级"""
        text = f"{title} {summary}".lower()

        # P0: 产品发布、重大更新
        for keyword in self.p0_keywords:
            if keyword.lower() in text:
                return "P0"

        # P1: 技术文章、研究
        for keyword in self.p1_keywords:
            if keyword.lower() in text:
                return "P1"

        # 基于公司优先级提升
        boost = config.get("priority_boost", 1.0)
        if boost >= 1.8:  # OpenAI, Anthropic
            return "P1"

        return "P2"

    def _extract_signal(self, title: str, summary: str) -> str:
        """提取投资信号"""
        text = f"{title} {summary}".lower()

        # 正面信号
        positive_keywords = [
            "launch", "release", "breakthrough", "partnership",
            "growth", "expand", "milestone", "record",
            "发布", "突破", "合作", "增长"
        ]

        # 负面信号
        negative_keywords = [
            "delay", "issue", "problem", "concern", "risk",
            "deprecate", "discontinue", "limit",
            "延迟", "问题", "风险", "下线"
        ]

        for kw in positive_keywords:
            if kw in text:
                return "Positive"

        for kw in negative_keywords:
            if kw in text:
                return "Negative"

        return "Neutral"

    def _detect_content_type(self, title: str, summary: str) -> str:
        """检测内容类型"""
        text = f"{title} {summary}".lower()

        if any(kw in text for kw in ["launch", "release", "introducing", "announcing", "发布"]):
            return "product_launch"

        if any(kw in text for kw in ["research", "paper", "study", "研究"]):
            return "research"

        if any(kw in text for kw in ["api", "developer", "sdk", "开发者"]):
            return "api_update"

        if any(kw in text for kw in ["partner", "collaborat", "合作"]):
            return "partnership"

        if any(kw in text for kw in ["safety", "responsible", "安全"]):
            return "safety"

        return "general"

    def generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        now = datetime.now()
        return [
            {
                "title": "Introducing GPT-5: Our Most Capable Model Yet",
                "summary": "Today we're launching GPT-5, featuring breakthrough capabilities in reasoning, coding, and multimodal understanding. Now available via API.",
                "link": "https://openai.com/blog/gpt-5",
                "published": now.strftime("%Y-%m-%d %H:%M"),
                "source": "OpenAI Blog",
                "company": "OpenAI",
                "priority": "P0",
                "investment_signal": "Positive",
                "content_type": "product_launch",
            },
            {
                "title": "Gemini 2.0: Next Generation AI for Everyone",
                "summary": "Google announces Gemini 2.0 with state-of-the-art performance across benchmarks. General availability starting today.",
                "link": "https://blog.google/technology/ai/gemini-2",
                "published": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                "source": "Google AI Blog",
                "company": "Google",
                "priority": "P0",
                "investment_signal": "Positive",
                "content_type": "product_launch",
            },
            {
                "title": "Claude API Pricing Update",
                "summary": "We're reducing Claude API prices by 50% for all tiers, effective immediately. Enterprise customers will see additional volume discounts.",
                "link": "https://anthropic.com/news/pricing",
                "published": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
                "source": "Anthropic News",
                "company": "Anthropic",
                "priority": "P0",
                "investment_signal": "Positive",
                "content_type": "api_update",
            },
            {
                "title": "Research: Scaling Laws for AI Agents",
                "summary": "New research paper exploring how agent capabilities scale with compute and data. Key findings suggest...",
                "link": "https://ai.meta.com/research/scaling",
                "published": (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M"),
                "source": "Meta AI Blog",
                "company": "Meta",
                "priority": "P1",
                "investment_signal": "Neutral",
                "content_type": "research",
            },
        ]


def test_blog_collector():
    """测试博客采集器"""
    print("=" * 60)
    print("大厂博客采集器测试")
    print("=" * 60)

    collector = BlogCollector()

    # 使用测试数据
    print("\n测试1: 测试数据生成")
    test_posts = collector.generate_test_data()
    print(f"  生成 {len(test_posts)} 篇测试文章")

    for post in test_posts:
        print(f"\n  [{post['priority']}] {post['company']}: {post['title'][:50]}...")
        print(f"    信号: {post['investment_signal']} | 类型: {post['content_type']}")

    # 测试优先级计算
    print("\n测试2: 优先级计算")
    test_cases = [
        ("Introducing New Model", "Launch of our latest AI", "P0"),
        ("Research Paper on Safety", "Study examines alignment", "P1"),
        ("Team Update", "Welcome our new members", "P2"),
    ]

    for title, summary, expected in test_cases:
        priority = collector._calculate_priority(
            title, summary,
            {"priority_boost": 1.0}
        )
        status = "✅" if priority == expected else "❌"
        print(f"  {status} '{title[:30]}' → {priority} (期望: {expected})")

    # 测试真实RSS（如果网络可用）
    print("\n测试3: 真实RSS获取（可能为空）")
    try:
        posts = collector.fetch_all_blogs(hours=72)  # 3天内
        print(f"  获取到 {len(posts)} 篇真实文章")

        # 按来源统计
        sources = {}
        for post in posts:
            src = post["source"]
            sources[src] = sources.get(src, 0) + 1

        if sources:
            print("  来源统计:")
            for src, count in sorted(sources.items(), key=lambda x: -x[1]):
                print(f"    {src}: {count}")

    except Exception as e:
        print(f"  RSS获取失败（网络问题）: {e}")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_blog_collector()
