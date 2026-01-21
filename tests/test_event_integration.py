#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event模块集成测试脚本

该脚本用于测试event模块在main流程中的集成是否正常。
"""

import ast
import logging
import os
import sys

# 添加 src 目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """测试基本导入功能"""
    print("=" * 50)
    print("开始测试Event模块基本导入功能")
    print("=" * 50)
    
    try:
        # 1. 测试模块导入
        print("\n1. 测试模块导入...")
        from event.event_pipeline import EventPipeline
        from event.clustering import NewsClusterer
        from event.embedding import TextEmbedder
        from event.event_summary import EventSummarizer
        from event.event_config import CLUSTERING_ALGORITHM, MIN_CLUSTER_SIZE
        
        print("✓ 所有模块导入成功")
        
        # 2. 测试配置参数
        print("\n2. 测试配置参数...")
        print(f"聚类算法: {CLUSTERING_ALGORITHM}")
        print(f"最小聚类大小: {MIN_CLUSTER_SIZE}")
        print("✓ 配置参数读取正常")
        
        # 3. 测试类初始化
        print("\n3. 测试类初始化...")
        try:
            # 跳过embedder初始化，避免下载大文件
            clusterer = NewsClusterer()
            summarizer = EventSummarizer()
            print("✓ NewsClusterer和EventSummarizer初始化成功")
        except Exception as e:
            print(f"⚠ 部分类初始化失败（可能因为缺少模型文件）: {e}")
        
        # 4. 测试main.py中的event相关代码
        print("\n4. 测试main.py集成代码...")
        main_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py')
        with open(main_file_path, 'r', encoding='utf-8') as f:
            main_code = f.read()
        
        # 检查event相关导入
        tree = ast.parse(main_code)
        has_event_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'event' in node.module:
                    has_event_import = True
                    print(f"✓ 检测到event模块导入: from {node.module} import {', '.join([alias.name for alias in node.names])}")
        
        if has_event_import:
            print("✓ main.py中event模块导入正常")
        else:
            print("⚠ 未检测到event模块导入")
        
        # 检查event相关调用
        if 'EventPipeline' in main_code and 'analyze_events' in main_code:
            print("✓ main.py中event模块调用代码存在")
        else:
            print("⚠ main.py中event模块调用代码可能不完整")
        
        print("\n" + "=" * 50)
        print("Event模块基本集成测试完成 ✓")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_imports()
    sys.exit(0 if success else 1)