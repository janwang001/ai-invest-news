#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 2 精准监控集成测试

测试内容:
1. 博客采集器
2. 股价监控器
3. Twitter监控器 (Nitter RSS)
4. GitHub爆款监控器
5. Hacker News监控器
6. 通知系统
7. 精准监控器 v2.0 整合
8. 端到端流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors import (
    # Week 1
    SECEdgarCollector,
    RegulatoryCollector,
    AlertSystem,
    # Week 2
    BlogCollector,
    StockMonitor,
    StockAlert,
    TwitterMonitor,
    GitHubMonitor,
    HackerNewsMonitor,
    Notifier,
    Notification,
    # 监控器
    PrecisionMonitor,
    MonitorConfig,
    run_precision_monitor
)


def test_blog_collector():
    """测试博客采集器"""
    print("\n=== 测试1: 博客采集器 ===")

    collector = BlogCollector()

    # 测试数据生成
    posts = collector.generate_test_data()
    assert len(posts) > 0, "应生成测试数据"

    # 验证数据结构
    post = posts[0]
    assert "title" in post, "应包含标题"
    assert "company" in post, "应包含公司"
    assert "priority" in post, "应包含优先级"
    assert "investment_signal" in post, "应包含投资信号"

    # 测试优先级计算
    priority = collector._calculate_priority(
        "Introducing GPT-5",
        "Launch of our new model",
        {"priority_boost": 1.0}
    )
    assert priority == "P0", f"产品发布应为P0, 得到{priority}"

    # 测试信号提取
    signal = collector._extract_signal("Product launch announcement", "Big release today")
    assert signal == "Positive", f"发布应为Positive, 得到{signal}"

    print(f"  ✅ 生成 {len(posts)} 篇测试文章")
    print(f"  ✅ 优先级计算正常")
    print(f"  ✅ 信号提取正常")
    return True


def test_stock_monitor():
    """测试股价监控器"""
    print("\n=== 测试2: 股价监控器 ===")

    monitor = StockMonitor()

    # 测试数据生成
    alerts = monitor.check_all_stocks(test_mode=True)
    assert len(alerts) > 0, "应生成测试警报"

    # 验证警报结构
    alert = alerts[0]
    assert isinstance(alert, StockAlert), "应返回StockAlert对象"
    assert alert.symbol, "应包含股票代码"
    assert alert.priority in ["P0", "P1", "P2"], "优先级应为P0/P1/P2"

    # 测试阈值逻辑
    # 高变化率应触发P0
    high_change = [a for a in alerts if abs(a.change_pct) >= 5.0]
    for a in high_change:
        assert a.priority == "P0", f"5%+变化应为P0, {a.symbol}得到{a.priority}"

    # 测试格式化
    formatted = monitor.format_alert(alerts[0])
    assert alerts[0].symbol in formatted, "格式化应包含股票代码"

    print(f"  ✅ 生成 {len(alerts)} 个测试警报")
    print(f"  ✅ 警报结构正确")
    print(f"  ✅ 阈值逻辑正确")
    return True


def test_notifier():
    """测试通知系统"""
    print("\n=== 测试3: 通知系统 ===")

    notifier = Notifier()

    # 测试P0通知（立即发送）
    p0_notif = Notification(
        priority="P0",
        title="测试P0通知",
        message="这是一条P0测试通知",
        source="Test",
        timestamp="2026-02-04 15:00",
        signal="Positive"
    )

    # 清除默认控制台输出（测试时）
    notifier.channels = []

    notifier.notify(p0_notif)
    # P0应该立即发送，不在队列中

    # 测试P1通知（加入队列）
    p1_notif = Notification(
        priority="P1",
        title="测试P1通知",
        message="这是一条P1测试通知",
        source="Test",
        timestamp="2026-02-04 15:00"
    )
    notifier.notify(p1_notif)
    assert len(notifier.pending_p1) == 1, "P1应加入队列"

    # 测试P2通知
    p2_notif = Notification(
        priority="P2",
        title="测试P2通知",
        message="这是一条P2测试通知",
        source="Test",
        timestamp="2026-02-04 15:00"
    )
    notifier.notify(p2_notif)
    assert len(notifier.pending_p2) == 1, "P2应加入队列"

    # 测试统计
    stats = notifier.get_stats()
    assert stats["pending_p1"] == 1, "应有1条待处理P1"
    assert stats["pending_p2"] == 1, "应有1条待处理P2"

    print("  ✅ P0通知立即发送")
    print("  ✅ P1通知加入队列")
    print("  ✅ P2通知加入队列")
    print("  ✅ 统计信息正确")
    return True


def test_notifier_from_sources():
    """测试从各数据源创建通知"""
    print("\n=== 测试4: 数据源通知转换 ===")

    notifier = Notifier()
    notifier.channels = []  # 禁用输出

    # 测试博客通知
    blog_post = {
        "title": "GPT-5 Launch",
        "summary": "New model released",
        "company": "OpenAI",
        "source": "OpenAI Blog",
        "published": "2026-02-04 15:00",
        "link": "https://openai.com/blog/gpt5",
        "priority": "P0",
        "investment_signal": "Positive",
        "content_type": "product_launch"
    }
    blog_notif = notifier.notify_from_blog(blog_post)
    assert "OpenAI" in blog_notif.title, "博客通知应包含公司名"
    assert blog_notif.priority == "P0", "应保留优先级"

    # 测试股票通知
    stock_alert = StockAlert(
        symbol="NVDA",
        company="NVIDIA",
        category="chip",
        current_price=875.50,
        prev_close=820.00,
        change_pct=6.77,
        volume=85000000,
        avg_volume=45000000,
        volume_ratio=1.89,
        priority="P0",
        signal="Positive",
        alert_reason="涨跌幅+6.8%"
    )
    stock_notif = notifier.notify_from_stock(stock_alert)
    assert "NVDA" in stock_notif.title, "股票通知应包含代码"
    assert "+6.8%" in stock_notif.title or "+6.77%" in stock_notif.title, "应包含涨跌幅"

    print("  ✅ 博客通知转换正确")
    print("  ✅ 股票通知转换正确")
    return True


def test_precision_monitor_v2():
    """测试精准监控器 v2.0"""
    print("\n=== 测试5: 精准监控器 v2.0 ===")

    config = MonitorConfig(
        test_mode=True,
        sec_enabled=True,
        regulatory_enabled=False,  # 禁用网络请求
        blog_enabled=True,
        stock_enabled=True,
        twitter_enabled=True,
        github_enabled=True,
        hackernews_enabled=True,
        notify_file=False,
    )

    monitor = PrecisionMonitor(config)

    # 运行一次
    results = monitor.run_once()

    # 验证结果结构
    assert "blog_posts" in results, "应包含博客结果"
    assert "stock_alerts" in results, "应包含股票结果"
    assert "twitter_posts" in results, "应包含Twitter结果"
    assert "github_repos" in results, "应包含GitHub结果"
    assert "hackernews_stories" in results, "应包含HN结果"
    assert len(results["blog_posts"]) > 0, "应有博客数据"
    assert len(results["stock_alerts"]) > 0, "应有股票数据"
    assert len(results["twitter_posts"]) > 0, "应有Twitter数据"
    assert len(results["github_repos"]) > 0, "应有GitHub数据"
    assert len(results["hackernews_stories"]) > 0, "应有HN数据"

    # 检查统计
    stats = monitor.get_stats()
    assert stats["blog_checks"] == 1, "博客应检查1次"
    assert stats["stock_checks"] == 1, "股票应检查1次"
    assert stats["twitter_checks"] == 1, "Twitter应检查1次"
    assert stats["github_checks"] == 1, "GitHub应检查1次"
    assert stats["hackernews_checks"] == 1, "HN应检查1次"

    print(f"  ✅ 博客检查: {stats['blog_checks']} 次, 数据: {len(results['blog_posts'])}")
    print(f"  ✅ 股票检查: {stats['stock_checks']} 次, 数据: {len(results['stock_alerts'])}")
    print(f"  ✅ Twitter检查: {stats['twitter_checks']} 次, 数据: {len(results['twitter_posts'])}")
    print(f"  ✅ GitHub检查: {stats['github_checks']} 次, 数据: {len(results['github_repos'])}")
    print(f"  ✅ HN检查: {stats['hackernews_checks']} 次, 数据: {len(results['hackernews_stories'])}")
    print(f"  ✅ 生成警报: {stats['alerts_generated']} 条")
    return True


def test_end_to_end_v2():
    """端到端测试 v2.0"""
    print("\n=== 测试6: 端到端流程 v2.0 ===")

    # 使用便捷函数（全部数据源）
    results = run_precision_monitor(
        test_mode=True,
        sec_hours=24,
        regulatory_hours=24,
        blog_hours=24,
        twitter_hours=24,
        github_days=7,
        hackernews_hours=24,
        enable_blog=True,
        enable_stock=True,
        enable_twitter=True,
        enable_github=True,
        enable_hackernews=True
    )

    assert results is not None, "应返回结果"

    # 计算总警报数
    total_p0 = len(results["alerts"]["p0"])
    total_p1 = len(results["alerts"]["p1"])
    total_p2 = len(results["alerts"]["p2"])

    # 至少应有来自SEC、博客、股票的警报
    assert total_p0 + total_p1 + total_p2 > 0, "应有警报生成"

    print(f"  ✅ 端到端流程正常")
    print(f"  ✅ P0警报: {total_p0}")
    print(f"  ✅ P1警报: {total_p1}")
    print(f"  ✅ P2警报: {total_p2}")
    return True


def test_webhook_payload():
    """测试Webhook payload格式"""
    print("\n=== 测试7: Webhook Payload ===")

    from src.collectors.notifier import WebhookChannel

    # 测试各平台payload格式
    platforms = ["slack", "wecom", "dingtalk", "generic"]

    notif = Notification(
        priority="P0",
        title="测试警报",
        message="这是测试消息",
        source="Test",
        timestamp="2026-02-04 15:00"
    )

    for platform in platforms:
        channel = WebhookChannel("http://example.com/webhook", platform)
        payload = channel._build_payload(notif)

        assert payload is not None, f"{platform} payload不应为空"

        if platform == "slack":
            assert "text" in payload or "blocks" in payload
        elif platform == "wecom":
            assert payload.get("msgtype") == "markdown"
        elif platform == "dingtalk":
            assert payload.get("msgtype") == "markdown"
        else:
            assert "title" in payload

        print(f"  ✅ {platform} payload格式正确")

    return True


def test_twitter_monitor():
    """测试Twitter监控器"""
    print("\n=== 测试8: Twitter监控器 ===")

    monitor = TwitterMonitor()

    # 测试数据生成
    tweets = monitor.generate_test_data()
    assert len(tweets) > 0, "应生成测试数据"

    # 验证数据结构
    tweet = tweets[0]
    assert "username" in tweet, "应包含用户名"
    assert "company" in tweet, "应包含公司"
    assert "content" in tweet, "应包含内容"
    assert "priority" in tweet, "应包含优先级"
    assert "investment_signal" in tweet, "应包含投资信号"

    # 测试优先级计算
    priority = monitor._calculate_priority(
        "Excited to announce our new model GPT-5",
        {"priority_boost": 1.0}
    )
    assert priority == "P0", f"重大公告应为P0, 得到{priority}"

    # 测试信号提取
    signal = monitor._extract_signal("We are excited to launch this new product")
    assert signal == "Positive", f"发布应为Positive, 得到{signal}"

    print(f"  ✅ 生成 {len(tweets)} 条测试推文")
    print(f"  ✅ 优先级计算正常")
    print(f"  ✅ 信号提取正常")
    return True


def test_github_monitor():
    """测试GitHub监控器"""
    print("\n=== 测试9: GitHub监控器 ===")

    monitor = GitHubMonitor()

    # 测试数据生成
    repos = monitor.generate_test_data()
    assert len(repos) > 0, "应生成测试数据"

    # 验证数据结构
    repo = repos[0]
    assert "full_name" in repo, "应包含项目全名"
    assert "stars" in repo, "应包含Star数"
    assert "priority" in repo, "应包含优先级"
    assert "is_priority_org" in repo, "应包含是否优先组织"

    # 测试AI相关判断
    test_cases = [
        ("llm-chatbot", "A chatbot using LLM", ["chatbot", "ai"], True),
        ("my-website", "Personal portfolio", ["web"], False),
        ("gpt-wrapper", "GPT API wrapper", [], True),
    ]

    for name, desc, topics, expected in test_cases:
        result = monitor._is_ai_related(name, desc, topics)
        assert result == expected, f"AI判断错误: {name}"

    print(f"  ✅ 生成 {len(repos)} 个测试项目")
    print(f"  ✅ AI相关判断正确")
    return True


def test_hackernews_monitor():
    """测试Hacker News监控器"""
    print("\n=== 测试10: HN监控器 ===")

    monitor = HackerNewsMonitor()

    # 测试数据生成
    stories = monitor.generate_test_data()
    assert len(stories) > 0, "应生成测试数据"

    # 验证数据结构
    story = stories[0]
    assert "title" in story, "应包含标题"
    assert "score" in story, "应包含分数"
    assert "comments" in story, "应包含评论数"
    assert "priority" in story, "应包含优先级"
    assert "is_hot" in story, "应包含热门标记"

    # 测试AI相关判断
    test_cases = [
        ("OpenAI announces GPT-5", "https://openai.com", True),
        ("My weekend project", "https://github.com/me", False),
        ("LLM inference optimization", "https://arxiv.org", True),
    ]

    for title, url, expected in test_cases:
        result = monitor._is_ai_related(title, url)
        assert result == expected, f"AI判断错误: {title}"

    print(f"  ✅ 生成 {len(stories)} 条测试stories")
    print(f"  ✅ AI相关判断正确")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Week 2 精准监控集成测试")
    print("=" * 60)

    tests = [
        ("博客采集器", test_blog_collector),
        ("股价监控器", test_stock_monitor),
        ("通知系统", test_notifier),
        ("数据源通知转换", test_notifier_from_sources),
        ("精准监控器 v2.0", test_precision_monitor_v2),
        ("端到端流程 v2.0", test_end_to_end_v2),
        ("Webhook Payload", test_webhook_payload),
        ("Twitter监控器", test_twitter_monitor),
        ("GitHub监控器", test_github_monitor),
        ("HN监控器", test_hackernews_monitor),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ❌ 错误: {e}")

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    for name, success, error in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
        if error:
            print(f"      错误: {error}")

    print(f"\n总计: {passed}/{len(results)} 通过")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
