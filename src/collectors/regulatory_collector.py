#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监管机构监控模块

监控美国和欧盟监管机构的AI相关行动：
- FTC (联邦贸易委员会): 反垄断、消费者保护
- DOJ (司法部): 刑事调查、反垄断
- EU Commission: AI法案、数字市场法
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict
import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RegulatoryCollector:
    """监管机构采集器"""

    def __init__(self):
        # FTC RSS源
        self.ftc_rss = "https://www.ftc.gov/feeds/ftc-news.xml"
        self.ftc_base = "https://www.ftc.gov"

        # DOJ RSS源
        self.doj_rss = "https://www.justice.gov/feeds/opa/justice-news.xml"
        self.doj_base = "https://www.justice.gov"

        # EU Commission (无官方RSS，需爬取)
        self.eu_news = "https://ec.europa.eu/commission/presscorner/api/documents"

        # AI相关关键词
        self.ai_keywords = [
            "artificial intelligence", "AI", "machine learning",
            "algorithmic", "algorithm", "automated decision",
            # 公司名
            "OpenAI", "ChatGPT", "GPT",
            "Google", "Alphabet", "DeepMind",
            "Microsoft", "Bing",
            "Meta", "Facebook",
            "Amazon", "AWS",
            "Anthropic", "Claude",
            "NVIDIA",
        ]

        # 高敏感度关键词（触发P0）
        self.critical_keywords = [
            "lawsuit", "investigation", "charges", "criminal",
            "antitrust", "monopoly", "anticompetitive",
            "fine", "penalty", "settlement",
            "ban", "prohibited", "injunction",
            "consent decree", "enforcement action",
        ]

        self.headers = {
            "User-Agent": "AI Investment News Analysis System/1.1"
        }

    def fetch_ftc_news(self, hours: int = 24) -> List[Dict]:
        """
        获取FTC最新新闻

        Args:
            hours: 时间范围（小时）

        Returns:
            新闻列表
        """
        try:
            logger.info("开始获取FTC最新新闻...")

            feed = feedparser.parse(self.ftc_rss)

            if not feed.entries:
                logger.warning("未获取到FTC新闻")
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            news_list = []

            for entry in feed.entries:
                try:
                    # 解析时间
                    published = datetime(*entry.published_parsed[:6])

                    if published < cutoff_time:
                        continue

                    # 基本信息
                    news = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": published.strftime("%Y-%m-%d %H:%M"),
                        "summary": entry.summary if hasattr(entry, 'summary') else "",
                        "source": "FTC",
                        "agency": "Federal Trade Commission",
                    }

                    # 关键词过滤
                    if not self._is_ai_related(news):
                        continue

                    # 获取全文
                    full_content = self._fetch_ftc_article(news["link"])
                    news["content"] = full_content

                    # 计算优先级
                    news["priority"] = self._calculate_priority(news)

                    news_list.append(news)

                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"解析FTC新闻条目失败: {e}")
                    continue

            logger.info(f"获取到 {len(news_list)} 条FTC AI相关新闻")
            return news_list

        except Exception as e:
            logger.error(f"获取FTC新闻失败: {e}")
            return []

    def fetch_doj_news(self, hours: int = 24) -> List[Dict]:
        """
        获取DOJ最新新闻

        Args:
            hours: 时间范围（小时）

        Returns:
            新闻列表
        """
        try:
            logger.info("开始获取DOJ最新新闻...")

            feed = feedparser.parse(self.doj_rss)

            if not feed.entries:
                logger.warning("未获取到DOJ新闻")
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            news_list = []

            for entry in feed.entries:
                try:
                    # 解析时间
                    published = datetime(*entry.published_parsed[:6])

                    if published < cutoff_time:
                        continue

                    news = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": published.strftime("%Y-%m-%d %H:%M"),
                        "summary": entry.get('summary', ''),
                        "source": "DOJ",
                        "agency": "Department of Justice",
                    }

                    # 关键词过滤
                    if not self._is_ai_related(news):
                        continue

                    # 获取全文
                    full_content = self._fetch_doj_article(news["link"])
                    news["content"] = full_content

                    # 计算优先级
                    news["priority"] = self._calculate_priority(news)

                    news_list.append(news)

                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"解析DOJ新闻条目失败: {e}")
                    continue

            logger.info(f"获取到 {len(news_list)} 条DOJ AI相关新闻")
            return news_list

        except Exception as e:
            logger.error(f"获取DOJ新闻失败: {e}")
            return []

    def fetch_eu_news(self, hours: int = 24) -> List[Dict]:
        """
        获取EU Commission最新新闻

        Args:
            hours: 时间范围（小时）

        Returns:
            新闻列表
        """
        try:
            logger.info("开始获取EU Commission最新新闻...")

            # EU API参数
            params = {
                "pagenumber": 1,
                "pagesize": 50,
                "language": "en",
            }

            response = requests.get(
                self.eu_news,
                params=params,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("results", [])

            cutoff_time = datetime.now() - timedelta(hours=hours)
            news_list = []

            for item in items:
                try:
                    # 解析时间
                    published_str = item.get("publicationDate", "")
                    if not published_str:
                        continue

                    # ISO格式: 2024-01-20T10:30:00
                    published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))

                    if published.replace(tzinfo=None) < cutoff_time:
                        continue

                    news = {
                        "title": item.get("title", {}).get("name", ""),
                        "link": f"https://ec.europa.eu/commission/presscorner/detail/en/{item.get('reference', '')}",
                        "published": published.strftime("%Y-%m-%d %H:%M"),
                        "summary": item.get("headline", {}).get("name", ""),
                        "source": "EU Commission",
                        "agency": "European Commission",
                    }

                    # 关键词过滤
                    if not self._is_ai_related(news):
                        continue

                    # 内容
                    news["content"] = item.get("text", {}).get("name", "")

                    # 计算优先级
                    news["priority"] = self._calculate_priority(news)

                    news_list.append(news)

                except Exception as e:
                    logger.error(f"解析EU新闻条目失败: {e}")
                    continue

            logger.info(f"获取到 {len(news_list)} 条EU AI相关新闻")
            return news_list

        except Exception as e:
            logger.error(f"获取EU新闻失败: {e}")
            return []

    def fetch_all_regulatory_news(self, hours: int = 24) -> List[Dict]:
        """
        获取所有监管机构新闻

        Args:
            hours: 时间范围（小时）

        Returns:
            合并后的新闻列表
        """
        all_news = []

        # FTC
        ftc_news = self.fetch_ftc_news(hours)
        all_news.extend(ftc_news)

        # DOJ
        doj_news = self.fetch_doj_news(hours)
        all_news.extend(doj_news)

        # EU
        eu_news = self.fetch_eu_news(hours)
        all_news.extend(eu_news)

        # 按优先级和时间排序
        all_news.sort(key=lambda x: (
            0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
            x["published"]
        ), reverse=True)

        logger.info(f"总计获取 {len(all_news)} 条监管新闻")
        return all_news

    def _is_ai_related(self, news: Dict) -> bool:
        """判断是否AI相关"""
        text = f"{news['title']} {news['summary']}".lower()

        for keyword in self.ai_keywords:
            if keyword.lower() in text:
                return True

        return False

    def _calculate_priority(self, news: Dict) -> str:
        """
        计算优先级

        Returns:
            "P0" | "P1" | "P2"
        """
        text = f"{news['title']} {news['summary']} {news.get('content', '')}".lower()

        # 检查高敏感度关键词
        for keyword in self.critical_keywords:
            if keyword.lower() in text:
                return "P0"

        # 如果标题包含公司名，提升优先级
        major_companies = ["openai", "google", "microsoft", "meta", "amazon", "nvidia"]
        title_lower = news['title'].lower()

        for company in major_companies:
            if company in title_lower:
                return "P1"

        return "P2"

    def _fetch_ftc_article(self, url: str) -> str:
        """获取FTC文章全文"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # FTC文章主体在article标签中
            article = soup.find('article')
            if article:
                # 移除script和style
                for tag in article(['script', 'style']):
                    tag.decompose()
                return article.get_text(separator=' ', strip=True)

            return ""

        except Exception as e:
            logger.error(f"获取FTC文章失败 {url}: {e}")
            return ""

    def _fetch_doj_article(self, url: str) -> str:
        """获取DOJ文章全文"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # DOJ文章主体
            content = soup.find('div', class_='field--name-body')
            if content:
                for tag in content(['script', 'style']):
                    tag.decompose()
                return content.get_text(separator=' ', strip=True)

            return ""

        except Exception as e:
            logger.error(f"获取DOJ文章失败 {url}: {e}")
            return ""


def test_regulatory_collector():
    """测试监管采集器"""
    print("=" * 60)
    print("监管机构采集器测试")
    print("=" * 60)

    collector = RegulatoryCollector()

    # 测试获取最近24小时新闻
    print("\n测试: 获取最近24小时的监管新闻...")
    news_list = collector.fetch_all_regulatory_news(hours=24)

    print(f"\n获取到 {len(news_list)} 条监管新闻")

    # 按来源统计
    sources = {}
    for news in news_list:
        source = news['source']
        sources[source] = sources.get(source, 0) + 1

    print("\n来源统计:")
    for source, count in sources.items():
        print(f"  {source}: {count} 条")

    # 按优先级统计
    priorities = {}
    for news in news_list:
        priority = news['priority']
        priorities[priority] = priorities.get(priority, 0) + 1

    print("\n优先级统计:")
    for priority in ["P0", "P1", "P2"]:
        count = priorities.get(priority, 0)
        print(f"  {priority}: {count} 条")

    # 显示前3条
    print("\n前3条新闻:")
    for i, news in enumerate(news_list[:3], 1):
        print(f"\n新闻 {i}:")
        print(f"  标题: {news['title']}")
        print(f"  来源: {news['source']}")
        print(f"  时间: {news['published']}")
        print(f"  优先级: {news['priority']}")
        print(f"  链接: {news['link']}")
        print(f"  摘要: {news['summary'][:200]}...")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_regulatory_collector()
