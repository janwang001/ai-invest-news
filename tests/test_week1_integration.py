#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 1 精准监控集成测试

测试内容:
1. SEC EDGAR 采集器
2. 监管机构采集器
3. 警报系统 (P0/P1/P2)
4. 精准监控调度器
5. 端到端流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors import (
    SECEdgarCollector,
    RegulatoryCollector,
    AlertSystem,
    Alert,
    AlertPriority,
    PrecisionMonitor,
    MonitorConfig,
    run_precision_monitor
)


def test_sec_collector():
    """测试SEC采集器"""
    print("\n=== 测试1: SEC EDGAR 采集器 ===")

    collector = SECEdgarCollector()

    # 测试数据生成
    filings = collector.fetch_recent_filings(hours=24, test_mode=True)

    assert len(filings) > 0, "应该返回测试数据"
    assert filings[0]["filing_type"] in ["8-K", "D", "S-1"], "应包含关键Form类型"
    assert "company_name" in filings[0], "应包含公司名"

    # 测试优先级计算
    priority = collector.calculate_priority(filings[0])
    assert priority in ["P0", "P1", "P2"], f"优先级应为P0/P1/P2, 得到{priority}"

    print(f"  ✅ 获取到 {len(filings)} 个测试文件")
    print(f"  ✅ 优先级计算正常: {priority}")
    return True


def test_regulatory_collector():
    """测试监管采集器"""
    print("\n=== 测试2: 监管机构采集器 ===")

    collector = RegulatoryCollector()

    # 测试AI关键词检测
    test_news = {
        "title": "FTC investigates OpenAI for anticompetitive practices",
        "summary": "Investigation into AI market dominance"
    }

    is_ai = collector._is_ai_related(test_news)
    assert is_ai, "应检测到AI相关内容"

    # 测试优先级计算
    priority = collector._calculate_priority(test_news)
    assert priority == "P0", f"包含investigation应为P0, 得到{priority}"

    print("  ✅ AI关键词检测正常")
    print("  ✅ 优先级计算正常: P0")
    return True


def test_alert_system():
    """测试警报系统"""
    print("\n=== 测试3: 警报系统 ===")

    system = AlertSystem()

    # 测试SEC警报生成
    sec_filing = {
        "filing_type": "S-1",
        "company_name": "OpenAI Inc",
        "link": "https://sec.gov/test",
        "published": "2026-02-04 10:00"
    }
    alert = system.process_sec_filing(sec_filing)

    assert alert is not None, "应生成警报"
    assert alert.priority == "P0", f"S-1应为P0, 得到{alert.priority}"
    assert alert.investment_signal == "Positive", f"IPO应为正面信号"

    # 测试监管警报生成
    regulatory_news = {
        "title": "DOJ launches criminal investigation",
        "summary": "Criminal charges pending",
        "source": "DOJ",
        "agency": "Department of Justice",
        "link": "https://doj.gov/test"
    }
    alert2 = system.process_regulatory_news(regulatory_news)

    assert alert2 is not None, "应生成监管警报"
    assert alert2.priority == "P0", f"criminal应为P0, 得到{alert2.priority}"
    assert alert2.investment_signal == "Negative", f"调查应为负面信号"

    # 测试警报获取
    p0_alerts = system.get_p0_alerts()
    assert len(p0_alerts) == 2, f"应有2个P0警报, 得到{len(p0_alerts)}"

    print(f"  ✅ SEC警报生成正常: {alert.title}")
    print(f"  ✅ 监管警报生成正常: {alert2.title[:40]}...")
    print(f"  ✅ P0警报数量: {len(p0_alerts)}")
    return True


def test_precision_monitor():
    """测试精准监控器"""
    print("\n=== 测试4: 精准监控器 ===")

    config = MonitorConfig(
        test_mode=True,
        sec_enabled=True,
        regulatory_enabled=False  # 禁用监管以避免网络请求
    )

    monitor = PrecisionMonitor(config)

    # 设置回调
    p0_received = []
    def on_p0(alert):
        p0_received.append(alert)

    monitor.on_p0_alert = on_p0

    # 运行一次
    results = monitor.run_once()

    assert "alerts" in results, "结果应包含alerts"
    assert len(results["alerts"]["p0"]) > 0, "应有P0警报"
    assert len(p0_received) > 0, "P0回调应被调用"

    # 检查统计
    stats = monitor.get_stats()
    assert stats["sec_checks"] == 1, "SEC应检查1次"
    assert stats["alerts_generated"] > 0, "应生成警报"

    print(f"  ✅ 监控运行正常")
    print(f"  ✅ P0回调触发: {len(p0_received)} 次")
    print(f"  ✅ 警报生成: {stats['alerts_generated']} 条")
    return True


def test_alert_priority_logic():
    """测试警报优先级逻辑"""
    print("\n=== 测试5: 优先级逻辑 ===")

    system = AlertSystem()

    # P0: IPO注册
    assert system._determine_sec_priority({"filing_type": "S-1"}) == "P0"

    # P0: 大额融资 (>$100M)
    assert system._determine_sec_priority({
        "filing_type": "D",
        "funding_info": {"total_sold": "200000000"}
    }) == "P0"

    # P1: 小额融资
    assert system._determine_sec_priority({
        "filing_type": "D",
        "funding_info": {"total_sold": "50000000"}
    }) == "P1"

    # P0: 8-K收购
    assert system._determine_sec_priority({
        "filing_type": "8-K",
        "8k_items": [{"code": "item 1.01"}]
    }) == "P0"

    # P1: 8-K其他
    assert system._determine_sec_priority({
        "filing_type": "8-K",
        "8k_items": [{"code": "item 8.01"}]
    }) == "P1"

    # P1: 13D激进投资
    assert system._determine_sec_priority({"filing_type": "13D"}) == "P1"

    # P2: 其他
    assert system._determine_sec_priority({"filing_type": "13G"}) == "P2"

    print("  ✅ S-1 (IPO) → P0")
    print("  ✅ Form D >$100M → P0")
    print("  ✅ Form D <$100M → P1")
    print("  ✅ 8-K 收购 → P0")
    print("  ✅ 8-K 其他 → P1")
    print("  ✅ 13D → P1")
    print("  ✅ 13G → P2")
    return True


def test_investment_signal_logic():
    """测试投资信号逻辑"""
    print("\n=== 测试6: 投资信号逻辑 ===")

    system = AlertSystem()

    # SEC信号
    signal, action = system._determine_investment_signal({"filing_type": "S-1"}, "sec")
    assert signal == "Positive", f"IPO应为Positive, 得到{signal}"

    signal, action = system._determine_investment_signal({
        "filing_type": "8-K",
        "8k_items": [{"code": "item 1.02"}]  # 资产处置
    }, "sec")
    assert signal == "Negative", f"资产处置应为Negative, 得到{signal}"

    # 监管信号
    signal, action = system._determine_investment_signal({
        "title": "investigation launched",
        "summary": "probe into practices"
    }, "regulatory")
    assert signal == "Negative", f"调查应为Negative, 得到{signal}"
    assert action == "Immediate", f"调查应需Immediate, 得到{action}"

    signal, action = system._determine_investment_signal({
        "title": "case dismissed by court",
        "summary": "allegations dropped"
    }, "regulatory")
    assert signal == "Positive", f"dismissed应为Positive, 得到{signal}"

    print("  ✅ IPO → Positive")
    print("  ✅ 资产处置 → Negative")
    print("  ✅ 调查 → Negative + Immediate")
    print("  ✅ 驳回 → Positive")
    return True


def test_end_to_end():
    """端到端测试"""
    print("\n=== 测试7: 端到端流程 ===")

    # 使用便捷函数
    results = run_precision_monitor(
        test_mode=True,
        sec_hours=24,
        regulatory_hours=24
    )

    assert results is not None, "应返回结果"
    assert "timestamp" in results, "应包含时间戳"
    assert "alerts" in results, "应包含警报"

    total_alerts = (
        len(results["alerts"]["p0"]) +
        len(results["alerts"]["p1"]) +
        len(results["alerts"]["p2"])
    )

    print(f"  ✅ 端到端流程正常")
    print(f"  ✅ 总警报数: {total_alerts}")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Week 1 精准监控集成测试")
    print("=" * 60)

    tests = [
        ("SEC EDGAR 采集器", test_sec_collector),
        ("监管机构采集器", test_regulatory_collector),
        ("警报系统", test_alert_system),
        ("精准监控器", test_precision_monitor),
        ("优先级逻辑", test_alert_priority_logic),
        ("投资信号逻辑", test_investment_signal_logic),
        ("端到端流程", test_end_to_end),
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
