#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H5 应用数据导出器

将分析结果导出为 JSON 格式，供 H5 前端应用使用。
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WebDataExporter:
    """H5 应用数据导出器"""

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化导出器

        Args:
            output_dir: 输出目录，默认为 webapp/data
        """
        if output_dir is None:
            # 默认输出到 webapp/data 目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "webapp", "data")

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"WebDataExporter 初始化，输出目录: {self.output_dir}")

    def export(self, result: Dict[str, Any], stats: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        导出分析结果到 JSON 文件

        Args:
            result: 分析结果字典，包含 date, news, events
            stats: 可选的统计信息

        Returns:
            dict: 导出结果，包含文件路径
        """
        export_result = {
            "success": False,
            "data_file": "",
            "index_file": ""
        }

        try:
            date_str = result.get("date", datetime.now().strftime("%Y-%m-%d"))

            # 1. 导出当天的详细数据
            data_file = self._export_daily_data(result, date_str)
            export_result["data_file"] = data_file

            # 2. 更新索引文件
            index_file = self._update_index(result, date_str)
            export_result["index_file"] = index_file

            export_result["success"] = True
            logger.info(f"数据导出成功: {data_file}")

        except Exception as e:
            logger.error(f"数据导出失败: {e}", exc_info=True)
            export_result["error"] = str(e)

        return export_result

    def _export_daily_data(self, result: Dict[str, Any], date_str: str) -> str:
        """
        导出当天的详细数据

        Args:
            result: 分析结果
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            str: 导出的文件路径
        """
        # 文件名格式: 20260120.json
        filename = date_str.replace("-", "") + ".json"
        file_path = os.path.join(self.output_dir, filename)

        # 处理数据，移除过大的字段
        export_data = self._prepare_export_data(result)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return file_path

    def _prepare_export_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备导出数据，移除不需要的大字段

        Args:
            result: 原始分析结果

        Returns:
            dict: 处理后的数据
        """
        export_data = {
            "date": result.get("date", ""),
            "news": [],
            "events": []
        }

        # 处理新闻列表
        for news in result.get("news", []):
            news_item = {
                "title": news.get("title", ""),
                "url": news.get("url", ""),
                "source": news.get("source", ""),
                "published_at": news.get("published_at", ""),
                "ai_summary": news.get("ai_summary", ""),
            }

            # 投资信息
            if news.get("investment_info"):
                news_item["investment_info"] = self._simplify_investment_info(
                    news.get("investment_info", {})
                )

            export_data["news"].append(news_item)

        # 处理事件列表
        for event in result.get("events", []):
            event_item = {
                "representative_title": event.get("representative_title", ""),
                "summary": event.get("summary", ""),
                "news_count": event.get("news_count", 0),
                "sources": event.get("sources", []),
                "companies": event.get("companies", []),
                "news_indices": event.get("news_indices", []),
                "decision": event.get("decision", {})
            }
            export_data["events"].append(event_item)

        return export_data

    def _simplify_investment_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        简化投资信息，保留关键字段

        Args:
            info: 原始投资信息

        Returns:
            dict: 简化后的投资信息
        """
        return {
            "core_thesis": info.get("core_thesis", ""),
            "market_impact": info.get("market_impact", ""),
            "risk_factors": info.get("risk_factors", []),
            "time_horizon": info.get("time_horizon", ""),
            "related_tickers": info.get("related_tickers", []),
            "confidence_level": info.get("confidence_level", "")
        }

    def _update_index(self, result: Dict[str, Any], date_str: str) -> str:
        """
        更新索引文件，记录所有可用的日期数据

        Args:
            result: 分析结果
            date_str: 日期字符串

        Returns:
            str: 索引文件路径
        """
        index_file = os.path.join(self.output_dir, "index.json")

        # 读取现有索引
        index_data = {"articles": [], "last_updated": ""}
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception:
                pass

        # 构建当天的索引项
        events = result.get("events", [])
        top_events = []
        for event in events[:3]:  # 取前3个事件作为预览
            decision = event.get("decision", {})
            top_events.append({
                "title": event.get("representative_title", "")[:50],
                "signal": decision.get("signal", "neutral")
            })

        article_item = {
            "date": date_str,
            "eventCount": len(events),
            "newsCount": len(result.get("news", [])),
            "topEvents": top_events
        }

        # 更新或添加索引项
        articles = index_data.get("articles", [])
        existing_index = next(
            (i for i, a in enumerate(articles) if a.get("date") == date_str),
            None
        )

        if existing_index is not None:
            articles[existing_index] = article_item
        else:
            articles.insert(0, article_item)  # 新数据插入到最前面

        # 按日期排序（降序）
        articles.sort(key=lambda x: x.get("date", ""), reverse=True)

        # 保留最近30天的数据
        articles = articles[:30]

        index_data["articles"] = articles
        index_data["last_updated"] = datetime.now().isoformat()

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return index_file


def export_to_webapp(result: Dict[str, Any], stats: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    便捷函数：导出数据到 H5 应用

    Args:
        result: 分析结果
        stats: 可选的统计信息

    Returns:
        dict: 导出结果
    """
    exporter = WebDataExporter()
    return exporter.export(result, stats)
