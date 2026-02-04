#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS抓取性能基准测试

对比串行和并发两种模式的性能，输出详细的测试报告
"""

import sys
import os
import time
import logging
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search.search_pipeline import SearchPipeline
from search.search_pipeline_v2 import SearchPipelineV2
from search.concurrent_rss_fetcher import ConcurrentRSSFetcher


class PerformanceBenchmark:
    """性能基准测试工具"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.results = {
            "serial": {},
            "concurrent": {},
            "comparison": {}
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def test_serial_mode(
        self,
        hours: int = 24,
        max_items: int = 5
    ) -> Dict[str, Any]:
        """测试串行模式"""
        self.logger.info("=" * 70)
        self.logger.info("开始测试：串行RSS抓取")
        self.logger.info("=" * 70)

        start_time = time.time()
        memory_before = self._get_memory_usage()

        try:
            pipeline = SearchPipeline(hours=hours, max_items_per_source=max_items)
            news, stats = pipeline.search_recent_ai_news()

            end_time = time.time()
            memory_after = self._get_memory_usage()

            result = {
                "success": True,
                "news_count": len(news),
                "elapsed_time": end_time - start_time,
                "memory_usage_mb": memory_after - memory_before,
                "stats": stats
            }

            # 源统计
            source_stats = stats.get("sources", {})
            result["successful_sources"] = sum(
                1 for s in source_stats.values()
                if isinstance(s, dict) and s.get("valid_fetched", 0) > 0
            )
            result["failed_sources"] = sum(
                1 for s in source_stats.values()
                if isinstance(s, dict) and s.get("valid_fetched", 0) == 0
            )

            self.logger.info(f"✓ 串行模式完成")
            self.logger.info(f"  - 耗时: {result['elapsed_time']:.2f}s")
            self.logger.info(f"  - 新闻数: {result['news_count']}")
            self.logger.info(f"  - 内存增量: {result['memory_usage_mb']:.1f}MB")
            self.logger.info(f"  - 成功源: {result['successful_sources']}")

            return result

        except Exception as e:
            self.logger.error(f"✗ 串行模式测试失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    def test_concurrent_mode(
        self,
        hours: int = 24,
        max_items: int = 5,
        max_concurrent: int = 10
    ) -> Dict[str, Any]:
        """测试并发模式"""
        self.logger.info("=" * 70)
        self.logger.info("开始测试：并发RSS抓取")
        self.logger.info("=" * 70)

        start_time = time.time()
        memory_before = self._get_memory_usage()

        try:
            fetcher = ConcurrentRSSFetcher(
                hours=hours,
                max_items_per_source=max_items,
                max_concurrent=max_concurrent
            )
            news, stats = fetcher.fetch_rss_sync()

            end_time = time.time()
            memory_after = self._get_memory_usage()

            result = {
                "success": True,
                "news_count": len(news),
                "elapsed_time": end_time - start_time,
                "memory_usage_mb": memory_after - memory_before,
                "stats": stats,
                "max_concurrent": max_concurrent
            }

            # 源统计
            classification = stats.get("source_classification", {})
            result["successful_sources"] = len(classification.get("valid_sources", []))
            result["failed_sources"] = (
                len(classification.get("invalid_sources", [])) +
                len(classification.get("error_sources", []))
            )

            # 性能统计
            if "performance" in stats:
                perf = stats["performance"]
                result["avg_time_per_source"] = perf.get("avg_time_per_source", 0)

            self.logger.info(f"✓ 并发模式完成")
            self.logger.info(f"  - 耗时: {result['elapsed_time']:.2f}s")
            self.logger.info(f"  - 新闻数: {result['news_count']}")
            self.logger.info(f"  - 内存增量: {result['memory_usage_mb']:.1f}MB")
            self.logger.info(f"  - 成功源: {result['successful_sources']}")
            self.logger.info(f"  - 并发数: {max_concurrent}")

            return result

        except Exception as e:
            self.logger.error(f"✗ 并发模式测试失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "max_concurrent": max_concurrent
            }

    def test_concurrent_with_different_levels(
        self,
        hours: int = 24,
        max_items: int = 5
    ) -> Dict[int, Dict[str, Any]]:
        """测试不同并发级别的性能"""
        self.logger.info("=" * 70)
        self.logger.info("测试不同并发级别")
        self.logger.info("=" * 70)

        concurrent_levels = [5, 10, 15, 20]
        results = {}

        for level in concurrent_levels:
            self.logger.info(f"\n测试并发级别: {level}")
            result = self.test_concurrent_mode(hours, max_items, level)
            results[level] = result
            time.sleep(2)  # 间隔2秒

        return results

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # 如果没有安装psutil，返回0
            return 0.0

    def compare_results(
        self,
        serial_result: Dict[str, Any],
        concurrent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对比两种模式的结果"""
        if not serial_result.get("success") or not concurrent_result.get("success"):
            return {"error": "测试失败，无法对比"}

        serial_time = serial_result["elapsed_time"]
        concurrent_time = concurrent_result["elapsed_time"]

        improvement = (serial_time - concurrent_time) / serial_time * 100
        speedup = serial_time / concurrent_time

        comparison = {
            "time_improvement_percent": improvement,
            "speedup_factor": speedup,
            "time_saved_seconds": serial_time - concurrent_time,
            "serial_time": serial_time,
            "concurrent_time": concurrent_time,
            "serial_news_count": serial_result["news_count"],
            "concurrent_news_count": concurrent_result["news_count"],
            "news_count_diff": abs(
                serial_result["news_count"] - concurrent_result["news_count"]
            ),
            "memory_overhead_mb": (
                concurrent_result["memory_usage_mb"] - serial_result["memory_usage_mb"]
            )
        }

        return comparison

    def print_report(self):
        """打印详细的测试报告"""
        print("\n" + "=" * 70)
        print("RSS抓取性能基准测试报告")
        print("=" * 70)

        # 测试配置
        print("\n【测试配置】")
        print("-" * 70)
        print(f"Python版本: {sys.version.split()[0]}")
        print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 串行模式结果
        if self.results["serial"]:
            serial = self.results["serial"]
            print("\n【串行模式】")
            print("-" * 70)
            if serial.get("success"):
                print(f"✓ 测试成功")
                print(f"  耗时: {serial['elapsed_time']:.2f}s")
                print(f"  获取新闻: {serial['news_count']} 条")
                print(f"  成功源: {serial['successful_sources']}")
                print(f"  失败源: {serial['failed_sources']}")
                print(f"  内存增量: {serial['memory_usage_mb']:.1f}MB")
            else:
                print(f"✗ 测试失败: {serial.get('error', '未知错误')}")

        # 并发模式结果
        if self.results["concurrent"]:
            concurrent = self.results["concurrent"]
            print("\n【并发模式】")
            print("-" * 70)
            if concurrent.get("success"):
                print(f"✓ 测试成功")
                print(f"  耗时: {concurrent['elapsed_time']:.2f}s")
                print(f"  获取新闻: {concurrent['news_count']} 条")
                print(f"  成功源: {concurrent['successful_sources']}")
                print(f"  失败源: {concurrent['failed_sources']}")
                print(f"  内存增量: {concurrent['memory_usage_mb']:.1f}MB")
                print(f"  并发级别: {concurrent.get('max_concurrent', 'N/A')}")
                if "avg_time_per_source" in concurrent:
                    print(f"  平均每源: {concurrent['avg_time_per_source']:.2f}s")
            else:
                print(f"✗ 测试失败: {concurrent.get('error', '未知错误')}")

        # 性能对比
        if self.results["comparison"]:
            comp = self.results["comparison"]
            print("\n【性能对比】")
            print("-" * 70)
            if "error" not in comp:
                print(f"串行耗时: {comp['serial_time']:.2f}s")
                print(f"并发耗时: {comp['concurrent_time']:.2f}s")
                print(f"性能提升: {comp['time_improvement_percent']:.1f}%")
                print(f"加速比: {comp['speedup_factor']:.2f}x")
                print(f"节省时间: {comp['time_saved_seconds']:.2f}s")
                print(f"新闻数差异: {comp['news_count_diff']} 条")
                print(f"内存开销: {comp['memory_overhead_mb']:.1f}MB")

                # 结论
                print("\n【结论】")
                print("-" * 70)
                if comp['time_improvement_percent'] > 50:
                    print("✓ 并发模式显著提升性能，推荐使用")
                elif comp['time_improvement_percent'] > 30:
                    print("✓ 并发模式有明显提升，建议使用")
                elif comp['time_improvement_percent'] > 0:
                    print("○ 并发模式有小幅提升")
                else:
                    print("✗ 并发模式未带来性能提升，建议检查网络环境")
            else:
                print(f"✗ 对比失败: {comp['error']}")

        # 不同并发级别对比
        if "concurrent_levels" in self.results:
            print("\n【不同并发级别对比】")
            print("-" * 70)
            levels = self.results["concurrent_levels"]
            print(f"{'并发数':<10} {'耗时(s)':<12} {'新闻数':<10} {'成功率':<10}")
            print("-" * 70)
            for level, result in sorted(levels.items()):
                if result.get("success"):
                    success_rate = (
                        result['successful_sources'] /
                        (result['successful_sources'] + result['failed_sources']) * 100
                    )
                    print(
                        f"{level:<10} "
                        f"{result['elapsed_time']:<12.2f} "
                        f"{result['news_count']:<10} "
                        f"{success_rate:<10.1f}%"
                    )

        print("\n" + "=" * 70)

    def run_full_benchmark(self):
        """运行完整的基准测试"""
        self.logger.info("开始完整基准测试")

        # 测试1: 串行模式
        self.results["serial"] = self.test_serial_mode(hours=24, max_items=5)

        # 等待2秒
        time.sleep(2)

        # 测试2: 并发模式
        self.results["concurrent"] = self.test_concurrent_mode(
            hours=24,
            max_items=5,
            max_concurrent=10
        )

        # 对比结果
        self.results["comparison"] = self.compare_results(
            self.results["serial"],
            self.results["concurrent"]
        )

        # 打印报告
        self.print_report()


def main():
    """主函数"""
    print("RSS抓取性能基准测试工具 v1.0")
    print("=" * 70)

    benchmark = PerformanceBenchmark()

    # 运行基准测试
    benchmark.run_full_benchmark()

    # 可选：测试不同并发级别
    if input("\n是否测试不同并发级别？(y/n): ").lower() == 'y':
        print("\n开始测试不同并发级别...")
        benchmark.results["concurrent_levels"] = (
            benchmark.test_concurrent_with_different_levels(hours=24, max_items=5)
        )
        benchmark.print_report()


if __name__ == "__main__":
    main()
