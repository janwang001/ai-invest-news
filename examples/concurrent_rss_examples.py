#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发RSS抓取示例

演示如何使用新的并发RSS抓取功能
"""

import sys
import os
import logging
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search.search_pipeline_v2 import SearchPipelineV2
from search.concurrent_rss_fetcher import ConcurrentRSSFetcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example1_basic_usage():
    """示例1: 基本使用 - 使用SearchPipelineV2"""
    print("\n" + "=" * 70)
    print("示例1: 基本使用 - SearchPipelineV2")
    print("=" * 70)

    # 创建管道（默认启用并发）
    pipeline = SearchPipelineV2(
        hours=24,               # 搜索最近24小时
        max_items_per_source=5, # 每个源最多5条
        use_concurrent=True,    # 使用并发（默认）
        max_concurrent=10       # 最大并发数10
    )

    # 运行完整流程
    start_time = time.time()
    news, stats = pipeline.run_pipeline()
    elapsed = time.time() - start_time

    print(f"\n✓ 完成")
    print(f"  - 耗时: {elapsed:.2f}s")
    print(f"  - 获取新闻: {len(news)} 条")

    # 显示前3条新闻
    print("\n前3条新闻:")
    for i, item in enumerate(news[:3], 1):
        print(f"  [{i}] {item['title'][:60]}...")
        print(f"      来源: {item['source']}")


def example2_only_search():
    """示例2: 仅搜索不处理"""
    print("\n" + "=" * 70)
    print("示例2: 仅搜索RSS，不进行后续处理")
    print("=" * 70)

    pipeline = SearchPipelineV2(
        hours=24,
        max_items_per_source=5,
        use_concurrent=True
    )

    # 仅运行搜索
    start_time = time.time()
    news, stats = pipeline.search_recent_ai_news()
    elapsed = time.time() - start_time

    print(f"\n✓ 完成")
    print(f"  - 耗时: {elapsed:.2f}s")
    print(f"  - 获取新闻: {len(news)} 条")

    # 显示性能统计
    if "performance" in stats:
        perf = stats["performance"]
        print(f"\n性能统计:")
        print(f"  - 平均每源: {perf['avg_time_per_source']:.2f}s")
        print(f"  - 成功: {perf['successful_fetches']}")
        print(f"  - 失败: {perf['failed_fetches']}")


def example3_direct_fetcher():
    """示例3: 直接使用ConcurrentRSSFetcher"""
    print("\n" + "=" * 70)
    print("示例3: 直接使用ConcurrentRSSFetcher")
    print("=" * 70)

    # 创建抓取器
    fetcher = ConcurrentRSSFetcher(
        hours=24,
        max_items_per_source=5,
        max_concurrent=15,  # 提高并发数
        timeout=10,         # 缩短超时时间
        max_retries=1       # 减少重试次数
    )

    # 执行抓取
    start_time = time.time()
    news, stats = fetcher.fetch_rss_sync()
    elapsed = time.time() - start_time

    print(f"\n✓ 完成")
    print(f"  - 耗时: {elapsed:.2f}s")
    print(f"  - 获取新闻: {len(news)} 条")

    # 显示源分类统计
    classification = stats.get("source_classification", {})
    print(f"\n源分类统计:")
    print(f"  - 有效源: {len(classification.get('valid_sources', []))}")
    print(f"  - 过期源: {len(classification.get('expired_sources', []))}")
    print(f"  - 无效源: {len(classification.get('invalid_sources', []))}")
    print(f"  - 错误源: {len(classification.get('error_sources', []))}")


def example4_serial_mode():
    """示例4: 使用串行模式（向后兼容）"""
    print("\n" + "=" * 70)
    print("示例4: 使用串行模式（向后兼容）")
    print("=" * 70)

    # 关闭并发，使用串行模式
    pipeline = SearchPipelineV2(
        hours=24,
        max_items_per_source=5,
        use_concurrent=False  # 关闭并发
    )

    start_time = time.time()
    news, stats = pipeline.run_pipeline()
    elapsed = time.time() - start_time

    print(f"\n✓ 完成（串行模式）")
    print(f"  - 耗时: {elapsed:.2f}s")
    print(f"  - 获取新闻: {len(news)} 条")


def example5_error_handling():
    """示例5: 错误处理和降级"""
    print("\n" + "=" * 70)
    print("示例5: 错误处理和降级策略")
    print("=" * 70)

    try:
        # 尝试并发模式
        logger.info("尝试并发模式...")
        pipeline = SearchPipelineV2(use_concurrent=True, max_concurrent=10)
        news, stats = pipeline.search_recent_ai_news()

        # 检查失败率
        if "performance" in stats:
            perf = stats["performance"]
            total = perf["total_sources"]
            failed = perf["failed_fetches"]
            fail_rate = failed / total if total > 0 else 0

            print(f"\n失败率: {fail_rate * 100:.1f}%")

            if fail_rate > 0.3:
                logger.warning("失败率过高，建议降级到串行模式")
                # 这里可以选择重新用串行模式运行

    except Exception as e:
        logger.error(f"并发模式失败: {e}")
        logger.info("降级到串行模式...")

        # 降级到串行模式
        pipeline = SearchPipelineV2(use_concurrent=False)
        news, stats = pipeline.search_recent_ai_news()
        print(f"\n✓ 串行模式完成，获取 {len(news)} 条新闻")


def example6_custom_config():
    """示例6: 根据环境自定义配置"""
    print("\n" + "=" * 70)
    print("示例6: 根据环境自定义配置")
    print("=" * 70)

    # 模拟不同环境的配置
    configs = {
        "dev": {
            "max_concurrent": 15,
            "timeout": 10,
            "max_items_per_source": 5
        },
        "prod": {
            "max_concurrent": 10,
            "timeout": 20,
            "max_items_per_source": 20
        },
        "low_spec": {
            "max_concurrent": 5,
            "timeout": 30,
            "max_items_per_source": 10
        }
    }

    # 选择配置（这里用dev）
    env = "dev"
    config = configs[env]

    print(f"\n使用配置: {env}")
    print(f"  - max_concurrent: {config['max_concurrent']}")
    print(f"  - timeout: {config['timeout']}s")

    fetcher = ConcurrentRSSFetcher(
        hours=24,
        max_items_per_source=config["max_items_per_source"],
        max_concurrent=config["max_concurrent"],
        timeout=config["timeout"]
    )

    start_time = time.time()
    news, stats = fetcher.fetch_rss_sync()
    elapsed = time.time() - start_time

    print(f"\n✓ 完成")
    print(f"  - 耗时: {elapsed:.2f}s")
    print(f"  - 获取新闻: {len(news)} 条")


def main():
    """主函数 - 运行所有示例"""
    print("=" * 70)
    print("并发RSS抓取示例合集")
    print("=" * 70)

    examples = [
        ("基本使用", example1_basic_usage),
        ("仅搜索", example2_only_search),
        ("直接使用抓取器", example3_direct_fetcher),
        ("串行模式", example4_serial_mode),
        ("错误处理", example5_error_handling),
        ("自定义配置", example6_custom_config),
    ]

    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  0. 运行所有示例")

    try:
        choice = input("\n请选择要运行的示例 (0-6): ").strip()

        if choice == "0":
            # 运行所有示例
            for name, func in examples:
                print(f"\n运行: {name}")
                func()
                time.sleep(1)
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            # 运行选定的示例
            idx = int(choice) - 1
            name, func = examples[idx]
            print(f"\n运行: {name}")
            func()
        else:
            print("无效的选择")
            return

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)

    print("\n" + "=" * 70)
    print("示例运行完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
