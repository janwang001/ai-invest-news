#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件

配置测试环境，设置正确的 Python 路径。
"""

import os
import sys

# 将 src 目录添加到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# pytest fixtures 可以在这里定义
# 例如：
# @pytest.fixture
# def sample_news():
#     return {"title": "Test News", "content": "Test Content"}
