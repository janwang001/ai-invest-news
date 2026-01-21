# -*- coding: utf-8 -*-
"""
fetch 模块

提供文章抓取、投资信息抽取和轻量化特征提取功能
"""
from .article_fetcher import ArticleFetcher
from .article_fetcher import ArticleResult
from .article_fetcher import fetch_article
from .investment_extractor import ExtractionResult
from .investment_extractor import InvestmentExtractor
from .investment_extractor import InvestmentInfo
from .investment_extractor import extract_investment_info
from .light_features_extractor import LightArticleFeatures
from .light_features_extractor import LightFeaturesExtractor
from .light_features_extractor import extract_light_features

__all__ = [
    # 文章抓取
    "ArticleFetcher",
    "ArticleResult",
    "fetch_article",
    # 投资信息抽取
    "InvestmentExtractor",
    "InvestmentInfo",
    "ExtractionResult",
    "extract_investment_info",
    # 轻量化特征提取
    "LightFeaturesExtractor",
    "LightArticleFeatures",
    "extract_light_features",
]
