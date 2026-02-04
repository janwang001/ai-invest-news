#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的渐进式并发测试脚本

特点:
- 从小并发开始逐步增加
- 实时监控系统资源
- 自动停止异常情况
- 生成详细的性能报告
"""

import sys
import os
import time
import logging
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search.concurrent_rss_fetcher import ConcurrentRSSFetcher
from search.search_pipeline import SearchPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_system_status():
    """获取系统资源状态"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / 1024 / 1024
        }
    except ImportError:
        return {"cpu_percent": 0, "memory_percent": 0, "memory_available_mb": 0}


def safe_test_concurrent(max_concurrent, hours=24, max_items=3):
    """
    安全测试单个并发级别

    Args:
        max_concurrent: 并发数
        hours: 搜索时间范围
        max_items: 每源最大条数（测试时用小值）

    Returns:
        dict: 测试结果
    """
    logger.info("=" * 70)
    logger.info(f"测试并发级别: {max_concurrent}")
    logger.info("=" * 70)

    # 检查系统资源
    sys_status = get_system_status()
    logger.info(f"系统状态 - CPU: {sys_status['cpu_percent']:.1f}%, "
                f"内存: {sys_status['memory_percent']:.1f}%")

    # 如果资源紧张，跳过测试
    if sys_status['cpu_percent'] > 80 or sys_status['memory_percent'] > 85:
        logger.warning("⚠️  系统资源紧张，跳过此测试")
        return {
            "success": False,
            "error": "System resource insufficient",
            "max_concurrent": max_concurrent
        }

    result = {
        "max_concurrent": max_concurrent,
        "success": False,
        "start_time": datetime.now().isoformat(),
        "sys_status_before": sys_status
    }

    start_time = time.time()

    try:
        logger.info(f"开始测试 (并发={max_concurrent}, 每源最多{max_items}条)...")

        fetcher = ConcurrentRSSFetcher(
            hours=hours,
            max_items_per_source=max_items,
            max_concurrent=max_concurrent,
            timeout=15  # 15秒超时
        )

        news, stats = fetcher.fetch_rss_sync()

        elapsed = time.time() - start_time

        # 获取测试后的系统状态
        sys_status_after = get_system_status()

        result.update({
            "success": True,
            "elapsed_time": elapsed,
            "news_count": len(news),
            "stats": stats,
            "sys_status_after": sys_status_after
        })

        # 提取关键指标
        if "performance" in stats:
            perf = stats["performance"]
            result["successful_sources"] = perf.get("successful_fetches", 0)
            result["failed_sources"] = perf.get("failed_fetches", 0)
            result["avg_time_per_source"] = perf.get("avg_time_per_source", 0)

        logger.info(f"✓ 测试完成")
        logger.info(f"  - 耗时: {elapsed:.2f}s")
        logger.info(f"  - 获取新闻: {len(news)} 条")
        logger.info(f"  - CPU使用: {sys_status['cpu_percent']:.1f}% -> "
                   f"{sys_status_after['cpu_percent']:.1f}%")
        logger.info(f"  - 内存使用: {sys_status['memory_percent']:.1f}% -> "
                   f"{sys_status_after['memory_percent']:.1f}%")

    except KeyboardInterrupt:
        logger.warning("⚠️  用户中断测试")
        result["error"] = "User interrupted"
        raise

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ 测试失败: {e}")
        result.update({
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed
        })

    # 等待系统恢复
    time.sleep(3)

    return result


def test_serial_baseline(hours=24, max_items=3):
    """测试串行模式作为基准"""
    logger.info("=" * 70)
    logger.info("测试串行模式 (基准)")
    logger.info("=" * 70)

    sys_status = get_system_status()
    logger.info(f"系统状态 - CPU: {sys_status['cpu_percent']:.1f}%, "
                f"内存: {sys_status['memory_percent']:.1f}%")

    result = {
        "mode": "serial",
        "success": False,
        "start_time": datetime.now().isoformat(),
        "sys_status_before": sys_status
    }

    start_time = time.time()

    try:
        logger.info(f"开始测试 (串行模式, 每源最多{max_items}条)...")

        pipeline = SearchPipeline(hours=hours, max_items_per_source=max_items)
        news, stats = pipeline.search_recent_ai_news()

        elapsed = time.time() - start_time
        sys_status_after = get_system_status()

        result.update({
            "success": True,
            "elapsed_time": elapsed,
            "news_count": len(news),
            "stats": stats,
            "sys_status_after": sys_status_after
        })

        # 提取成功/失败源数量
        source_stats = stats.get("sources", {})
        result["successful_sources"] = sum(
            1 for s in source_stats.values()
            if isinstance(s, dict) and s.get("valid_fetched", 0) > 0
        )
        result["failed_sources"] = sum(
            1 for s in source_stats.values()
            if isinstance(s, dict) and s.get("valid_fetched", 0) == 0
        )

        logger.info(f"✓ 测试完成")
        logger.info(f"  - 耗时: {elapsed:.2f}s")
        logger.info(f"  - 获取新闻: {len(news)} 条")
        logger.info(f"  - 成功源: {result['successful_sources']}")

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ 测试失败: {e}")
        result.update({
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed
        })

    time.sleep(3)
    return result


def generate_report(serial_result, concurrent_results):
    """生成性能对比报告"""
    print("\n" + "=" * 80)
    print("RSS并发抓取性能测试报告")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试配置: 每源最多3条新闻 (安全测试)")

    # 串行模式结果
    print("\n【串行模式 - 基准】")
    print("-" * 80)
    if serial_result["success"]:
        print(f"✓ 测试成功")
        print(f"  耗时: {serial_result['elapsed_time']:.2f}s")
        print(f"  获取新闻: {serial_result['news_count']} 条")
        print(f"  成功源: {serial_result.get('successful_sources', 0)}")
        print(f"  失败源: {serial_result.get('failed_sources', 0)}")
    else:
        print(f"✗ 测试失败: {serial_result.get('error', '未知错误')}")

    # 并发模式结果
    print("\n【并发模式测试】")
    print("-" * 80)
    print(f"{'并发数':<10} {'状态':<8} {'耗时(s)':<12} {'新闻数':<10} "
          f"{'成功源':<10} {'加速比':<10}")
    print("-" * 80)

    serial_time = serial_result.get('elapsed_time', 0)

    for result in concurrent_results:
        if result["success"]:
            speedup = serial_time / result['elapsed_time'] if result['elapsed_time'] > 0 else 0
            print(f"{result['max_concurrent']:<10} "
                  f"{'✓':<8} "
                  f"{result['elapsed_time']:<12.2f} "
                  f"{result['news_count']:<10} "
                  f"{result.get('successful_sources', 0):<10} "
                  f"{speedup:<10.2f}x")
        else:
            error = result.get('error', '未知')[:20]
            print(f"{result['max_concurrent']:<10} "
                  f"{'✗':<8} "
                  f"{'-':<12} "
                  f"{'-':<10} "
                  f"{'-':<10} "
                  f"{error}")

    # 性能对比分析
    print("\n【性能对比分析】")
    print("-" * 80)

    successful_tests = [r for r in concurrent_results if r["success"]]
    if successful_tests and serial_result["success"]:
        best_result = min(successful_tests, key=lambda x: x['elapsed_time'])

        improvement = (serial_time - best_result['elapsed_time']) / serial_time * 100
        speedup = serial_time / best_result['elapsed_time']

        print(f"最佳并发配置: {best_result['max_concurrent']}")
        print(f"串行耗时: {serial_time:.2f}s")
        print(f"并发耗时: {best_result['elapsed_time']:.2f}s")
        print(f"性能提升: {improvement:.1f}%")
        print(f"加速比: {speedup:.2f}x")
        print(f"节省时间: {serial_time - best_result['elapsed_time']:.2f}s")

    # 系统资源分析
    print("\n【系统资源使用】")
    print("-" * 80)
    for result in concurrent_results:
        if result["success"]:
            before = result.get("sys_status_before", {})
            after = result.get("sys_status_after", {})
            print(f"并发={result['max_concurrent']}: "
                  f"CPU {before.get('cpu_percent', 0):.1f}%→{after.get('cpu_percent', 0):.1f}%, "
                  f"内存 {before.get('memory_percent', 0):.1f}%→{after.get('memory_percent', 0):.1f}%")

    # 建议
    print("\n【建议】")
    print("-" * 80)
    if successful_tests:
        best_concurrent = best_result['max_concurrent']
        if improvement > 50:
            print(f"✓ 并发模式显著提升性能，推荐使用 max_concurrent={best_concurrent}")
        elif improvement > 30:
            print(f"✓ 并发模式有明显提升，建议使用 max_concurrent={best_concurrent}")
        else:
            print(f"○ 并发模式有小幅提升，可选择使用 max_concurrent={best_concurrent}")
    else:
        print("✗ 所有并发测试失败，建议检查网络环境或使用串行模式")

    print("\n" + "=" * 80)

    # 保存报告到文件
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        "test_time": datetime.now().isoformat(),
        "serial_result": serial_result,
        "concurrent_results": concurrent_results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n详细报告已保存到: {report_file}")


def main():
    """主测试流程"""
    print("=" * 80)
    print("安全的渐进式并发测试")
    print("=" * 80)
    print("\n配置:")
    print("  - 测试规模: 每源最多3条新闻 (安全测试)")
    print("  - 并发级别: 2, 5, 10")
    print("  - 超时时间: 15秒/请求")
    print("  - 自动监控系统资源")
    print("\n⚠️  测试期间请勿关闭窗口")
    print("⚠️  如需中断，按 Ctrl+C")

    input("\n按回车键开始测试...")

    results = {
        "serial": None,
        "concurrent": []
    }

    try:
        # 测试1: 串行模式（基准）
        print("\n" + "=" * 80)
        print("第1步: 测试串行模式（作为基准）")
        print("=" * 80)
        results["serial"] = test_serial_baseline(hours=24, max_items=3)

        if not results["serial"]["success"]:
            logger.error("串行模式测试失败，停止后续测试")
            return

        # 测试2: 低并发 (2)
        print("\n" + "=" * 80)
        print("第2步: 测试低并发 (并发数=2)")
        print("=" * 80)
        result = safe_test_concurrent(max_concurrent=2, hours=24, max_items=3)
        results["concurrent"].append(result)

        if not result["success"]:
            logger.warning("低并发测试失败，停止后续测试")
        else:
            # 测试3: 中并发 (5)
            print("\n" + "=" * 80)
            print("第3步: 测试中并发 (并发数=5)")
            print("=" * 80)
            result = safe_test_concurrent(max_concurrent=5, hours=24, max_items=3)
            results["concurrent"].append(result)

            if result["success"]:
                # 测试4: 标准并发 (10)
                print("\n" + "=" * 80)
                print("第4步: 测试标准并发 (并发数=10)")
                print("=" * 80)
                result = safe_test_concurrent(max_concurrent=10, hours=24, max_items=3)
                results["concurrent"].append(result)

        # 生成报告
        generate_report(results["serial"], results["concurrent"])

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        if results["concurrent"]:
            print("\n生成部分测试报告...")
            generate_report(results["serial"], results["concurrent"])

    except Exception as e:
        logger.error(f"测试过程出现异常: {e}", exc_info=True)


if __name__ == "__main__":
    main()
