#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEO Twitter/X 监控

通过Nitter实例的RSS功能监控关键CEO账号:
- Sam Altman (OpenAI)
- Dario Amodei (Anthropic)
- Satya Nadella (Microsoft)
- Sundar Pichai (Google)
- Elon Musk (xAI, Tesla)
- Jensen Huang (NVIDIA)

CEO发言 = 市场信号，需要快速捕捉
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
import re

logger = logging.getLogger(__name__)


class TwitterMonitor:
    """CEO Twitter监控器（通过Nitter RSS）"""

    def __init__(self):
        # Nitter实例列表（公共实例，可能不稳定）
        self.nitter_instances = [
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
            "https://nitter.woodland.cafe",
            "https://nitter.net",
        ]

        # 当前使用的实例索引
        self.current_instance_idx = 0

        # 关键CEO账号
        self.critical_accounts = {
            "sama": {
                "name": "Sam Altman",
                "company": "OpenAI",
                "role": "CEO",
                "priority_boost": 2.0,
            },
            "DarioAmodei": {
                "name": "Dario Amodei",
                "company": "Anthropic",
                "role": "CEO",
                "priority_boost": 1.8,
            },
            "satloganella": {
                "name": "Satya Nadella",
                "company": "Microsoft",
                "role": "CEO",
                "priority_boost": 1.5,
            },
            "sundarpichai": {
                "name": "Sundar Pichai",
                "company": "Google",
                "role": "CEO",
                "priority_boost": 1.5,
            },
            "elonmusk": {
                "name": "Elon Musk",
                "company": "xAI/Tesla",
                "role": "CEO",
                "priority_boost": 1.8,
            },
            "jensen_huang": {
                "name": "Jensen Huang",
                "company": "NVIDIA",
                "role": "CEO",
                "priority_boost": 1.5,
            },
            "demaborja": {
                "name": "Demis Hassabis",
                "company": "DeepMind",
                "role": "CEO",
                "priority_boost": 1.5,
            },
            "ylecun": {
                "name": "Yann LeCun",
                "company": "Meta AI",
                "role": "Chief AI Scientist",
                "priority_boost": 1.3,
            },
        }

        # P0触发关键词（重大公告）
        self.p0_keywords = [
            "announcing", "excited to announce", "launching", "released",
            "new model", "gpt-5", "gpt-4", "claude", "gemini",
            "partnership", "deal", "acquisition", "merger",
            "stepping down", "resign", "leaving",
            "regulatory", "ftc", "doj", "lawsuit",
            "ipo", "funding", "billion", "investment",
        ]

        # P1触发关键词
        self.p1_keywords = [
            "update", "improvement", "feature", "api",
            "pricing", "enterprise", "customers",
            "hiring", "team", "growth",
            "safety", "alignment", "responsible",
        ]

        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AI Investment Monitor/1.0)"
        }

    def _get_nitter_rss_url(self, username: str) -> str:
        """获取Nitter RSS URL"""
        instance = self.nitter_instances[self.current_instance_idx]
        return f"{instance}/{username}/rss"

    def _try_next_instance(self):
        """切换到下一个Nitter实例"""
        self.current_instance_idx = (self.current_instance_idx + 1) % len(self.nitter_instances)
        logger.info(f"切换到Nitter实例: {self.nitter_instances[self.current_instance_idx]}")

    def fetch_account_tweets(self, username: str, hours: int = 24) -> List[Dict]:
        """
        获取单个账号的最近推文

        Args:
            username: Twitter用户名
            hours: 时间范围

        Returns:
            推文列表
        """
        account_info = self.critical_accounts.get(username, {})
        tweets = []

        # 尝试多个Nitter实例
        for attempt in range(len(self.nitter_instances)):
            try:
                rss_url = self._get_nitter_rss_url(username)
                feed = feedparser.parse(rss_url)

                if feed.bozo and not feed.entries:
                    # RSS解析失败，尝试下一个实例
                    self._try_next_instance()
                    continue

                cutoff_time = datetime.now() - timedelta(hours=hours)

                for entry in feed.entries[:20]:  # 最多20条
                    try:
                        # 解析时间
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        else:
                            published = datetime.now()

                        if published < cutoff_time:
                            continue

                        # 清理推文内容
                        content = self._clean_tweet_content(entry.get('description', ''))
                        title = entry.get('title', '')[:200]

                        # 计算优先级
                        priority = self._calculate_priority(content, account_info)

                        # 提取投资信号
                        signal = self._extract_signal(content)

                        tweet = {
                            "username": username,
                            "author": account_info.get("name", username),
                            "company": account_info.get("company", "Unknown"),
                            "role": account_info.get("role", "Unknown"),
                            "content": content,
                            "title": title,
                            "link": entry.get('link', ''),
                            "published": published.strftime("%Y-%m-%d %H:%M"),
                            "source": "Twitter/X",
                            "priority": priority,
                            "investment_signal": signal,
                        }

                        tweets.append(tweet)

                    except Exception as e:
                        logger.debug(f"解析推文失败: {e}")
                        continue

                # 成功获取，跳出重试循环
                if tweets or feed.entries:
                    break

            except Exception as e:
                logger.warning(f"获取 @{username} 推文失败 (实例{attempt+1}): {e}")
                self._try_next_instance()
                time.sleep(1)

        return tweets

    def fetch_all_accounts(self, hours: int = 24) -> List[Dict]:
        """
        获取所有关键账号的推文

        Args:
            hours: 时间范围

        Returns:
            所有推文列表
        """
        all_tweets = []

        for username in self.critical_accounts.keys():
            try:
                tweets = self.fetch_account_tweets(username, hours)
                all_tweets.extend(tweets)
                time.sleep(1)  # 礼貌延迟
            except Exception as e:
                logger.error(f"获取 @{username} 失败: {e}")

        # 按优先级和时间排序
        all_tweets.sort(
            key=lambda x: (
                0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                x["published"]
            ),
            reverse=True
        )

        logger.info(f"Twitter: 获取到 {len(all_tweets)} 条推文")
        return all_tweets

    def _clean_tweet_content(self, html_content: str) -> str:
        """清理推文HTML内容"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', html_content)
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        # 限制长度
        return text[:500]

    def _calculate_priority(self, content: str, account_info: Dict) -> str:
        """计算推文优先级"""
        content_lower = content.lower()

        # P0: 重大公告关键词
        for keyword in self.p0_keywords:
            if keyword.lower() in content_lower:
                return "P0"

        # P1: 一般重要关键词
        for keyword in self.p1_keywords:
            if keyword.lower() in content_lower:
                return "P1"

        # 基于账号重要性
        boost = account_info.get("priority_boost", 1.0)
        if boost >= 1.8:
            return "P1"

        return "P2"

    def _extract_signal(self, content: str) -> str:
        """提取投资信号"""
        content_lower = content.lower()

        # 正面信号
        positive_keywords = [
            "excited", "announcing", "launching", "growth",
            "milestone", "record", "partnership", "deal",
        ]

        # 负面信号
        negative_keywords = [
            "concern", "issue", "problem", "delay",
            "stepping down", "leaving", "lawsuit", "investigation",
        ]

        for kw in positive_keywords:
            if kw in content_lower:
                return "Positive"

        for kw in negative_keywords:
            if kw in content_lower:
                return "Negative"

        return "Neutral"

    def generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        now = datetime.now()
        return [
            {
                "username": "sama",
                "author": "Sam Altman",
                "company": "OpenAI",
                "role": "CEO",
                "content": "Excited to announce GPT-5 is now available to all ChatGPT Plus users. This is our most capable model yet.",
                "title": "GPT-5 announcement",
                "link": "https://twitter.com/sama/status/123456",
                "published": now.strftime("%Y-%m-%d %H:%M"),
                "source": "Twitter/X",
                "priority": "P0",
                "investment_signal": "Positive",
            },
            {
                "username": "satyanadella",
                "author": "Satya Nadella",
                "company": "Microsoft",
                "role": "CEO",
                "content": "Our partnership with OpenAI continues to deliver incredible value for our customers. Azure AI revenue up 50% YoY.",
                "title": "Azure AI growth",
                "link": "https://twitter.com/satyanadella/status/789012",
                "published": (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                "source": "Twitter/X",
                "priority": "P1",
                "investment_signal": "Positive",
            },
            {
                "username": "elonmusk",
                "author": "Elon Musk",
                "company": "xAI/Tesla",
                "role": "CEO",
                "content": "Grok 2 training is complete. Will be released next week. Much better at coding and math.",
                "title": "Grok 2 release",
                "link": "https://twitter.com/elonmusk/status/345678",
                "published": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
                "source": "Twitter/X",
                "priority": "P0",
                "investment_signal": "Positive",
            },
        ]


def test_twitter_monitor():
    """测试Twitter监控器"""
    print("=" * 60)
    print("Twitter/X 监控器测试")
    print("=" * 60)

    monitor = TwitterMonitor()

    # 测试数据
    print("\n测试1: 测试数据生成")
    test_tweets = monitor.generate_test_data()
    print(f"  生成 {len(test_tweets)} 条测试推文")

    for tweet in test_tweets:
        print(f"\n  [{tweet['priority']}] @{tweet['username']} ({tweet['company']})")
        print(f"    {tweet['content'][:80]}...")
        print(f"    信号: {tweet['investment_signal']}")

    # 测试真实获取（可能失败，Nitter实例不稳定）
    print("\n测试2: 真实数据获取（可能失败）")
    try:
        # 只测试一个账号
        tweets = monitor.fetch_account_tweets("sama", hours=72)
        print(f"  @sama: 获取到 {len(tweets)} 条推文")

        for tweet in tweets[:2]:
            print(f"\n    [{tweet['priority']}] {tweet['content'][:60]}...")

    except Exception as e:
        print(f"  获取失败（Nitter实例可能不可用）: {e}")

    # 测试优先级计算
    print("\n测试3: 优先级计算")
    test_cases = [
        ("Excited to announce our new model GPT-5", "P0"),
        ("We are hiring ML engineers", "P1"),
        ("Great weather today", "P2"),
        ("Stepping down from my role as CEO", "P0"),
    ]

    for content, expected in test_cases:
        priority = monitor._calculate_priority(content, {"priority_boost": 1.0})
        status = "✅" if priority == expected else "❌"
        print(f"  {status} '{content[:40]}...' → {priority} (期望: {expected})")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_twitter_monitor()
