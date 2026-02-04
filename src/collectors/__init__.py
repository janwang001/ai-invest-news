"""
数据采集器模块 v2.0 (Week 1 + Week 2)

精准监控高敏感度投资信号源:

Week 1:
- SEC EDGAR: 8-K重大事件, Form D融资, S-1 IPO, 13D/13G持股
- 监管机构: FTC反垄断, DOJ调查, EU Commission
- 警报系统: P0(5分钟)/P1(1小时)/P2(每日)

Week 2:
- 大厂博客: Google AI, OpenAI, Meta AI, Anthropic, NVIDIA
- 股价异动: AI芯片(NVDA/AMD), 云厂商(MSFT/GOOGL), AI概念股
- CEO Twitter: Sam Altman, Elon Musk, Satya Nadella等 (via Nitter RSS)
- GitHub爆款: AI相关趋势项目, 顶级组织新项目
- Hacker News: AI相关热门讨论
- 通知系统: 控制台, 文件, Webhook(Slack/企业微信/钉钉)

使用方式:
    from src.collectors import run_precision_monitor

    # 测试模式（所有数据源）
    results = run_precision_monitor(test_mode=True)

    # 生产模式
    results = run_precision_monitor(
        sec_hours=1,
        regulatory_hours=2,
        blog_hours=24,
        enable_stock=True
    )

    # 带Webhook通知
    results = run_precision_monitor(
        webhook_url="https://hooks.slack.com/...",
        webhook_platform="slack"
    )
"""

from .sec_edgar_collector import SECEdgarCollector
from .regulatory_collector import RegulatoryCollector
from .blog_collector import BlogCollector
from .stock_monitor import StockMonitor, StockAlert
from .twitter_monitor import TwitterMonitor
from .github_monitor import GitHubMonitor
from .hackernews_monitor import HackerNewsMonitor
from .alert_system import AlertSystem, Alert, AlertPriority, AlertType
from .notifier import Notifier, Notification, ConsoleChannel, FileChannel, WebhookChannel
from .precision_monitor import PrecisionMonitor, MonitorConfig, run_precision_monitor

__all__ = [
    # Week 1 采集器
    'SECEdgarCollector',
    'RegulatoryCollector',

    # Week 2 采集器
    'BlogCollector',
    'StockMonitor',
    'StockAlert',
    'TwitterMonitor',
    'GitHubMonitor',
    'HackerNewsMonitor',

    # 警报系统
    'AlertSystem',
    'Alert',
    'AlertPriority',
    'AlertType',

    # 通知系统
    'Notifier',
    'Notification',
    'ConsoleChannel',
    'FileChannel',
    'WebhookChannel',

    # 监控器
    'PrecisionMonitor',
    'MonitorConfig',
    'run_precision_monitor',
]
