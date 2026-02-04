#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精准监控命令行工具 v2.1

高敏感度数据源精准监控:
- Week 1: SEC EDGAR, 监管机构 (FTC/DOJ/EU)
- Week 2: 大厂博客, 股价异动, CEO Twitter, GitHub爆款, HN热门

使用方式:
    # 测试模式（所有数据源）
    python src/run_monitor.py --test

    # 生产模式（全部数据源）
    python src/run_monitor.py

    # 仅SEC和监管
    python src/run_monitor.py --no-blog --no-stock --no-twitter --no-github --no-hn

    # 自定义时间范围
    python src/run_monitor.py --sec-hours 1 --blog-hours 12 --twitter-hours 6

    # 导出结果
    python src/run_monitor.py --export alerts.json

    # 带Webhook通知
    python src/run_monitor.py --webhook https://hooks.slack.com/xxx --webhook-platform slack
"""

import argparse
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors import run_precision_monitor, PrecisionMonitor, MonitorConfig


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI投资精准监控 v2.1 - 高敏感度数据源监控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python src/run_monitor.py --test              # 测试模式（所有源）
  python src/run_monitor.py --no-blog --no-stock # 仅SEC+监管
  python src/run_monitor.py --sec-hours 1       # SEC仅回看1小时
  python src/run_monitor.py --export out.json   # 导出警报
  python src/run_monitor.py --webhook URL       # 带Webhook通知

数据源:
  Week 1: SEC EDGAR (8-K/D/S-1/13D), 监管 (FTC/DOJ/EU)
  Week 2: 大厂博客 (OpenAI/Google/Meta), 股价异动 (NVDA/MSFT等)
          CEO Twitter (@sama/@elonmusk等), GitHub爆款, HN热门
        """
    )

    # 基本选项
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="测试模式（使用模拟数据）"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    # Week 1 选项
    parser.add_argument(
        "--sec-hours",
        type=int,
        default=24,
        help="SEC回看时间范围（小时），默认24"
    )

    parser.add_argument(
        "--regulatory-hours",
        type=int,
        default=24,
        help="监管新闻回看时间范围（小时），默认24"
    )

    parser.add_argument(
        "--no-sec",
        action="store_true",
        help="禁用SEC监控"
    )

    parser.add_argument(
        "--no-regulatory",
        action="store_true",
        help="禁用监管监控"
    )

    # Week 2 选项
    parser.add_argument(
        "--blog-hours",
        type=int,
        default=24,
        help="博客回看时间范围（小时），默认24"
    )

    parser.add_argument(
        "--no-blog",
        action="store_true",
        help="禁用博客监控"
    )

    parser.add_argument(
        "--no-stock",
        action="store_true",
        help="禁用股价监控"
    )

    # Twitter选项
    parser.add_argument(
        "--twitter-hours",
        type=int,
        default=24,
        help="Twitter回看时间范围（小时），默认24"
    )

    parser.add_argument(
        "--no-twitter",
        action="store_true",
        help="禁用CEO Twitter监控"
    )

    # GitHub选项
    parser.add_argument(
        "--github-days",
        type=int,
        default=7,
        help="GitHub回看时间范围（天），默认7"
    )

    parser.add_argument(
        "--no-github",
        action="store_true",
        help="禁用GitHub爆款监控"
    )

    # Hacker News选项
    parser.add_argument(
        "--hn-hours",
        type=int,
        default=24,
        help="HN回看时间范围（小时），默认24"
    )

    parser.add_argument(
        "--no-hn",
        action="store_true",
        help="禁用Hacker News监控"
    )

    # 通知选项
    parser.add_argument(
        "--webhook",
        type=str,
        help="Webhook URL（Slack/企业微信/钉钉）"
    )

    parser.add_argument(
        "--webhook-platform",
        type=str,
        default="generic",
        choices=["slack", "wecom", "dingtalk", "generic"],
        help="Webhook平台类型，默认generic"
    )

    parser.add_argument(
        "--no-file",
        action="store_true",
        help="禁用文件记录"
    )

    # 导出选项
    parser.add_argument(
        "--export", "-e",
        type=str,
        help="导出警报到JSON文件"
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 打印配置
    print("=" * 60)
    print("AI投资精准监控系统 v2.1")
    print("=" * 60)
    print(f"模式: {'测试' if args.test else '生产'}")
    print()
    print("数据源状态:")
    print(f"  SEC监控: {'关闭' if args.no_sec else f'开启 (回看{args.sec_hours}小时)'}")
    print(f"  监管监控: {'关闭' if args.no_regulatory else f'开启 (回看{args.regulatory_hours}小时)'}")
    print(f"  博客监控: {'关闭' if args.no_blog else f'开启 (回看{args.blog_hours}小时)'}")
    print(f"  股价监控: {'关闭' if args.no_stock else '开启'}")
    print(f"  Twitter监控: {'关闭' if args.no_twitter else f'开启 (回看{args.twitter_hours}小时)'}")
    print(f"  GitHub监控: {'关闭' if args.no_github else f'开启 (回看{args.github_days}天)'}")
    print(f"  HN监控: {'关闭' if args.no_hn else f'开启 (回看{args.hn_hours}小时)'}")
    print()
    print("通知渠道:")
    print(f"  控制台: 开启")
    print(f"  文件记录: {'关闭' if args.no_file else '开启'}")
    print(f"  Webhook: {'开启 (' + args.webhook_platform + ')' if args.webhook else '关闭'}")
    print("=" * 60)

    # 创建配置
    config = MonitorConfig(
        test_mode=args.test,
        # Week 1
        sec_enabled=not args.no_sec,
        sec_lookback_hours=args.sec_hours,
        regulatory_enabled=not args.no_regulatory,
        regulatory_lookback_hours=args.regulatory_hours,
        # Week 2
        blog_enabled=not args.no_blog,
        blog_lookback_hours=args.blog_hours,
        stock_enabled=not args.no_stock,
        twitter_enabled=not args.no_twitter,
        twitter_lookback_hours=args.twitter_hours,
        github_enabled=not args.no_github,
        github_lookback_days=args.github_days,
        hackernews_enabled=not args.no_hn,
        hackernews_lookback_hours=args.hn_hours,
        # 通知
        notify_console=True,
        notify_file=not args.no_file,
        webhook_url=args.webhook,
        webhook_platform=args.webhook_platform,
    )

    # 运行监控
    monitor = PrecisionMonitor(config)

    # P0回调 - 打印紧急警报
    def on_p0_alert(alert):
        print(f"\n🚨 紧急警报 (P0): {alert.title}")
        print(f"   信号: {alert.investment_signal}")
        print(f"   行动: {alert.action_required}")
        print(f"   来源: {alert.source}")

    monitor.on_p0_alert = on_p0_alert

    # 执行
    results = monitor.run_once()

    # 导出
    if args.export:
        monitor.export_results(args.export)
        print(f"\n警报已导出: {args.export}")

    # 统计
    stats = monitor.get_stats()
    print("\n" + "=" * 60)
    print("运行统计:")
    print(f"  SEC检查: {stats['sec_checks']} 次")
    print(f"  监管检查: {stats['regulatory_checks']} 次")
    print(f"  博客检查: {stats['blog_checks']} 次")
    print(f"  股票检查: {stats['stock_checks']} 次")
    print(f"  Twitter检查: {stats['twitter_checks']} 次")
    print(f"  GitHub检查: {stats['github_checks']} 次")
    print(f"  HN检查: {stats['hackernews_checks']} 次")
    print()
    print(f"  警报总数: {stats['total_alerts']}")
    print(f"    P0: {stats['p0_alerts']} (需立即关注)")
    print(f"    P1: {stats['p1_alerts']} (高优先级)")
    print(f"    P2: {stats['p2_alerts']} (每日汇总)")
    print("=" * 60)

    # 返回P0数量作为退出码
    return stats['p0_alerts']


if __name__ == "__main__":
    sys.exit(main())
