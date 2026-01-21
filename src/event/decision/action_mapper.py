"""
事件动作映射器
importance + signal → action
"""

import logging

logger = logging.getLogger(__name__)


class EventActionMapper:
    """
    importance + signal → action
    """

    def map(self, importance: str, signal: str) -> str:
        """
        根据重要性和信号映射投资动作
        
        Args:
            importance: 重要性级别（"High" / "Medium" / "Low"）
            signal: 信号方向（"Positive" / "Neutral" / "Risk"）
            
        Returns:
            str: 投资动作（"Watch" / "Hold" / "Avoid"）
        """
        try:
            # 验证输入参数
            valid_importance = {"High", "Medium", "Low"}
            valid_signal = {"Positive", "Neutral", "Risk"}
            
            if importance not in valid_importance:
                logger.warning(f"无效的重要性级别: {importance}，使用默认值'Low'")
                importance = "Low"
            
            if signal not in valid_signal:
                logger.warning(f"无效的信号方向: {signal}，使用默认值'Neutral'")
                signal = "Neutral"

            # 根据规则映射动作
            if importance == "High":
                if signal == "Positive":
                    action = "Hold"
                elif signal == "Risk":
                    action = "Avoid"
                else:
                    action = "Watch"
            elif importance == "Medium":
                if signal == "Positive":
                    action = "Watch"
                elif signal == "Risk":
                    action = "Avoid"
                else:
                    action = "Watch"
            else:
                action = "Avoid"

            logger.debug(f"动作映射: {importance} + {signal} → {action}")
            return action

        except Exception as e:
            logger.error(f"动作映射失败: {e}", exc_info=True)
            # 映射失败时返回最保守的动作
            return "Avoid"