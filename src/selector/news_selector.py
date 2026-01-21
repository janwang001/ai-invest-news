#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻选择器模块 - NewsSelectorPipeline类

集成新闻评分、排序和选择功能，用于识别高投资价值的AI新闻。
支持轻量化特征评分（light_features）。
"""

from typing import List, Dict, Any, Tuple
import re
import logging


class NewsSelectorPipeline:
    """新闻选择器管道类，统一管理新闻评分和选择流程"""

    # ===============================
    # 1. 投资事件定义（核心）
    # ===============================
    EVENT_RULES = {
        "earnings": {
            "keywords": ["earnings", "revenue", "profit", "guidance", "forecast"],
            "score": 3.0
        },
        "funding": {
            "keywords": ["funding", "raised", "raise", "series", "investment"],
            "score": 2.5
        },
        "acquisition": {
            "keywords": ["acquire", "acquisition", "merger", "buy"],
            "score": 2.5
        },
        "chip_supply": {
            "keywords": ["gpu", "chip", "semiconductor", "accelerator", "h100", "h200"],
            "score": 2.5
        },
        "product_commercial": {
            "keywords": ["launch", "release", "commercial", "enterprise"],
            "score": 2.0
        },
        "regulation": {
            "keywords": ["regulation", "ban", "export control", "policy"],
            "score": 2.0
        }
    }

    # ===============================
    # 2. 重点公司（投资权重）
    # ===============================
    IMPORTANT_COMPANIES = {
        "nvidia", "openai", "google", "microsoft", "meta",
        "amazon", "tsmc", "amd", "intel", "arm"
    }

    # ===============================
    # 3. PR / 无效内容识别
    # ===============================
    PR_PATTERNS = [
        "we are excited", "proud to announce", "leading provider",
        "groundbreaking", "revolutionary", "award-winning"
    ]

    OPINION_PATTERNS = [
        "opinion", "thoughts on", "what is", "how to", "guide", "tutorial"
    ]

    # ===============================
    # 4. 轻量化特征评分权重
    # ===============================
    LIGHT_FEATURE_WEIGHTS = {
        "content_length_threshold": 1000,  # 内容长度阈值
        "content_length_score": 0.5,       # 内容长度达标加分
        "has_numbers_score": 1.0,          # 有数字加分
        "has_quote_score": 1.5,            # 有引用加分
        "company_count_score": 0.5,        # 每个公司加分（最多2分）
        "company_count_max": 2.0,          # 公司加分上限
        "signal_term_score": 0.3,          # 每个信号词加分（最多2分）
        "signal_term_max": 2.0,            # 信号词加分上限
    }

    def __init__(self, top_k: int = 5):
        """
        初始化新闻选择器管道

        Args:
            top_k: 选择的高价值新闻数量
        """
        self.top_k = top_k
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger

    def _contains_any(self, text: str, patterns: List[str]) -> bool:
        """检查文本是否包含任何指定模式"""
        try:
            text = text.lower()
            return any(p in text for p in patterns)
        except Exception as e:
            self.logger.error(f"检查文本模式时出错: {e}", exc_info=True)
            return False

    def _detect_events(self, text: str) -> List[str]:
        """检测文本中的投资事件"""
        try:
            text = text.lower()
            matched = []
            for event, rule in self.EVENT_RULES.items():
                if any(k in text for k in rule["keywords"]):
                    matched.append(event)
            return matched
        except Exception as e:
            self.logger.error(f"检测事件时出错: {e}", exc_info=True)
            return []

    def _detect_companies(self, text: str) -> List[str]:
        """检测文本中提及的重点公司"""
        try:
            text = text.lower()
            return [c for c in self.IMPORTANT_COMPANIES if c in text]
        except Exception as e:
            self.logger.error(f"检测公司时出错: {e}", exc_info=True)
            return []

    def _has_numbers(self, text: str) -> bool:
        """检查文本是否包含数字（可量化信息）"""
        try:
            return bool(re.search(r"\$?\d+(\.\d+)?", text))
        except Exception as e:
            self.logger.error(f"检测数字时出错: {e}", exc_info=True)
            return False

    def _score_light_features(self, news: Dict[str, Any]) -> float:
        """
        基于轻量化特征计算额外分数

        Args:
            news: 新闻字典，可能包含 light_features 字段

        Returns:
            float: 轻量化特征贡献的分数
        """
        light_features = news.get("light_features", {})
        if not light_features:
            return 0.0

        score = 0.0
        weights = self.LIGHT_FEATURE_WEIGHTS

        # 内容长度评分
        content_length = light_features.get("content_length", 0)
        if content_length >= weights["content_length_threshold"]:
            score += weights["content_length_score"]

        # 数字信息评分
        if light_features.get("has_numbers", False):
            score += weights["has_numbers_score"]

        # 引用评分
        if light_features.get("has_quote", False):
            score += weights["has_quote_score"]

        # 公司提及评分
        company_count = light_features.get("company_count", 0)
        company_score = min(
            company_count * weights["company_count_score"],
            weights["company_count_max"]
        )
        score += company_score

        # 信号词评分
        signal_term_count = light_features.get("signal_term_count", 0)
        signal_score = min(
            signal_term_count * weights["signal_term_score"],
            weights["signal_term_max"]
        )
        score += signal_score

        return round(score, 2)

    def _score_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单条新闻进行投资评分

        Args:
            news: 新闻字典

        Returns:
            包含评分结果的新闻字典
        """
        try:
            score = 0.0
            signals = []

            title = news.get("title", "")
            # 兼容两种字段名：summary 或 content
            summary = news.get("summary", news.get("content", ""))
            text = f"{title} {summary}".lower()

            # --- PR / 观点直接降权 ---
            if self._contains_any(text, self.PR_PATTERNS):
                score -= 2.0

            if self._contains_any(text, self.OPINION_PATTERNS):
                score -= 1.5

            # --- 事件评分 ---
            events = self._detect_events(text)
            for e in events:
                score += self.EVENT_RULES[e]["score"]
                signals.append(e)

            # --- 公司加权 ---
            companies = self._detect_companies(text)
            if companies:
                score += 1.5

            # --- 可量化信息 ---
            if self._has_numbers(text):
                score += 1.0

            # --- 内容长度过滤 ---
            summary_len = len(summary)
            if summary_len < 60:
                score -= 1.0
            elif summary_len > 300:
                score += 0.5

            # --- 轻量化特征评分（新增） ---
            light_feature_score = self._score_light_features(news)
            score += light_feature_score

            news["investment_score"] = round(score, 2)
            news["signals"] = signals
            news["companies"] = companies
            news["light_feature_score"] = light_feature_score

            self.logger.debug(
                f"新闻评分完成 - 标题: {title[:50]}..., "
                f"分数: {score}, 信号: {signals}, "
                f"轻量化特征分: {light_feature_score}"
            )
            return news

        except Exception as e:
            self.logger.error(f"评分新闻时出错: {e}", exc_info=True)
            news["investment_score"] = 0.0
            news["signals"] = []
            news["companies"] = []
            news["light_feature_score"] = 0.0
            return news

    def select_news(self, news_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        执行完整的新闻选择流程：评分 -> 排序 -> 选择

        Args:
            news_list: 新闻列表

        Returns:
            tuple: (selected_news, stats)
                - selected_news: 高价值资讯（top_k）
                - stats: 选择统计信息
        """
        self.logger.info("=" * 50)
        self.logger.info(f"开始新闻选择流程 - 输入: {len(news_list)} 条，top_k: {self.top_k}")
        self.logger.info("=" * 50)

        stats = {
            "input_count": len(news_list),
            "selected_count": 0,
            "dropped_count": 0,
            "top_k": self.top_k,
            "average_score": 0.0,
            "score_distribution": {},
            "light_features_count": 0,  # 新增：有轻量化特征的新闻数量
        }

        try:
            if not isinstance(news_list, list):
                self.logger.error(f"输入不是列表类型: {type(news_list)}")
                raise TypeError(f"news_list 应该是列表，但收到 {type(news_list)}")

            if not news_list:
                self.logger.warning("输入新闻列表为空")
                return [], stats

            # 统计有轻量化特征的新闻数量
            light_features_count = sum(
                1 for n in news_list if n.get("light_features")
            )
            stats["light_features_count"] = light_features_count

            # 步骤1：评分
            self.logger.info(f"\n【步骤1】评分 - 处理 {len(news_list)} 条新闻")
            self.logger.info(f"其中 {light_features_count} 条带有轻量化特征")
            scored = []
            for idx, n in enumerate(news_list, 1):
                try:
                    if not isinstance(n, dict):
                        self.logger.warning(f"[{idx}] 条目不是字典类型，跳过")
                        continue
                    scored_item = self._score_news(n.copy())
                    scored.append(scored_item)
                    self.logger.debug(
                        f"[{idx}] ✓ {scored_item.get('title', '未知')[:40]}... "
                        f"分数: {scored_item.get('investment_score', 0)}"
                    )
                except Exception as e:
                    self.logger.error(f"[{idx}] 评分失败: {e}", exc_info=True)
                    continue

            if not scored:
                self.logger.warning("评分后无有效新闻")
                return [], stats

            self.logger.info(f"评分完成 - 共评分 {len(scored)} 条")

            # 步骤2：排序
            self.logger.info(f"\n【步骤2】排序")
            scored.sort(key=lambda x: x["investment_score"], reverse=True)
            scores = [n.get("investment_score", 0) for n in scored]
            avg_score = sum(scores) / len(scores) if scores else 0
            stats["average_score"] = round(avg_score, 2)
            self.logger.info(f"排序完成 - 平均分数: {stats['average_score']}")

            # 步骤3：选择和过滤
            self.logger.info(f"\n【步骤3】选择前 {self.top_k} 条（过滤分数 <= 0）")
            selected = [n for n in scored if n["investment_score"] > 0][:self.top_k]
            dropped = [n for n in scored if n["investment_score"] <= 0]

            stats["selected_count"] = len(selected)
            stats["dropped_count"] = len(dropped)
            stats["output_count"] = len(selected)

            # 分数分布统计
            score_ranges = {"<0": 0, "0-0.5": 0, "0.5-1": 0, ">1": 0}
            for n in scored:
                s = n.get("investment_score", 0)
                if s < 0:
                    score_ranges["<0"] += 1
                elif s <= 0.5:
                    score_ranges["0-0.5"] += 1
                elif s <= 1:
                    score_ranges["0.5-1"] += 1
                else:
                    score_ranges[">1"] += 1
            stats["score_distribution"] = score_ranges

            self.logger.info(f"选择完成 - 选中: {stats['selected_count']} 条，过滤: {stats['dropped_count']} 条")
            self.logger.info(f"分数分布 - {score_ranges}")
            self.logger.info("=" * 50)

            return selected, stats

        except Exception as e:
            self.logger.error(f"新闻选择流程失败: {e}", exc_info=True)
            raise


def news_select(news_list: List[Dict[str, Any]], top_k: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    函数式接口：新闻选择流程
    
    Args:
        news_list: 新闻列表
        top_k: 选择的高价值新闻数量
        
    Returns:
        tuple: (selected_news, stats)
    """
    pipeline = NewsSelectorPipeline(top_k=top_k)
    return pipeline.select_news(news_list)


def main():
    """测试函数"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("="*50)
        logger.info("开始新闻选择模块测试")
        logger.info("="*50)
        
        # 测试数据
        test_news = [
            {
                "title": "NVIDIA 发布新 GPU 芯片",
                "summary": "NVIDIA 宣布推出最新的 H200 GPU 芯片，性能提升 50%，售价 $35000"
            },
            {
                "title": "OpenAI 获得新融资",
                "summary": "OpenAI 获得 B 轮融资 1 亿美元，用于 GPT 模型研发"
            },
            {
                "title": "我对 AI 的看法",
                "summary": "这是我的观点和想法，关于如何理解 AI 技术"
            },
            {
                "标题": "微软宣布激动人心的产品",
                "summary": "we are excited to announce 一款革命性产品，groundbreaking 技术"
            },
            {
                "标题": "AMD 与 Intel 合并谈判",
                "summary": "两家芯片公司进行收购谈判，涉及金额 $50 亿"
            }
        ]
        
        # 使用NewsSelectorPipeline类
        pipeline = NewsSelectorPipeline(top_k=3)
        selected, stats = pipeline.select_news(test_news)
        
        print("\n" + "="*50)
        print(f"测试结果 - 选中 {stats['selected_count']} 条新闻")
        print("="*50)
        
        for idx, news in enumerate(selected, 1):
            print(f"\n[{idx}] {news.get('title', '未知')}")
            print(f"    投资评分: {news.get('investment_score', 0)}")
            print(f"    信号: {news.get('signals', [])}")
            print(f"    公司: {news.get('companies', [])}")
        
        print("\n" + "="*50)
        print("统计信息")
        print("="*50)
        print(f"输入: {stats['input_count']} 条")
        print(f"选中: {stats['selected_count']} 条（top_k={stats['top_k']}）")
        print(f"过滤: {stats['dropped_count']} 条")
        print(f"平均分数: {stats['average_score']}")
        print(f"分数分布: {stats['score_distribution']}")
        
        logger.info("="*50)
        logger.info("测试完成")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {e}", exc_info=True)
        print(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()
