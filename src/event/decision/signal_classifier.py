"""
事件信号分类器
判断事件的市场信号方向：Positive / Neutral / Risk
"""

import logging
from typing import Dict, List
from .decision_config import POSITIVE_SIGNALS, RISK_SIGNALS

logger = logging.getLogger(__name__)


class EventSignalClassifier:
    """
    判断事件的市场信号方向
    """

    def classify(self, event: Dict) -> str:
        """
        分类事件信号方向
        
        Args:
            event: 事件字典，包含新闻列表等信息
            
        Returns:
            str: 信号方向（"Positive" / "Neutral" / "Risk"）
        """
        try:
            signals = self._collect_signals(event)

            has_positive = bool(signals & POSITIVE_SIGNALS)
            has_risk = bool(signals & RISK_SIGNALS)

            logger.debug(f"信号分类: 收集到 {len(signals)} 个信号，正面信号={has_positive}, 风险信号={has_risk}")

            if has_positive and not has_risk:
                logger.debug("事件信号分类为: Positive")
                return "Positive"

            if has_risk and not has_positive:
                logger.debug("事件信号分类为: Risk")
                return "Risk"

            if has_positive and has_risk:
                logger.debug("事件信号分类为: Neutral (混合信号)")
                return "Neutral"

            logger.debug("事件信号分类为: Neutral (无明确信号)")
            return "Neutral"

        except Exception as e:
            logger.error(f"事件信号分类失败: {e}", exc_info=True)
            # 分类失败时返回Neutral，避免影响后续流程
            return "Neutral"

    def _collect_signals(self, event: Dict) -> set:
        """从事件中收集所有信号关键词"""
        collected = set()
        for news in event.get("news_list", []):
            collected.update(news.get("signals", []))
        return collected