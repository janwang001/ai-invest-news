"""
事件决策流水线
对 Event 进行完整决策判断
"""

import logging
from typing import List, Dict, Tuple

from .importance_evaluator import EventImportanceEvaluator
from .signal_classifier import EventSignalClassifier
from .action_mapper import EventActionMapper

logger = logging.getLogger(__name__)


class EventDecisionPipeline:
    """
    对 Event 进行完整决策判断
    """

    def __init__(self):
        """初始化决策组件"""
        self.importance_evaluator = EventImportanceEvaluator()
        self.signal_classifier = EventSignalClassifier()
        self.action_mapper = EventActionMapper()

    def decide(self, events: List[Dict]) -> List[Dict]:
        """
        对事件列表进行决策判断
        
        Args:
            events: 事件列表，每个事件包含新闻列表等信息
            
        Returns:
            List[Dict]: 添加了决策信息的事件列表
        """
        decided_events = []

        for event in events:
            importance = self.importance_evaluator.evaluate(event)
            signal = self.signal_classifier.classify(event)
            action = self.action_mapper.map(importance, signal)

            event["decision"] = {
                "importance": importance,
                "signal": signal,
                "action": action,
            }

            decided_events.append(event)

        return decided_events

    def decide_with_stats(self, events: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        对事件列表进行决策判断并返回统计信息
        
        Args:
            events: 事件列表，每个事件包含新闻列表等信息
            
        Returns:
            Tuple[List[Dict], Dict]: (决策后的事件列表, 统计信息字典)
        """
        if not events:
            logger.info("无事件需要决策，返回空结果")
            return [], {"total_events": 0, "success_count": 0, "error_count": 0}

        decided_events = []
        stats = {
            "total_events": len(events),
            "success_count": 0,
            "error_count": 0,
            "importance_distribution": {"High": 0, "Medium": 0, "Low": 0},
            "signal_distribution": {"Positive": 0, "Neutral": 0, "Risk": 0},
            "action_distribution": {"Watch": 0, "Hold": 0, "Avoid": 0},
            "errors": []
        }

        logger.info(f"开始对 {len(events)} 个事件进行决策判断")

        for i, event in enumerate(events):
            try:
                # 重要性评估
                importance = self.importance_evaluator.evaluate(event)
                stats["importance_distribution"][importance] += 1
                
                # 信号分类
                signal = self.signal_classifier.classify(event)
                stats["signal_distribution"][signal] += 1
                
                # 动作映射
                action = self.action_mapper.map(importance, signal)
                stats["action_distribution"][action] += 1

                event["decision"] = {
                    "importance": importance,
                    "signal": signal,
                    "action": action,
                }

                decided_events.append(event)
                stats["success_count"] += 1
                
                logger.debug(f"事件 {i+1}/{len(events)} 决策完成: {importance} | {signal} | {action}")

            except Exception as e:
                error_msg = f"事件 {i+1}/{len(events)} 决策失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats["error_count"] += 1
                stats["errors"].append(error_msg)
                
                # 决策失败的事件仍然保留，但不添加决策信息
                decided_events.append(event)

        # 计算成功率
        stats["success_rate"] = stats["success_count"] / max(stats["total_events"], 1)
        
        logger.info(f"决策完成: 成功 {stats['success_count']}/{stats['total_events']} "
                   f"(成功率: {stats['success_rate']:.1%})")
        
        if stats["error_count"] > 0:
            logger.warning(f"有 {stats['error_count']} 个事件决策失败")

        return decided_events, stats