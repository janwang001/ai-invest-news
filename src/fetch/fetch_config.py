# -*- coding: utf-8 -*-
"""
fetch 模块配置文件

统一管理抓取相关的配置项，避免魔法数字
"""
import os
from pathlib import Path


# ============================================
# 网络请求配置
# ============================================

# 请求超时时间（秒）
REQUEST_TIMEOUT = 10

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ============================================
# 文本处理配置
# ============================================

# 抓取文章的最大字符数（控制 token 消耗）
MAX_ARTICLE_CHARS = 6000

# 清洗时过滤的最小行长度（字符数）
MIN_LINE_LENGTH = 30

# 需要过滤的噪声关键词（小写匹配）
NOISE_KEYWORDS = [
    "cookie",
    "subscribe",
    "newsletter",
    "sign up",
    "advertisement",
    "sponsored",
]

# ============================================
# 存储配置
# ============================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 原始数据存储目录（位于项目根目录下）
RAW_DATA_DIR = PROJECT_ROOT / "raw_data"

# 日期格式（用于创建子目录）
DATE_FORMAT = "%Y%m%d"

# ============================================
# 重试配置
# ============================================

# 最大重试次数
MAX_RETRIES = 2

# 重试间隔（秒）
RETRY_DELAY = 1

# ============================================
# 投资信息抽取配置
# ============================================

# AI 模型名称
EXTRACTOR_MODEL_NAME = "qwen-plus-latest"

# 抽取结果的最大条目数（每个维度）
MAX_ITEMS_PER_DIMENSION = 10

# 抽取文件后缀
EXTRACTED_FILE_SUFFIX = "_investment.json"

# 投资信息维度定义
INVESTMENT_DIMENSIONS = [
    "facts",             # 明确事实
    "numbers",           # 数字/量化信息
    "business",          # 商业化信息
    "industry_impact",   # 行业影响
    "management_claims", # 管理层表态
    "uncertainties",     # 不确定性/风险
]


def get_daily_data_dir(date_str: str) -> Path:
    """
    获取指定日期的数据存储目录

    :param date_str: 日期字符串，格式为 YYYYMMDD
    :return: 数据目录路径
    """
    daily_dir = RAW_DATA_DIR / date_str
    if not daily_dir.exists():
        daily_dir.mkdir(parents=True, exist_ok=True)
    return daily_dir


def url_to_filename(url: str) -> str:
    """
    将 URL 转换为安全的文件名

    :param url: 原始 URL
    :return: 安全的文件名
    """
    import hashlib
    import re

    # 移除协议前缀
    clean_url = re.sub(r'^https?://', '', url)

    # 提取域名和路径的关键部分
    parts = clean_url.split('/')
    domain = parts[0].replace('.', '_')

    # 使用 URL 的 hash 作为唯一标识
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # 组合文件名
    filename = f"{domain}_{url_hash}.txt"

    return filename
