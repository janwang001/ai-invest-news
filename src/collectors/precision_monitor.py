#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精准监控调度器 v2.0

统一调度高敏感度数据源的监控:
- SEC EDGAR: 每5分钟检查（8-K, S-1等重大事件）
- 监管机构: 每15分钟检查（FTC, DOJ, EU）
- 大厂博客: 每30分钟检查（产品发布、API更新）
- 股价异动: 每5分钟检查（涨跌>5%触发P0）
- CEO Twitter: 每30分钟检查（通过Nitter RSS）
- GitHub爆款: 每小时检查（AI相关趋势项目）
- Hacker News: 每30分钟检查（AI热门讨论）
- 生成统一警报并按优先级分发

Week 1: SEC EDGAR + 监管机构
Week 2: 大厂博客 + 股价异动 + Twitter + GitHub + HN + 通知系统
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

from .sec_edgar_collector import SECEdgarCollector
from .regulatory_collector import RegulatoryCollector
from .blog_collector import BlogCollector
from .stock_monitor import StockMonitor, StockAlert
from .twitter_monitor import TwitterMonitor
from .github_monitor import GitHubMonitor
from .hackernews_monitor import HackerNewsMonitor
from .alert_system import AlertSystem, Alert, AlertPriority
from .notifier import Notifier, Notification

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """监控配置"""
    # SEC配置
    sec_enabled: bool = True
    sec_interval_minutes: int = 5  # 每5分钟检查
    sec_lookback_hours: int = 1    # 回看1小时

    # 监管配置
    regulatory_enabled: bool = True
    regulatory_interval_minutes: int = 15  # 每15分钟检查
    regulatory_lookback_hours: int = 2     # 回看2小时

    # 博客配置 (Week 2)
    blog_enabled: bool = True
    blog_interval_minutes: int = 30  # 每30分钟检查
    blog_lookback_hours: int = 24    # 回看24小时

    # 股价配置 (Week 2)
    stock_enabled: bool = True
    stock_interval_minutes: int = 5  # 每5分钟检查

    # Twitter配置 (Week 2)
    twitter_enabled: bool = True
    twitter_interval_minutes: int = 30  # 每30分钟检查
    twitter_lookback_hours: int = 24    # 回看24小时

    # GitHub配置 (Week 2)
    github_enabled: bool = True
    github_interval_minutes: int = 60  # 每小时检查
    github_lookback_days: int = 7      # 回看7天

    # Hacker News配置 (Week 2)
    hackernews_enabled: bool = True
    hackernews_interval_minutes: int = 30  # 每30分钟检查
    hackernews_lookback_hours: int = 24    # 回看24小时

    # 通知配置 (Week 2)
    notify_console: bool = True
    notify_file: bool = True
    notify_file_dir: str = "output/alerts"
    webhook_url: Optional[str] = None
    webhook_platform: str = "generic"  # slack/wecom/dingtalk/generic

    # 测试模式
    test_mode: bool = False


class PrecisionMonitor:
    """
    精准监控器 v2.0

    负责调度各数据源的监控，生成统一警报并推送通知
    """

    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()

        # 初始化采集器 (Week 1)
        self.sec_collector = SECEdgarCollector()
        self.regulatory_collector = RegulatoryCollector()

        # 初始化采集器 (Week 2)
        self.blog_collector = BlogCollector()
        self.stock_monitor = StockMonitor()
        self.twitter_monitor = TwitterMonitor()
        self.github_monitor = GitHubMonitor()
        self.hackernews_monitor = HackerNewsMonitor()

        # 警报系统
        self.alert_system = AlertSystem()

        # 通知系统 (Week 2)
        self.notifier = self._setup_notifier()

        # 回调函数（用于警报通知）
        self.on_p0_alert: Optional[Callable[[Alert], None]] = None
        self.on_p1_alert: Optional[Callable[[Alert], None]] = None

        # 统计
        self.stats = {
            "sec_checks": 0,
            "regulatory_checks": 0,
            "blog_checks": 0,
            "stock_checks": 0,
            "twitter_checks": 0,
            "github_checks": 0,
            "hackernews_checks": 0,
            "alerts_generated": 0,
            "notifications_sent": 0,
            "last_sec_check": None,
            "last_regulatory_check": None,
            "last_blog_check": None,
            "last_stock_check": None,
            "last_twitter_check": None,
            "last_github_check": None,
            "last_hackernews_check": None,
            "errors": []
        }

    def _setup_notifier(self) -> Notifier:
        """设置通知系统"""
        notifier = Notifier()

        # 清除默认控制台（如果不需要）
        if not self.config.notify_console:
            notifier.channels = []

        # 添加文件渠道
        if self.config.notify_file:
            notifier.add_file_channel(self.config.notify_file_dir)

        # 添加Webhook
        if self.config.webhook_url:
            notifier.add_webhook(
                self.config.webhook_url,
                self.config.webhook_platform
            )

        return notifier

    def run_once(self) -> Dict:
        """
        执行一次完整的监控检查

        Returns:
            包含所有警报的结果字典
        """
        logger.info("=" * 60)
        logger.info(f"开始精准监控 v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "sec_filings": [],
            "regulatory_news": [],
            "blog_posts": [],
            "stock_alerts": [],
            "twitter_posts": [],
            "github_repos": [],
            "hackernews_stories": [],
            "alerts": {
                "p0": [],
                "p1": [],
                "p2": []
            }
        }

        # 清空之前的警报
        self.alert_system.clear_alerts()

        # 1. SEC EDGAR 监控 (Week 1)
        if self.config.sec_enabled:
            sec_results = self._check_sec()
            results["sec_filings"] = sec_results

        # 2. 监管机构监控 (Week 1)
        if self.config.regulatory_enabled:
            regulatory_results = self._check_regulatory()
            results["regulatory_news"] = regulatory_results

        # 3. 大厂博客监控 (Week 2)
        if self.config.blog_enabled:
            blog_results = self._check_blogs()
            results["blog_posts"] = blog_results

        # 4. 股价异动监控 (Week 2)
        if self.config.stock_enabled:
            stock_results = self._check_stocks()
            results["stock_alerts"] = stock_results

        # 5. CEO Twitter监控 (Week 2)
        if self.config.twitter_enabled:
            twitter_results = self._check_twitter()
            results["twitter_posts"] = twitter_results

        # 6. GitHub爆款监控 (Week 2)
        if self.config.github_enabled:
            github_results = self._check_github()
            results["github_repos"] = github_results

        # 7. Hacker News监控 (Week 2)
        if self.config.hackernews_enabled:
            hackernews_results = self._check_hackernews()
            results["hackernews_stories"] = hackernews_results

        # 8. 收集警报
        results["alerts"]["p0"] = [a.to_dict() for a in self.alert_system.get_p0_alerts()]
        results["alerts"]["p1"] = [a.to_dict() for a in self.alert_system.get_p1_alerts()]
        results["alerts"]["p2"] = [a.to_dict() for a in self.alert_system.get_p2_alerts()]

        # 9. 发送通知 (Week 2)
        self._send_notifications()

        # 10. 触发P0回调（立即通知）
        for alert in self.alert_system.get_p0_alerts():
            if self.on_p0_alert:
                try:
                    self.on_p0_alert(alert)
                except Exception as e:
                    logger.error(f"P0回调失败: {e}")

        # 11. 输出汇总
        print(self.alert_system.generate_alert_summary())

        logger.info(f"监控完成 | P0: {len(results['alerts']['p0'])}, "
                   f"P1: {len(results['alerts']['p1'])}, "
                   f"P2: {len(results['alerts']['p2'])}")

        return results

    def _check_sec(self) -> List[Dict]:
        """检查SEC EDGAR"""
        logger.info("检查 SEC EDGAR...")
        self.stats["sec_checks"] += 1
        self.stats["last_sec_check"] = datetime.now().isoformat()

        try:
            # 获取最近文件
            filings = self.sec_collector.fetch_recent_filings(
                hours=self.config.sec_lookback_hours,
                test_mode=self.config.test_mode
            )

            logger.info(f"SEC: 获取到 {len(filings)} 个文件")

            # 处理每个文件，生成警报
            for filing in filings:
                # 解析8-K
                if filing.get("filing_type") in ["8-K", "8-K/A"]:
                    filing = self.sec_collector.parse_form_8k(filing)

                # 解析Form D
                if filing.get("filing_type") in ["D", "D/A"]:
                    filing = self.sec_collector.parse_form_d(filing)

                # 生成警报
                alert = self.alert_system.process_sec_filing(filing)
                if alert:
                    self.stats["alerts_generated"] += 1

            return filings

        except Exception as e:
            logger.error(f"SEC检查失败: {e}")
            self.stats["errors"].append({
                "source": "SEC",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_regulatory(self) -> List[Dict]:
        """检查监管机构"""
        logger.info("检查监管机构 (FTC/DOJ/EU)...")
        self.stats["regulatory_checks"] += 1
        self.stats["last_regulatory_check"] = datetime.now().isoformat()

        try:
            # 获取所有监管新闻
            news_list = self.regulatory_collector.fetch_all_regulatory_news(
                hours=self.config.regulatory_lookback_hours
            )

            logger.info(f"监管: 获取到 {len(news_list)} 条新闻")

            # 处理每条新闻，生成警报
            for news in news_list:
                alert = self.alert_system.process_regulatory_news(news)
                if alert:
                    self.stats["alerts_generated"] += 1

            return news_list

        except Exception as e:
            logger.error(f"监管检查失败: {e}")
            self.stats["errors"].append({
                "source": "Regulatory",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_blogs(self) -> List[Dict]:
        """检查大厂博客 (Week 2)"""
        logger.info("检查大厂博客...")
        self.stats["blog_checks"] += 1
        self.stats["last_blog_check"] = datetime.now().isoformat()

        try:
            if self.config.test_mode:
                posts = self.blog_collector.generate_test_data()
            else:
                posts = self.blog_collector.fetch_all_blogs(
                    hours=self.config.blog_lookback_hours
                )

            logger.info(f"博客: 获取到 {len(posts)} 篇文章")

            # 处理博客文章，生成通知
            for post in posts:
                if post.get("priority") in ["P0", "P1"]:
                    self.notifier.notify_from_blog(post)
                    self.stats["alerts_generated"] += 1

            return posts

        except Exception as e:
            logger.error(f"博客检查失败: {e}")
            self.stats["errors"].append({
                "source": "Blog",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_stocks(self) -> List[Dict]:
        """检查股价异动 (Week 2)"""
        logger.info("检查股价异动...")
        self.stats["stock_checks"] += 1
        self.stats["last_stock_check"] = datetime.now().isoformat()

        try:
            alerts = self.stock_monitor.check_all_stocks(
                test_mode=self.config.test_mode
            )

            logger.info(f"股票: 检测到 {len(alerts)} 个异动")

            # 处理股票警报
            result_list = []
            for stock_alert in alerts:
                self.notifier.notify_from_stock(stock_alert)
                self.stats["alerts_generated"] += 1
                result_list.append({
                    "symbol": stock_alert.symbol,
                    "company": stock_alert.company,
                    "change_pct": stock_alert.change_pct,
                    "priority": stock_alert.priority,
                    "signal": stock_alert.signal
                })

            return result_list

        except Exception as e:
            logger.error(f"股票检查失败: {e}")
            self.stats["errors"].append({
                "source": "Stock",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_twitter(self) -> List[Dict]:
        """检查CEO Twitter (Week 2)"""
        logger.info("检查CEO Twitter...")
        self.stats["twitter_checks"] += 1
        self.stats["last_twitter_check"] = datetime.now().isoformat()

        try:
            if self.config.test_mode:
                tweets = self.twitter_monitor.generate_test_data()
            else:
                tweets = self.twitter_monitor.fetch_all_accounts(
                    hours=self.config.twitter_lookback_hours
                )

            logger.info(f"Twitter: 获取到 {len(tweets)} 条推文")

            # 处理推文，生成通知
            for tweet in tweets:
                if tweet.get("priority") in ["P0", "P1"]:
                    notif = Notification(
                        priority=tweet["priority"],
                        title=f"[{tweet['company']}] @{tweet['username']}",
                        message=tweet["content"][:200],
                        source="Twitter/X",
                        timestamp=tweet["published"],
                        signal=tweet.get("investment_signal", "Neutral"),
                        url=tweet.get("link", "")
                    )
                    self.notifier.notify(notif)
                    self.stats["alerts_generated"] += 1

            return tweets

        except Exception as e:
            logger.error(f"Twitter检查失败: {e}")
            self.stats["errors"].append({
                "source": "Twitter",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_github(self) -> List[Dict]:
        """检查GitHub爆款项目 (Week 2)"""
        logger.info("检查GitHub爆款项目...")
        self.stats["github_checks"] += 1
        self.stats["last_github_check"] = datetime.now().isoformat()

        try:
            if self.config.test_mode:
                repos = self.github_monitor.generate_test_data()
            else:
                repos = self.github_monitor.fetch_all_trending(
                    days=self.config.github_lookback_days
                )

            logger.info(f"GitHub: 发现 {len(repos)} 个趋势项目")

            # 处理项目，生成通知
            for repo in repos:
                if repo.get("priority") in ["P0", "P1"]:
                    notif = Notification(
                        priority=repo["priority"],
                        title=f"[GitHub] {repo['full_name']}",
                        message=f"⭐{repo['stars']:,} | {repo['description'][:100]}",
                        source="GitHub",
                        timestamp=repo.get("created_at", ""),
                        signal="Positive" if repo.get("is_priority_org") else "Neutral",
                        url=repo.get("url", "")
                    )
                    self.notifier.notify(notif)
                    self.stats["alerts_generated"] += 1

            return repos

        except Exception as e:
            logger.error(f"GitHub检查失败: {e}")
            self.stats["errors"].append({
                "source": "GitHub",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _check_hackernews(self) -> List[Dict]:
        """检查Hacker News热门讨论 (Week 2)"""
        logger.info("检查Hacker News...")
        self.stats["hackernews_checks"] += 1
        self.stats["last_hackernews_check"] = datetime.now().isoformat()

        try:
            if self.config.test_mode:
                stories = self.hackernews_monitor.generate_test_data()
            else:
                stories = self.hackernews_monitor.fetch_ai_stories(
                    hours=self.config.hackernews_lookback_hours
                )

            logger.info(f"HN: 获取到 {len(stories)} 条AI相关讨论")

            # 处理stories，生成通知
            for story in stories:
                if story.get("priority") in ["P0", "P1"]:
                    notif = Notification(
                        priority=story["priority"],
                        title=f"[HN] {story['title'][:80]}",
                        message=f"⬆️{story['score']} | 💬{story['comments']}",
                        source="Hacker News",
                        timestamp=story["time"],
                        signal=story.get("investment_signal", "Neutral"),
                        url=story.get("hn_url", "")
                    )
                    self.notifier.notify(notif)
                    self.stats["alerts_generated"] += 1

            return stories

        except Exception as e:
            logger.error(f"HN检查失败: {e}")
            self.stats["errors"].append({
                "source": "HackerNews",
                "error": str(e),
                "time": datetime.now().isoformat()
            })
            return []

    def _send_notifications(self):
        """发送通知 (Week 2)"""
        try:
            # P0已经在各模块中立即发送
            # 这里处理P1汇总
            self.notifier.flush_p1()
            self.stats["notifications_sent"] += len(self.notifier.pending_p1)

            # P2写入文件
            self.notifier.flush_p2()

        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    async def run_continuous(self, duration_minutes: int = 60):
        """
        持续运行监控

        Args:
            duration_minutes: 运行时长（分钟）
        """
        logger.info(f"启动持续监控，运行时长: {duration_minutes} 分钟")

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        last_sec_check = datetime.min
        last_regulatory_check = datetime.min

        while datetime.now() < end_time:
            now = datetime.now()

            # SEC检查
            if self.config.sec_enabled:
                sec_due = (now - last_sec_check).total_seconds() / 60 >= self.config.sec_interval_minutes
                if sec_due:
                    self._check_sec()
                    last_sec_check = now

            # 监管检查
            if self.config.regulatory_enabled:
                regulatory_due = (now - last_regulatory_check).total_seconds() / 60 >= self.config.regulatory_interval_minutes
                if regulatory_due:
                    self._check_regulatory()
                    last_regulatory_check = now

            # 等待1分钟
            await asyncio.sleep(60)

        logger.info("持续监控结束")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "total_alerts": len(self.alert_system.alerts),
            "p0_alerts": len(self.alert_system.get_p0_alerts()),
            "p1_alerts": len(self.alert_system.get_p1_alerts()),
            "p2_alerts": len(self.alert_system.get_p2_alerts()),
        }

    def export_results(self, filepath: str):
        """导出结果"""
        self.alert_system.export_alerts_json(filepath)


def run_precision_monitor(
    test_mode: bool = False,
    sec_hours: int = 24,
    regulatory_hours: int = 24,
    blog_hours: int = 24,
    twitter_hours: int = 24,
    github_days: int = 7,
    hackernews_hours: int = 24,
    enable_blog: bool = True,
    enable_stock: bool = True,
    enable_twitter: bool = True,
    enable_github: bool = True,
    enable_hackernews: bool = True,
    webhook_url: str = None,
    webhook_platform: str = "generic"
) -> Dict:
    """
    运行精准监控（单次）

    Args:
        test_mode: 是否使用测试数据
        sec_hours: SEC回看小时数
        regulatory_hours: 监管回看小时数
        blog_hours: 博客回看小时数
        twitter_hours: Twitter回看小时数
        github_days: GitHub回看天数
        hackernews_hours: HN回看小时数
        enable_blog: 是否启用博客监控
        enable_stock: 是否启用股价监控
        enable_twitter: 是否启用Twitter监控
        enable_github: 是否启用GitHub监控
        enable_hackernews: 是否启用HN监控
        webhook_url: Webhook URL
        webhook_platform: Webhook平台

    Returns:
        监控结果
    """
    config = MonitorConfig(
        test_mode=test_mode,
        sec_lookback_hours=sec_hours,
        regulatory_lookback_hours=regulatory_hours,
        blog_lookback_hours=blog_hours,
        twitter_lookback_hours=twitter_hours,
        github_lookback_days=github_days,
        hackernews_lookback_hours=hackernews_hours,
        blog_enabled=enable_blog,
        stock_enabled=enable_stock,
        twitter_enabled=enable_twitter,
        github_enabled=enable_github,
        hackernews_enabled=enable_hackernews,
        webhook_url=webhook_url,
        webhook_platform=webhook_platform
    )

    monitor = PrecisionMonitor(config)
    return monitor.run_once()


def test_precision_monitor():
    """测试精准监控器 v2.0"""
    print("=" * 60)
    print("精准监控器 v2.0 测试 (7个数据源)")
    print("=" * 60)

    # 使用测试模式
    config = MonitorConfig(
        test_mode=True,
        sec_lookback_hours=24,
        regulatory_lookback_hours=24,
        blog_lookback_hours=24,
        twitter_lookback_hours=24,
        github_lookback_days=7,
        hackernews_lookback_hours=24,
        blog_enabled=True,
        stock_enabled=True,
        twitter_enabled=True,
        github_enabled=True,
        hackernews_enabled=True,
        notify_file=False,  # 测试时不写文件
    )

    monitor = PrecisionMonitor(config)

    # 设置P0回调
    def on_p0(alert):
        print(f"\n🚨 P0 ALERT: {alert.title}")
        print(f"   Signal: {alert.investment_signal}")
        print(f"   Action: {alert.action_required}")

    monitor.on_p0_alert = on_p0

    # 运行一次
    results = monitor.run_once()

    # 输出统计
    stats = monitor.get_stats()
    print("\n" + "=" * 60)
    print("统计信息:")
    print(f"  SEC检查: {stats['sec_checks']}")
    print(f"  监管检查: {stats['regulatory_checks']}")
    print(f"  博客检查: {stats['blog_checks']}")
    print(f"  股票检查: {stats['stock_checks']}")
    print(f"  Twitter检查: {stats['twitter_checks']}")
    print(f"  GitHub检查: {stats['github_checks']}")
    print(f"  HN检查: {stats['hackernews_checks']}")
    print(f"  生成警报: {stats['alerts_generated']}")
    print(f"  P0警报: {stats['p0_alerts']}")
    print(f"  P1警报: {stats['p1_alerts']}")
    print(f"  P2警报: {stats['p2_alerts']}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_precision_monitor()
