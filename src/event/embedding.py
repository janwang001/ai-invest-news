"""
文本嵌入模块

该模块负责将新闻文本转换为向量表示，用于后续的聚类和事件检测。
支持结构化提示和嵌入缓存优化。
"""

import hashlib
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from .event_config import EMBEDDING_MODEL, EMBEDDING_DIMENSION


class TextEmbedder:
    """文本嵌入器，支持结构化提示和嵌入缓存"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        初始化文本嵌入器
        
        Args:
            model_name: 嵌入模型名称
        """
        self.model = SentenceTransformer(model_name)
        self._embedding_cache = {}  # 嵌入缓存字典
    
    def _generate_cache_key(self, text: str) -> str:
        """
        生成缓存键
        
        Args:
            text: 文本内容
            
        Returns:
            str: 缓存键（MD5哈希）
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _build_structured_prompt(self, news: Dict[str, Any]) -> str:
        """
        构建结构化提示文本
        
        Args:
            news: 新闻字典
            
        Returns:
            str: 结构化提示文本
        """
        title = news.get('title', '')
        content = news.get('content', '')
        signals = news.get('signals', [])
        companies = news.get('companies', [])
        
        # 构建结构化提示，增强事件语义理解
        structured_text = f"""
标题: {title}
内容: {content}
信号: {', '.join(signals) if signals else '无'}
公司: {', '.join(companies) if companies else '无'}
""".strip()
        
        return structured_text
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        对文本列表进行嵌入，支持缓存
        
        Args:
            texts: 文本列表
            
        Returns:
            np.ndarray: 嵌入向量矩阵
        """
        if not texts:
            return np.array([])
        
        # 检查缓存并批量处理未缓存的文本
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._generate_cache_key(text)
            if cache_key in self._embedding_cache:
                cached_embeddings.append(self._embedding_cache[cache_key])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 批量嵌入未缓存的文本
        if uncached_texts:
            new_embeddings = self.model.encode(uncached_texts, convert_to_numpy=True)
            
            # 缓存新嵌入结果
            for j, text in enumerate(uncached_texts):
                cache_key = self._generate_cache_key(text)
                self._embedding_cache[cache_key] = new_embeddings[j]
        
        # 合并所有嵌入结果
        all_embeddings = []
        cached_idx = 0
        uncached_idx = 0
        
        for i in range(len(texts)):
            if i in uncached_indices:
                all_embeddings.append(new_embeddings[uncached_idx])
                uncached_idx += 1
            else:
                all_embeddings.append(cached_embeddings[cached_idx])
                cached_idx += 1
        
        return np.array(all_embeddings)
    
    def embed_news(self, news_list: List[Dict[str, Any]]) -> np.ndarray:
        """
        对新闻列表进行嵌入，使用结构化提示
        
        Args:
            news_list: 新闻列表
            
        Returns:
            np.ndarray: 嵌入向量矩阵
        """
        if not news_list:
            return np.array([])
        
        # 使用结构化提示构建嵌入文本
        texts = []
        for news in news_list:
            structured_text = self._build_structured_prompt(news)
            texts.append(structured_text)
        
        return self.embed_texts(texts)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, int]: 缓存统计信息
        """
        return {
            "cache_size": len(self._embedding_cache),
            "cache_hits": sum(1 for key in self._embedding_cache if key.startswith("hit_")),
            "cache_misses": sum(1 for key in self._embedding_cache if key.startswith("miss_"))
        }
    
    def clear_cache(self) -> None:
        """清空嵌入缓存"""
        self._embedding_cache.clear()