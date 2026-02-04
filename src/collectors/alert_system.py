#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精准警报系统

3级优先级警报:
- P0: 超高优先级（5分钟内推送）- 重大监管行动、IPO、大额融资
- P1: 高优先级（1小时内汇总）- 8-K重大事件、监管新闻
- P2: 中优先级（每日汇总）- 一般Form D、持股变动
"""

import logging
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """警报优先级"""
    P0 = "P0"  # 5分钟内推送
    P1 = "P1"  # 1小时内汇总
    P2 = "P2"  # 每日汇总


class AlertType(Enum):
    """警报类型"""
    SEC_FILING = "sec_filing"      # SEC文件
    REGULATORY = "regulatory"       # 监管行动
    STOCK_MOVE = "stock_move"      # 股价异动
    BREAKING = "breaking"          # 突发新闻


@dataclass
class Alert:
    """警报数据结构"""
    alert_id: str
    priority: str  # P0/P1/P2
    alert_type: str
    title: str
    summary: str
    source: str
    url: str
    timestamp: str

    # 详细信息
    company: Optional[str] = None
    filing_type: Optional[str] = None
    amount: Optional[str] = None

    # 投资相关
    investment_signal: str = "Neutral"  # Positive/Negative/Neutral
    action_required: str = "Monitor"     # Immediate/Watch/Monitor

    # 元数据
    raw_data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AlertSystem:
    """精准警报系统"""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_counter = 0

        # P0触发条件
        self.p0_triggers = {
            # SEC相关
            "sec_forms": ["S-1", "S-1/A"],  # IPO注册
            "sec_8k_items": ["item 1.01", "item 2.02"],  # 收购、财务业绩
            "funding_threshold": 100_000_000,  # $100M以上融资

            # 监管相关
            "regulatory_keywords": [
                "lawsuit", "investigation", "charges", "criminal",
                "antitrust", "monopoly", "fine", "penalty", "ban",
                "injunction", "enforcement action", "settlement"
            ],
        }

        # AI相关公司（优先监控）
        self.priority_companies = [
            "OpenAI", "Anthropic", "Google", "Microsoft", "Meta",
            "Amazon", "NVIDIA", "xAI", "Cohere", "Mistral",
            "DeepMind", "Inflection", "Stability AI"
        ]

    def _generate_alert_id(self) -> str:
        """生成警报ID"""
        self.alert_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ALERT-{timestamp}-{self.alert_counter:04d}"

    def process_sec_filing(self, filing: Dict) -> Optional[Alert]:
        """
        处理SEC文件，生成警报

        Args:
            filing: SEC文件数据

        Returns:
            Alert对象或None
        """
        try:
            filing_type = filing.get("filing_type", "")
            company = filing.get("company_name", "Unknown")

            # 确定优先级
            priority = self._determine_sec_priority(filing)

            # 确定投资信号
            signal, action = self._determine_investment_signal(filing, "sec")

            # 生成摘要
            summary = self._generate_sec_summary(filing)

            alert = Alert(
                alert_id=self._generate_alert_id(),
                priority=priority,
                alert_type=AlertType.SEC_FILING.value,
                title=f"[{filing_type}] {company}",
                summary=summary,
                source="SEC EDGAR",
                url=filing.get("link", ""),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                company=company,
                filing_type=filing_type,
                amount=self._extract_amount(filing),
                investment_signal=signal,
                action_required=action,
                raw_data=filing
            )

            self.alerts.append(alert)
            logger.info(f"生成SEC警报: {alert.priority} - {alert.title}")

            return alert

        except Exception as e:
            logger.error(f"处理SEC文件失败: {e}")
            return None

    def process_regulatory_news(self, news: Dict) -> Optional[Alert]:
        """
        处理监管新闻，生成警报

        Args:
            news: 监管新闻数据

        Returns:
            Alert对象或None
        """
        try:
            source = news.get("source", "Unknown")
            agency = news.get("agency", source)

            # 确定优先级
            priority = self._determine_regulatory_priority(news)

            # 确定投资信号
            signal, action = self._determine_investment_signal(news, "regulatory")

            # 提取涉及的公司
            company = self._extract_company_from_text(
                f"{news.get('title', '')} {news.get('summary', '')}"
            )

            alert = Alert(
                alert_id=self._generate_alert_id(),
                priority=priority,
                alert_type=AlertType.REGULATORY.value,
                title=f"[{source}] {news.get('title', '')[:80]}",
                summary=news.get("summary", "")[:300],
                source=agency,
                url=news.get("link", ""),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                company=company,
                investment_signal=signal,
                action_required=action,
                raw_data=news
            )

            self.alerts.append(alert)
            logger.info(f"生成监管警报: {alert.priority} - {alert.title[:50]}")

            return alert

        except Exception as e:
            logger.error(f"处理监管新闻失败: {e}")
            return None

    def _determine_sec_priority(self, filing: Dict) -> str:
        """确定SEC文件优先级"""
        filing_type = filing.get("filing_type", "")

        # P0: IPO注册
        if filing_type in self.p0_triggers["sec_forms"]:
            return AlertPriority.P0.value

        # P0: 大额融资 (>$100M)
        funding_info = filing.get("funding_info", {})
        total_sold = funding_info.get("total_sold", "0")
        try:
            amount = float(total_sold.replace(",", "").replace("$", ""))
            if amount >= self.p0_triggers["funding_threshold"]:
                return AlertPriority.P0.value
        except (ValueError, AttributeError):
            pass

        # P0: 8-K重大事件（收购、财务业绩）
        if filing_type in ["8-K", "8-K/A"]:
            items = filing.get("8k_items", [])
            for item in items:
                if item.get("code", "").lower() in self.p0_triggers["sec_8k_items"]:
                    return AlertPriority.P0.value
            # 8-K但非重大item = P1
            return AlertPriority.P1.value

        # P1: Form D融资
        if filing_type in ["D", "D/A"]:
            return AlertPriority.P1.value

        # P1: 13D激进投资
        if filing_type in ["13D", "SC 13D"]:
            return AlertPriority.P1.value

        # P2: 其他
        return AlertPriority.P2.value

    def _determine_regulatory_priority(self, news: Dict) -> str:
        """确定监管新闻优先级"""
        text = f"{news.get('title', '')} {news.get('summary', '')} {news.get('content', '')}".lower()

        # 检查P0触发关键词
        for keyword in self.p0_triggers["regulatory_keywords"]:
            if keyword.lower() in text:
                return AlertPriority.P0.value

        # 检查是否涉及优先公司
        for company in self.priority_companies:
            if company.lower() in text:
                return AlertPriority.P1.value

        return AlertPriority.P2.value

    def _determine_investment_signal(self, data: Dict, data_type: str) -> tuple:
        """
        确定投资信号和行动建议

        Returns:
            (signal, action) tuple
        """
        if data_type == "sec":
            filing_type = data.get("filing_type", "")

            # IPO = 正面信号
            if filing_type in ["S-1", "S-1/A"]:
                return "Positive", "Watch"

            # 融资 = 正面信号
            if filing_type in ["D", "D/A"]:
                return "Positive", "Monitor"

            # 8-K看具体item
            if filing_type in ["8-K", "8-K/A"]:
                items = data.get("8k_items", [])
                for item in items:
                    code = item.get("code", "").lower()
                    if "1.01" in code:  # 收购
                        return "Positive", "Watch"
                    if "1.02" in code:  # 资产处置
                        return "Negative", "Watch"
                    if "5.02" in code:  # 高管变动
                        return "Neutral", "Monitor"

            # 13D激进投资
            if filing_type in ["13D", "SC 13D"]:
                return "Neutral", "Watch"

        elif data_type == "regulatory":
            text = f"{data.get('title', '')} {data.get('summary', '')}".lower()

            # 负面信号关键词
            negative_keywords = ["lawsuit", "investigation", "fine", "penalty", "ban", "charges"]
            for kw in negative_keywords:
                if kw in text:
                    return "Negative", "Immediate"

            # 正面信号关键词
            positive_keywords = ["approval", "cleared", "settled", "dismissed"]
            for kw in positive_keywords:
                if kw in text:
                    return "Positive", "Monitor"

        return "Neutral", "Monitor"

    def _generate_sec_summary(self, filing: Dict) -> str:
        """生成SEC文件摘要"""
        filing_type = filing.get("filing_type", "")
        company = filing.get("company_name", "Unknown")

        if filing_type in ["S-1", "S-1/A"]:
            return f"{company} 提交IPO注册文件，进入上市流程"

        if filing_type in ["D", "D/A"]:
            funding_info = filing.get("funding_info", {})
            amount = funding_info.get("total_sold", "未披露")
            investors = funding_info.get("total_investors", "未披露")
            return f"{company} 私募融资: ${amount}, 投资人数: {investors}"

        if filing_type in ["8-K", "8-K/A"]:
            items = filing.get("8k_items", [])
            if items:
                item_desc = ", ".join([i.get("description", "") for i in items[:2]])
                return f"{company} 8-K重大事件: {item_desc}"
            return f"{company} 提交8-K文件（重大事件）"

        if filing_type in ["13D", "SC 13D"]:
            return f"激进投资者披露持有 {company} 5%以上股份"

        return f"{company} 提交 {filing_type} 文件"

    def _extract_amount(self, filing: Dict) -> Optional[str]:
        """提取融资金额"""
        funding_info = filing.get("funding_info", {})
        total_sold = funding_info.get("total_sold")
        if total_sold:
            try:
                amount = float(total_sold.replace(",", "").replace("$", ""))
                if amount >= 1_000_000_000:
                    return f"${amount/1_000_000_000:.1f}B"
                elif amount >= 1_000_000:
                    return f"${amount/1_000_000:.1f}M"
                else:
                    return f"${amount:,.0f}"
            except (ValueError, AttributeError):
                return total_sold
        return None

    def _extract_company_from_text(self, text: str) -> Optional[str]:
        """从文本中提取公司名"""
        text_lower = text.lower()
        for company in self.priority_companies:
            if company.lower() in text_lower:
                return company
        return None

    def get_alerts_by_priority(self, priority: str) -> List[Alert]:
        """按优先级获取警报"""
        return [a for a in self.alerts if a.priority == priority]

    def get_p0_alerts(self) -> List[Alert]:
        """获取P0警报（需立即处理）"""
        return self.get_alerts_by_priority(AlertPriority.P0.value)

    def get_p1_alerts(self) -> List[Alert]:
        """获取P1警报（1小时内汇总）"""
        return self.get_alerts_by_priority(AlertPriority.P1.value)

    def get_p2_alerts(self) -> List[Alert]:
        """获取P2警报（每日汇总）"""
        return self.get_alerts_by_priority(AlertPriority.P2.value)

    def clear_alerts(self):
        """清空警报"""
        self.alerts = []

    def generate_alert_summary(self) -> str:
        """生成警报汇总"""
        p0 = self.get_p0_alerts()
        p1 = self.get_p1_alerts()
        p2 = self.get_p2_alerts()

        lines = [
            "=" * 60,
            f"警报汇总 | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            f"P0 (立即处理): {len(p0)} 条",
            f"P1 (1小时内): {len(p1)} 条",
            f"P2 (每日汇总): {len(p2)} 条",
            "",
        ]

        if p0:
            lines.append("### P0 警报 (需立即关注) ###")
            for alert in p0:
                lines.append(f"  [{alert.investment_signal}] {alert.title}")
                lines.append(f"    {alert.summary[:100]}...")
                lines.append(f"    行动: {alert.action_required} | 来源: {alert.source}")
                lines.append("")

        if p1:
            lines.append("### P1 警报 (高优先级) ###")
            for alert in p1:
                lines.append(f"  [{alert.investment_signal}] {alert.title}")
                lines.append(f"    {alert.summary[:80]}...")
                lines.append("")

        if p2:
            lines.append(f"### P2 警报 ({len(p2)}条，详见每日报告) ###")
            for alert in p2[:3]:  # 只显示前3条
                lines.append(f"  - {alert.title[:60]}")
            if len(p2) > 3:
                lines.append(f"  ... 还有 {len(p2)-3} 条")

        return "\n".join(lines)

    def export_alerts_json(self, filepath: str):
        """导出警报为JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "p0_count": len(self.get_p0_alerts()),
                "p1_count": len(self.get_p1_alerts()),
                "p2_count": len(self.get_p2_alerts()),
                "total": len(self.alerts)
            },
            "alerts": [a.to_dict() for a in self.alerts]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"警报已导出: {filepath}")


def test_alert_system():
    """测试警报系统"""
    print("=" * 60)
    print("警报系统测试")
    print("=" * 60)

    system = AlertSystem()

    # 测试SEC文件
    test_filings = [
        {
            "filing_type": "S-1",
            "company_name": "OpenAI Inc",
            "link": "https://sec.gov/test/s1",
            "published": "2026-02-04 10:00"
        },
        {
            "filing_type": "D",
            "company_name": "Anthropic PBC",
            "link": "https://sec.gov/test/d",
            "published": "2026-02-04 09:00",
            "funding_info": {
                "total_sold": "500000000",
                "total_investors": "15"
            }
        },
        {
            "filing_type": "8-K",
            "company_name": "NVIDIA Corp",
            "link": "https://sec.gov/test/8k",
            "published": "2026-02-04 08:00",
            "8k_items": [
                {"code": "item 1.01", "description": "收购/合并"}
            ]
        }
    ]

    print("\n处理SEC文件...")
    for filing in test_filings:
        system.process_sec_filing(filing)

    # 测试监管新闻
    test_news = [
        {
            "title": "FTC Launches Antitrust Investigation into OpenAI",
            "summary": "Federal Trade Commission announces investigation into potential anticompetitive practices",
            "source": "FTC",
            "agency": "Federal Trade Commission",
            "link": "https://ftc.gov/test"
        },
        {
            "title": "DOJ Clears Microsoft-Activision Deal",
            "summary": "Department of Justice approves merger after remedies",
            "source": "DOJ",
            "agency": "Department of Justice",
            "link": "https://doj.gov/test"
        }
    ]

    print("\n处理监管新闻...")
    for news in test_news:
        system.process_regulatory_news(news)

    # 输出汇总
    print("\n" + system.generate_alert_summary())

    # 统计
    print(f"\n总计: {len(system.alerts)} 条警报")
    print(f"  P0: {len(system.get_p0_alerts())}")
    print(f"  P1: {len(system.get_p1_alerts())}")
    print(f"  P2: {len(system.get_p2_alerts())}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_alert_system()
