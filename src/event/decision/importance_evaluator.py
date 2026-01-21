"""
事件重要性评估器
判断事件的重要程度：High / Medium / Low
"""

import logging
from typing import Dict
from .decision_config import IMPORTANCE_THRESHOLDS

logger = logging.getLogger(__name__)


class EventImportanceEvaluator:
    """
    判断事件的重要程度：High / Medium / Low
    """

    def evaluate(self, event: Dict) -> str:
        """
        评估事件重要性
        
        Args:
            event: 事件字典，包含新闻列表等信息
            
        Returns:
            str: 重要性级别（"High" / "Medium" / "Low"）
        """
        try:
            news_count = event.get("news_count", 0)
            sources = set(event.get("sources", []))
            avg_score = self._avg_investment_score(event)

            logger.debug(f"重要性评估: 新闻数={news_count}, 来源数={len(sources)}, 平均分数={avg_score:.3f}")

            if self._match("high", news_count, sources, avg_score):
                logger.debug("事件重要性评估为: High")
                return "High"

            if self._match("medium", news_count, sources, avg_score):
                logger.debug("事件重要性评估为: Medium")
                return "Medium"

            logger.debug("事件重要性评估为: Low")
            return "Low"

        except Exception as e:
            logger.error(f"事件重要性评估失败: {e}", exc_info=True)
            # 评估失败时返回Low级别，避免影响后续流程
            return "Low"

    def _avg_investment_score(self, event: Dict) -> float:
        """计算事件的平均投资分数"""
        scores = [
            n.get("investment_score", 0.0)
            for n in event.get("news_list", [])
        ]
        return sum(scores) / max(len(scores), 1)

    def _match(self, level: str, news_count: int, sources: set, score: float) -> bool:
        """检查是否满足指定级别的重要性阈值"""
        cfg = IMPORTANCE_THRESHOLDS[level]
        return (
            news_count >= cfg["min_news"]
            and len(sources) >= cfg["min_sources"]
            and score >= cfg["min_score"]
        )