"""
新闻聚类模块

该模块负责对新闻进行聚类分析，识别相关事件。
支持智能聚类策略和事件有效性判断。
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.cluster import DBSCAN
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity

from .event_config import CLUSTERING_ALGORITHM, MIN_CLUSTER_SIZE, CLUSTER_SELECTION_EPSILON, MIN_EVENT_SIZE


class NewsClusterer:
    """新闻聚类器，支持智能聚类策略和事件有效性判断"""
    
    def __init__(self, algorithm: str = CLUSTERING_ALGORITHM):
        """
        初始化新闻聚类器
        
        Args:
            algorithm: 聚类算法名称
        """
        self.algorithm = algorithm
        self.clusterer = None
        
        # 事件有效性判断阈值
        self.MIN_COMPANY_COUNT = 1  # 最小公司数量
        self.MIN_SIGNAL_COUNT = 1   # 最小信号数量
        self.MIN_INVESTMENT_SCORE = 0.3  # 最小投资分数阈值
    
    def _cosine_greedy_clustering(self, embeddings: np.ndarray, similarity_threshold: float = 0.7) -> np.ndarray:
        """
        贪心余弦相似度聚类算法，适用于小规模数据
        
        Args:
            embeddings: 嵌入向量矩阵
            similarity_threshold: 相似度阈值
            
        Returns:
            np.ndarray: 聚类标签
        """
        n = len(embeddings)
        if n == 0:
            return np.array([])
        
        labels = np.full(n, -1)  # 初始化为噪声点
        cluster_id = 0
        
        # 计算余弦相似度矩阵
        similarity_matrix = cosine_similarity(embeddings)
        
        # 贪心聚类
        for i in range(n):
            if labels[i] != -1:  # 已分配聚类
                continue
            
            # 找到与当前点相似度超过阈值的点
            similar_indices = np.where(similarity_matrix[i] > similarity_threshold)[0]
            
            if len(similar_indices) >= MIN_CLUSTER_SIZE:
                # 分配聚类标签
                labels[similar_indices] = cluster_id
                cluster_id += 1
        
        return labels
    
    def _is_valid_event(self, cluster: List[Dict[str, Any]]) -> bool:
        """
        判断聚类是否为有效事件
        
        Args:
            cluster: 聚类中的新闻列表
            
        Returns:
            bool: 是否为有效事件
        """
        if len(cluster) < MIN_EVENT_SIZE:
            return False
        
        # 统计公司数量和信号数量
        all_companies = set()
        all_signals = set()
        total_investment_score = 0.0
        
        for news in cluster:
            companies = news.get('companies', [])
            signals = news.get('signals', [])
            investment_score = news.get('investment_score', 0.0)
            
            all_companies.update(companies)
            all_signals.update(signals)
            total_investment_score += investment_score
        
        avg_investment_score = total_investment_score / len(cluster)
        
        # 事件有效性判断
        company_condition = len(all_companies) >= self.MIN_COMPANY_COUNT
        signal_condition = len(all_signals) >= self.MIN_SIGNAL_COUNT
        score_condition = avg_investment_score >= self.MIN_INVESTMENT_SCORE
        
        return company_condition and signal_condition and score_condition
    
    def fit_cluster(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        对嵌入向量进行聚类，根据数据规模选择算法
        
        Args:
            embeddings: 文本嵌入向量矩阵
            
        Returns:
            Tuple[np.ndarray, Dict]: 聚类标签和聚类统计信息
        """
        if embeddings.size == 0:
            return np.array([]), {"n_clusters": 0, "noise_points": 0}
        
        n_samples = len(embeddings)
        
        # 智能聚类策略：小规模数据用贪心算法，大规模数据用HDBSCAN
        if n_samples <= 10:
            # 小规模数据使用贪心余弦聚类
            labels = self._cosine_greedy_clustering(embeddings)
            algorithm_used = "cosine_greedy"
        else:
            # 大规模数据使用HDBSCAN
            if self.algorithm == "hdbscan":
                self.clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=MIN_CLUSTER_SIZE,
                    cluster_selection_epsilon=CLUSTER_SELECTION_EPSILON
                )
            else:
                # 默认使用DBSCAN
                self.clusterer = DBSCAN(eps=0.5, min_samples=MIN_CLUSTER_SIZE)
            
            labels = self.clusterer.fit_predict(embeddings)
            algorithm_used = self.algorithm
        
        # 统计聚类信息
        unique_labels = set(labels)
        n_clusters = len([l for l in unique_labels if l != -1])  # 排除噪声点
        noise_points = np.sum(labels == -1)
        
        stats = {
            "n_clusters": n_clusters,
            "noise_points": noise_points,
            "total_points": len(labels),
            "algorithm_used": algorithm_used,
            "sample_size": n_samples
        }
        
        return labels, stats
    
    def cluster_news(self, news_list: List[Dict[str, Any]], embeddings: np.ndarray) -> List[List[Dict[str, Any]]]:
        """
        对新闻进行聚类分组，并进行事件有效性判断
        
        Args:
            news_list: 新闻列表
            embeddings: 对应的嵌入向量
            
        Returns:
            List[List[Dict]]: 按聚类分组的有效事件列表
        """
        if not news_list or embeddings.size == 0:
            return []
        
        labels, stats = self.fit_cluster(embeddings)
        
        # 按聚类标签分组新闻
        clusters = {}
        for i, (news, label) in enumerate(zip(news_list, labels)):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(news)
        
        # 过滤噪声点（标签为-1）
        valid_clusters = [cluster for label, cluster in clusters.items() if label != -1]
        
        # 事件有效性判断：语义层过滤
        final_events = []
        for cluster in valid_clusters:
            if self._is_valid_event(cluster):
                final_events.append(cluster)
        
        # 记录有效性统计
        stats["original_clusters"] = len(valid_clusters)
        stats["valid_events"] = len(final_events)
        stats["filtered_clusters"] = len(valid_clusters) - len(final_events)
        
        return final_events
    
    def get_clustering_stats(self) -> Dict[str, Any]:
        """
        获取聚类统计信息
        
        Returns:
            Dict[str, Any]: 聚类统计信息
        """
        return {
            "min_company_count": self.MIN_COMPANY_COUNT,
            "min_signal_count": self.MIN_SIGNAL_COUNT,
            "min_investment_score": self.MIN_INVESTMENT_SCORE,
            "min_event_size": MIN_EVENT_SIZE
        }