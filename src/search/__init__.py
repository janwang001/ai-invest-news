"""Search module - RSS fetching and result processing"""

from .rss_config import *
from .search_pipeline import SearchPipeline
from .search_result_process import normalize_news, deduplicate_news, merge_similar_news

__all__ = [
    "SearchPipeline",
    "normalize_news",
    "deduplicate_news", 
    "merge_similar_news"
]
