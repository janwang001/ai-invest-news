#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资评分卡模块

实现7维度投资评分体系，用于量化评估新闻的投资价值
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# Tier 1 公司列表（高重要性）
TIER1_COMPANIES = {
    "OpenAI", "Microsoft", "Google", "Anthropic", "Meta", "Amazon",
    "NVIDIA", "Apple", "Tesla", "Alibaba", "Tencent", "ByteDance",
    "Baidu", "DeepMind", "Cohere", "Stability AI", "Midjourney"
}

# Tier 1 新闻源（高可信度）
TIER1_SOURCES = {
    "Financial Times", "Bloomberg", "Reuters", "The Wall Street Journal",
    "The Economist", "TechCrunch", "The Information"
}

# 高紧迫性信号
URGENT_SIGNALS = {
    "earnings", "regulation", "acquisition", "product_commercial",
    "funding", "partnership", "layoff"
}

# 创新信号
INNOVATION_SIGNALS = {
    "product_commercial", "product_prototype", "research_breakthrough",
    "algorithm_improvement"
}


@dataclass
class InvestmentScorecard:
    """
    7维度投资评分卡

    每个维度 0-10 分，综合得分 0-100
    """
    materiality_score: float = 0.0      # 重要性：财务影响规模
    urgency_score: float = 0.0          # 紧迫性：时间敏感度
    conviction_score: float = 0.0       # 确信度：证据质量
    competitive_score: float = 0.0      # 竞争影响：竞争格局变化
    risk_score: float = 0.0             # 风险：不确定性水平
    innovation_score: float = 0.0       # 创新度：技术/产品创新
    execution_score: float = 0.0        # 执行力：可执行性

    composite_score: float = 0.0        # 综合得分 0-100
    investment_rating: str = "Pass"     # 投资评级

    # 详细说明
    reasoning: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "materiality_score": round(self.materiality_score, 1),
            "urgency_score": round(self.urgency_score, 1),
            "conviction_score": round(self.conviction_score, 1),
            "competitive_score": round(self.competitive_score, 1),
            "risk_score": round(self.risk_score, 1),
            "innovation_score": round(self.innovation_score, 1),
            "execution_score": round(self.execution_score, 1),
            "composite_score": round(self.composite_score, 1),
            "investment_rating": self.investment_rating,
            "reasoning": self.reasoning,
        }


class InvestmentScorer:
    """投资评分器"""

    def __init__(self):
        # 综合评分权重
        self.weights = {
            "materiality": 0.25,      # 重要性权重最高
            "urgency": 0.20,          # 紧迫性次之
            "conviction": 0.20,       # 确信度次之
            "competitive": 0.15,      # 竞争影响
            "risk": 0.10,             # 风险（反向）
            "innovation": 0.10,       # 创新度
        }

    def calculate_scorecard(self, news: Dict[str, Any]) -> InvestmentScorecard:
        """
        计算7D评分卡

        Args:
            news: 新闻数据字典

        Returns:
            InvestmentScorecard: 评分卡对象
        """
        scorecard = InvestmentScorecard()
        reasoning = {}

        # 1. 重要性评分（Materiality）
        materiality, mat_reason = self._calculate_materiality(news)
        scorecard.materiality_score = materiality
        reasoning["materiality"] = mat_reason

        # 2. 紧迫性评分（Urgency）
        urgency, urg_reason = self._calculate_urgency(news)
        scorecard.urgency_score = urgency
        reasoning["urgency"] = urg_reason

        # 3. 确信度评分（Conviction）
        conviction, conv_reason = self._calculate_conviction(news)
        scorecard.conviction_score = conviction
        reasoning["conviction"] = conv_reason

        # 4. 竞争影响评分（Competitive）
        competitive, comp_reason = self._calculate_competitive(news)
        scorecard.competitive_score = competitive
        reasoning["competitive"] = comp_reason

        # 5. 风险评分（Risk）
        risk, risk_reason = self._calculate_risk(news)
        scorecard.risk_score = risk
        reasoning["risk"] = risk_reason

        # 6. 创新度评分（Innovation）
        innovation, innov_reason = self._calculate_innovation(news)
        scorecard.innovation_score = innovation
        reasoning["innovation"] = innov_reason

        # 7. 执行力评分（Execution）- 暂时使用默认值
        execution = 5.0
        scorecard.execution_score = execution
        reasoning["execution"] = "基于历史执行记录（默认中等）"

        # 计算综合得分（0-100）
        composite = (
            materiality * self.weights["materiality"] +
            urgency * self.weights["urgency"] +
            conviction * self.weights["conviction"] +
            competitive * self.weights["competitive"] +
            (10 - risk) * self.weights["risk"] +  # 风险反向计分
            innovation * self.weights["innovation"]
        ) * 10  # 缩放到0-100

        scorecard.composite_score = composite
        scorecard.reasoning = reasoning

        # 确定投资评级
        if composite >= 80:
            scorecard.investment_rating = "Strong Buy Signal"
        elif composite >= 65:
            scorecard.investment_rating = "Monitor"
        elif composite >= 45:
            scorecard.investment_rating = "Risk Alert"
        else:
            scorecard.investment_rating = "Pass"

        return scorecard

    def _calculate_materiality(self, news: Dict[str, Any]) -> tuple:
        """计算重要性评分"""
        score = 0.0
        reasons = []

        # 检查投资信息维度
        investment_info = news.get("investment_info", {})

        # 有数字信息 +3
        numbers = investment_info.get("numbers", [])
        if numbers:
            score += min(len(numbers) * 1.5, 3.0)
            reasons.append(f"包含{len(numbers)}个数字信息")

        # 有商业化信息 +3
        business = investment_info.get("business", [])
        if business:
            score += min(len(business) * 1.5, 3.0)
            reasons.append(f"包含{len(business)}个商业信息")

        # 涉及Tier 1公司 +4
        companies = news.get("companies", [])
        tier1_companies = [c for c in companies if c in TIER1_COMPANIES]
        if tier1_companies:
            score += 4.0
            reasons.append(f"涉及顶级公司: {', '.join(tier1_companies)}")

        # 有行业影响 +2
        industry_impact = investment_info.get("industry_impact", [])
        if industry_impact:
            score += 2.0
            reasons.append(f"行业影响: {len(industry_impact)}条")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "无明显重要信息"

        return score, reason_text

    def _calculate_urgency(self, news: Dict[str, Any]) -> tuple:
        """计算紧迫性评分"""
        score = 0.0
        reasons = []

        # 检查信号类型
        signals = news.get("signals", [])

        # 高紧迫性信号
        urgent_signals = [s for s in signals if s in URGENT_SIGNALS]
        if urgent_signals:
            score += min(len(urgent_signals) * 3.5, 7.0)
            reasons.append(f"紧急信号: {', '.join(urgent_signals)}")

        # 有管理层表态 +2
        investment_info = news.get("investment_info", {})
        management_claims = investment_info.get("management_claims", [])
        if management_claims:
            score += 2.0
            reasons.append("包含管理层表态")

        # 有时间周期信息 +1
        thesis = investment_info.get("investment_thesis", {})
        if isinstance(thesis, dict):
            time_horizon = thesis.get("time_horizon", "")
            if time_horizon in ["即时", "1-3个月"]:
                score += 1.0
                reasons.append(f"时间敏感: {time_horizon}")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "无明显时间敏感性"

        return score, reason_text

    def _calculate_conviction(self, news: Dict[str, Any]) -> tuple:
        """计算确信度评分"""
        score = 0.0
        reasons = []

        # 来源可信度
        source = news.get("source", "")
        if any(tier1 in source for tier1 in TIER1_SOURCES):
            score += 5.0
            reasons.append(f"顶级来源: {source}")
        else:
            score += 2.0
            reasons.append(f"一般来源: {source}")

        # 有引用 +3
        light_features = news.get("light_features", {})
        if light_features.get("has_quote"):
            score += 3.0
            reasons.append("包含直接引用")

        # 有具体事实 +2
        investment_info = news.get("investment_info", {})
        facts = investment_info.get("facts", [])
        if facts:
            score += 2.0
            reasons.append(f"包含{len(facts)}个事实")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "证据不足"

        return score, reason_text

    def _calculate_competitive(self, news: Dict[str, Any]) -> tuple:
        """计算竞争影响评分"""
        score = 0.0
        reasons = []

        investment_info = news.get("investment_info", {})
        industry_impact = investment_info.get("industry_impact", [])

        # 有行业影响信息
        if industry_impact:
            # 检查竞争相关关键词
            competitive_keywords = [
                "竞争", "市场份额", "份额", "对手", "替代",
                "挑战", "威胁", "优势", "护城河"
            ]

            competitive_items = [
                item for item in industry_impact
                if any(keyword in item for keyword in competitive_keywords)
            ]

            if competitive_items:
                score += min(len(competitive_items) * 3.0, 7.0)
                reasons.append(f"竞争影响: {len(competitive_items)}条")

        # 涉及多个公司 = 可能的竞争动态
        companies = news.get("companies", [])
        if len(companies) >= 2:
            score += 3.0
            reasons.append(f"涉及多家公司: {len(companies)}家")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "无明显竞争影响"

        return score, reason_text

    def _calculate_risk(self, news: Dict[str, Any]) -> tuple:
        """计算风险评分（越高风险越大）"""
        score = 0.0
        reasons = []

        investment_info = news.get("investment_info", {})
        uncertainties = investment_info.get("uncertainties", [])

        # 不确定性数量
        if uncertainties:
            score += min(len(uncertainties) * 2.0, 8.0)
            reasons.append(f"不确定性: {len(uncertainties)}条")

        # Bear case 数量
        thesis = investment_info.get("investment_thesis", {})
        if isinstance(thesis, dict):
            bear_case = thesis.get("bear_case", [])
            if len(bear_case) >= 2:
                score += 2.0
                reasons.append(f"看跌理由: {len(bear_case)}条")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "风险较低"

        return score, reason_text

    def _calculate_innovation(self, news: Dict[str, Any]) -> tuple:
        """计算创新度评分"""
        score = 0.0
        reasons = []

        # 检查信号类型
        signals = news.get("signals", [])
        innovation_signals = [s for s in signals if s in INNOVATION_SIGNALS]

        if innovation_signals:
            score += min(len(innovation_signals) * 4.0, 8.0)
            reasons.append(f"创新信号: {', '.join(innovation_signals)}")

        # 检查是否有产品/技术相关关键词
        title = news.get("title", "").lower()
        content = news.get("content", "").lower()

        innovation_keywords = [
            "breakthrough", "revolutionary", "novel", "first", "new model",
            "突破", "革命", "首次", "新模型", "创新"
        ]

        if any(keyword in title or keyword in content[:500] for keyword in innovation_keywords):
            score += 2.0
            reasons.append("包含创新关键词")

        score = min(score, 10.0)
        reason_text = "; ".join(reasons) if reasons else "无明显创新"

        return score, reason_text


def calculate_investment_scorecard(news: Dict[str, Any]) -> InvestmentScorecard:
    """
    便捷函数：计算投资评分卡

    Args:
        news: 新闻数据字典

    Returns:
        InvestmentScorecard: 评分卡对象
    """
    scorer = InvestmentScorer()
    return scorer.calculate_scorecard(news)


if __name__ == "__main__":
    # 测试代码
    test_news = {
        "title": "OpenAI获66亿美元融资，估值达1570亿美元",
        "source": "Bloomberg",
        "companies": ["OpenAI", "Microsoft"],
        "signals": ["funding", "partnership"],
        "light_features": {
            "has_quote": True,
        },
        "investment_info": {
            "facts": ["OpenAI完成新一轮融资", "微软参与投资"],
            "numbers": ["66亿美元", "1570亿美元估值", "5倍增长"],
            "business": ["企业客户收入增长", "API定价策略"],
            "industry_impact": ["竞争格局变化", "市场份额扩大"],
            "management_claims": ["CEO表示将加速AGI研发"],
            "uncertainties": ["竞争压力", "监管风险"],
            "investment_thesis": {
                "bull_case": ["企业市场快速增长", "技术领先优势", "微软战略支持"],
                "bear_case": ["估值过高", "竞争加剧", "监管不确定性"],
                "key_question": "OpenAI能否在模型商品化时保持定价权？",
                "time_horizon": "6-12个月",
                "comparable_events": ["类似NVIDIA 2016年AI热潮"]
            }
        }
    }

    print("=" * 60)
    print("投资评分卡测试")
    print("=" * 60)

    scorecard = calculate_investment_scorecard(test_news)

    print(f"\n【综合评分】: {scorecard.composite_score:.1f}/100")
    print(f"【投资评级】: {scorecard.investment_rating}")

    print(f"\n【7维度评分】")
    print(f"  重要性 (Materiality): {scorecard.materiality_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('materiality', '')}")
    print(f"  紧迫性 (Urgency): {scorecard.urgency_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('urgency', '')}")
    print(f"  确信度 (Conviction): {scorecard.conviction_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('conviction', '')}")
    print(f"  竞争影响 (Competitive): {scorecard.competitive_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('competitive', '')}")
    print(f"  风险 (Risk): {scorecard.risk_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('risk', '')}")
    print(f"  创新度 (Innovation): {scorecard.innovation_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('innovation', '')}")
    print(f"  执行力 (Execution): {scorecard.execution_score:.1f}/10")
    print(f"    → {scorecard.reasoning.get('execution', '')}")
