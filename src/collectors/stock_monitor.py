#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股价异动监控

使用免费数据源监控AI相关股票的异常波动:
- 日内涨跌幅 >5% 触发P0
- 日内涨跌幅 >3% 触发P1
- 成交量异常 >2x平均 额外提升优先级

数据源: Yahoo Finance (yfinance)

监控标的:
- AI芯片: NVDA, AMD, INTC, TSM
- 云厂商: MSFT, GOOGL, AMZN, META
- AI概念: PLTR, AI (C3.ai), PATH, SNOW
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 尝试导入yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance未安装，股价监控将使用模拟数据")


@dataclass
class StockAlert:
    """股票警报"""
    symbol: str
    company: str
    category: str  # chip, cloud, ai_concept
    current_price: float
    prev_close: float
    change_pct: float
    volume: int
    avg_volume: int
    volume_ratio: float
    priority: str  # P0/P1/P2
    signal: str    # Positive/Negative
    alert_reason: str


class StockMonitor:
    """股价异动监控器"""

    def __init__(self):
        # 监控股票列表
        self.watchlist = {
            # AI芯片
            "NVDA": {"name": "NVIDIA", "category": "chip", "importance": "high"},
            "AMD": {"name": "AMD", "category": "chip", "importance": "medium"},
            "INTC": {"name": "Intel", "category": "chip", "importance": "medium"},
            "TSM": {"name": "TSMC", "category": "chip", "importance": "high"},
            "AVGO": {"name": "Broadcom", "category": "chip", "importance": "medium"},

            # 云厂商/AI巨头
            "MSFT": {"name": "Microsoft", "category": "cloud", "importance": "high"},
            "GOOGL": {"name": "Alphabet", "category": "cloud", "importance": "high"},
            "AMZN": {"name": "Amazon", "category": "cloud", "importance": "high"},
            "META": {"name": "Meta", "category": "cloud", "importance": "high"},

            # AI概念股
            "PLTR": {"name": "Palantir", "category": "ai_concept", "importance": "medium"},
            "AI": {"name": "C3.ai", "category": "ai_concept", "importance": "low"},
            "PATH": {"name": "UiPath", "category": "ai_concept", "importance": "low"},
            "SNOW": {"name": "Snowflake", "category": "ai_concept", "importance": "medium"},
            "MDB": {"name": "MongoDB", "category": "ai_concept", "importance": "medium"},
            "CRM": {"name": "Salesforce", "category": "ai_concept", "importance": "medium"},
        }

        # 触发阈值
        self.thresholds = {
            "p0_change_pct": 5.0,   # 5%涨跌触发P0
            "p1_change_pct": 3.0,   # 3%涨跌触发P1
            "volume_alert": 2.0,    # 2倍平均成交量
            "high_importance_boost": 1.0,  # 高重要性股票阈值降低
        }

    def check_all_stocks(self, test_mode: bool = False) -> List[StockAlert]:
        """
        检查所有监控股票

        Args:
            test_mode: 是否使用测试数据

        Returns:
            股票警报列表
        """
        if test_mode or not YFINANCE_AVAILABLE:
            logger.info("使用股票测试数据")
            return self._generate_test_alerts()

        alerts = []
        symbols = list(self.watchlist.keys())

        logger.info(f"检查 {len(symbols)} 只股票...")

        try:
            # 批量获取数据
            tickers = yf.Tickers(" ".join(symbols))

            for symbol in symbols:
                try:
                    alert = self._check_single_stock(symbol, tickers.tickers[symbol])
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    logger.debug(f"检查 {symbol} 失败: {e}")

        except Exception as e:
            logger.error(f"批量获取股票数据失败: {e}")
            return self._generate_test_alerts()

        # 按优先级排序
        alerts.sort(key=lambda x: (
            0 if x.priority == "P0" else 1 if x.priority == "P1" else 2,
            -abs(x.change_pct)
        ))

        logger.info(f"发现 {len(alerts)} 个股票异动")
        return alerts

    def _check_single_stock(self, symbol: str, ticker) -> Optional[StockAlert]:
        """检查单只股票"""
        info = self.watchlist.get(symbol, {})

        try:
            # 获取当前数据
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 2:
                return None

            current = hist.iloc[-1]
            prev = hist.iloc[-2]

            current_price = current['Close']
            prev_close = prev['Close']
            change_pct = ((current_price - prev_close) / prev_close) * 100

            volume = int(current['Volume'])
            avg_volume = int(hist['Volume'].mean())
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

            # 判断是否触发警报
            alert = self._evaluate_alert(
                symbol, info, current_price, prev_close,
                change_pct, volume, avg_volume, volume_ratio
            )

            return alert

        except Exception as e:
            logger.debug(f"处理 {symbol} 数据失败: {e}")
            return None

    def _evaluate_alert(
        self, symbol: str, info: Dict,
        current_price: float, prev_close: float,
        change_pct: float, volume: int, avg_volume: int, volume_ratio: float
    ) -> Optional[StockAlert]:
        """评估是否触发警报"""

        # 根据重要性调整阈值
        importance = info.get("importance", "medium")
        threshold_adjust = 0
        if importance == "high":
            threshold_adjust = -self.thresholds["high_importance_boost"]

        p0_threshold = self.thresholds["p0_change_pct"] + threshold_adjust
        p1_threshold = self.thresholds["p1_change_pct"] + threshold_adjust

        abs_change = abs(change_pct)

        # 确定优先级
        priority = None
        alert_reasons = []

        if abs_change >= p0_threshold:
            priority = "P0"
            alert_reasons.append(f"涨跌幅{change_pct:+.1f}%")
        elif abs_change >= p1_threshold:
            priority = "P1"
            alert_reasons.append(f"涨跌幅{change_pct:+.1f}%")

        # 成交量异常提升优先级
        if volume_ratio >= self.thresholds["volume_alert"]:
            alert_reasons.append(f"成交量{volume_ratio:.1f}x")
            if priority == "P1":
                priority = "P0"
            elif priority is None:
                priority = "P2"

        if priority is None:
            return None

        # 确定信号方向
        signal = "Positive" if change_pct > 0 else "Negative"

        return StockAlert(
            symbol=symbol,
            company=info.get("name", symbol),
            category=info.get("category", "unknown"),
            current_price=current_price,
            prev_close=prev_close,
            change_pct=change_pct,
            volume=volume,
            avg_volume=avg_volume,
            volume_ratio=volume_ratio,
            priority=priority,
            signal=signal,
            alert_reason=" + ".join(alert_reasons)
        )

    def _generate_test_alerts(self) -> List[StockAlert]:
        """生成测试数据"""
        return [
            StockAlert(
                symbol="NVDA",
                company="NVIDIA",
                category="chip",
                current_price=875.50,
                prev_close=820.00,
                change_pct=6.77,
                volume=85000000,
                avg_volume=45000000,
                volume_ratio=1.89,
                priority="P0",
                signal="Positive",
                alert_reason="涨跌幅+6.8%"
            ),
            StockAlert(
                symbol="MSFT",
                company="Microsoft",
                category="cloud",
                current_price=415.20,
                prev_close=425.00,
                change_pct=-2.31,
                volume=35000000,
                avg_volume=22000000,
                volume_ratio=1.59,
                priority="P1",
                signal="Negative",
                alert_reason="涨跌幅-2.3%"
            ),
            StockAlert(
                symbol="PLTR",
                company="Palantir",
                category="ai_concept",
                current_price=24.50,
                prev_close=22.00,
                change_pct=11.36,
                volume=120000000,
                avg_volume=50000000,
                volume_ratio=2.40,
                priority="P0",
                signal="Positive",
                alert_reason="涨跌幅+11.4% + 成交量2.4x"
            ),
        ]

    def format_alert(self, alert: StockAlert) -> str:
        """格式化警报输出"""
        emoji = "📈" if alert.signal == "Positive" else "📉"
        return (
            f"{emoji} [{alert.priority}] {alert.symbol} ({alert.company})\n"
            f"   价格: ${alert.current_price:.2f} ({alert.change_pct:+.1f}%)\n"
            f"   成交量: {alert.volume:,} ({alert.volume_ratio:.1f}x平均)\n"
            f"   原因: {alert.alert_reason}"
        )

    def generate_summary(self, alerts: List[StockAlert]) -> str:
        """生成警报汇总"""
        if not alerts:
            return "股票市场: 无异动"

        lines = [
            "=" * 50,
            f"股票异动监控 | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 50,
        ]

        # 按类别分组
        by_category = {}
        for alert in alerts:
            cat = alert.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(alert)

        category_names = {
            "chip": "AI芯片",
            "cloud": "云厂商",
            "ai_concept": "AI概念股"
        }

        for cat, cat_alerts in by_category.items():
            lines.append(f"\n### {category_names.get(cat, cat)}")
            for alert in cat_alerts:
                lines.append(self.format_alert(alert))

        # 统计
        p0_count = sum(1 for a in alerts if a.priority == "P0")
        p1_count = sum(1 for a in alerts if a.priority == "P1")

        lines.extend([
            "",
            f"统计: P0={p0_count}, P1={p1_count}, 总计={len(alerts)}"
        ])

        return "\n".join(lines)


def test_stock_monitor():
    """测试股价监控器"""
    print("=" * 60)
    print("股价异动监控器测试")
    print("=" * 60)

    monitor = StockMonitor()

    # 测试模式
    print("\n测试1: 测试数据")
    alerts = monitor.check_all_stocks(test_mode=True)
    print(f"  生成 {len(alerts)} 个测试警报")

    for alert in alerts:
        print(f"\n{monitor.format_alert(alert)}")

    # 汇总
    print("\n" + monitor.generate_summary(alerts))

    # 真实数据（如果yfinance可用）
    if YFINANCE_AVAILABLE:
        print("\n测试2: 真实数据（可能无异动）")
        real_alerts = monitor.check_all_stocks(test_mode=False)
        print(f"  检测到 {len(real_alerts)} 个真实异动")

        if real_alerts:
            for alert in real_alerts[:3]:
                print(f"\n{monitor.format_alert(alert)}")
    else:
        print("\n测试2: yfinance未安装，跳过真实数据测试")
        print("  安装: pip install yfinance")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_stock_monitor()
