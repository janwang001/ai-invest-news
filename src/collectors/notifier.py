#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知推送系统

支持多种通知渠道:
- 控制台输出（默认）
- 文件记录
- Webhook (可扩展到Slack, 企业微信, 钉钉)
- 邮件（需配置SMTP）

优先级策略:
- P0: 立即推送所有渠道
- P1: 每小时汇总推送
- P2: 每日汇总（仅文件记录）
"""

import ipaddress
import logging
import json
import os
import socket
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    """通知消息"""
    priority: str          # P0/P1/P2
    title: str
    message: str
    source: str           # sec/regulatory/blog/stock
    timestamp: str
    url: Optional[str] = None
    signal: Optional[str] = None  # Positive/Negative/Neutral
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class NotificationChannel(ABC):
    """通知渠道基类"""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """发送通知"""
        pass

    @abstractmethod
    def send_batch(self, notifications: List[Notification]) -> bool:
        """批量发送"""
        pass


class ConsoleChannel(NotificationChannel):
    """控制台输出渠道"""

    def __init__(self, colored: bool = True):
        self.colored = colored

    def send(self, notification: Notification) -> bool:
        """发送单条通知"""
        output = self._format(notification)
        print(output)
        return True

    def send_batch(self, notifications: List[Notification]) -> bool:
        """批量发送"""
        if not notifications:
            return True

        print("\n" + "=" * 60)
        print(f"📬 通知汇总 ({len(notifications)}条) | {datetime.now().strftime('%H:%M')}")
        print("=" * 60)

        for notif in notifications:
            print(self._format(notif))
            print("-" * 40)

        return True

    def _format(self, notification: Notification) -> str:
        """格式化通知"""
        # 优先级图标
        priority_icons = {"P0": "🚨", "P1": "⚠️", "P2": "ℹ️"}
        icon = priority_icons.get(notification.priority, "📌")

        # 信号图标
        signal_icons = {"Positive": "📈", "Negative": "📉", "Neutral": "➡️"}
        signal_icon = signal_icons.get(notification.signal, "")

        lines = [
            f"{icon} [{notification.priority}] {notification.title}",
            f"   {notification.message[:200]}",
            f"   来源: {notification.source} | 时间: {notification.timestamp}",
        ]

        if signal_icon:
            lines[0] += f" {signal_icon}"

        if notification.url:
            lines.append(f"   链接: {notification.url}")

        return "\n".join(lines)


class FileChannel(NotificationChannel):
    """文件记录渠道"""

    def __init__(self, output_dir: str = "output/alerts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def send(self, notification: Notification) -> bool:
        """写入单条通知"""
        return self.send_batch([notification])

    def send_batch(self, notifications: List[Notification]) -> bool:
        """批量写入"""
        if not notifications:
            return True

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = os.path.join(self.output_dir, f"alerts_{date_str}.json")

        # 读取现有数据
        existing = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []

        # 追加新通知
        for notif in notifications:
            existing.append(notif.to_dict())

        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            logger.info(f"警报已写入: {filepath}")
            return True
        except IOError as e:
            logger.error(f"写入文件失败: {e}")
            return False


class WebhookChannel(NotificationChannel):
    """Webhook推送渠道（Slack, 企业微信, 钉钉等）"""

    # 允许的 webhook 域名白名单
    ALLOWED_WEBHOOK_DOMAINS = {
        'hooks.slack.com',
        'oapi.dingtalk.com',
        'qyapi.weixin.qq.com',
        'discord.com',
        'discordapp.com',
    }

    def __init__(self, webhook_url: str, platform: str = "generic"):
        """
        Args:
            webhook_url: Webhook URL
            platform: 平台类型 (slack/wecom/dingtalk/generic)

        Raises:
            ValueError: 如果 webhook URL 不安全
        """
        is_safe, reason = self._validate_webhook_url(webhook_url)
        if not is_safe:
            raise ValueError(f"不安全的 webhook URL: {reason}")

        self.webhook_url = webhook_url
        self.platform = platform

    def _validate_webhook_url(self, url: str) -> tuple:
        """
        验证 webhook URL 安全性（SSRF 防护）

        Args:
            url: webhook URL

        Returns:
            (is_safe, reason) 元组
        """
        try:
            parsed = urlparse(url)

            # 1. 只允许 https 协议（webhook 应该使用 https）
            if parsed.scheme != 'https':
                return False, f"Webhook 必须使用 HTTPS 协议，当前: {parsed.scheme}"

            hostname = parsed.hostname
            if not hostname:
                return False, "缺少主机名"

            hostname_lower = hostname.lower()

            # 2. 检查是否在白名单中
            if hostname_lower in self.ALLOWED_WEBHOOK_DOMAINS:
                return True, "域名在白名单中"

            # 3. 检查是否是白名单域名的子域名
            for allowed_domain in self.ALLOWED_WEBHOOK_DOMAINS:
                if hostname_lower.endswith('.' + allowed_domain):
                    return True, "子域名在白名单中"

            # 4. 对于不在白名单中的域名，进行安全检查
            # 禁止私有/内部地址
            blocked_suffixes = ('.local', '.internal', '.lan', '.localdomain')
            if hostname_lower.endswith(blocked_suffixes):
                return False, f"禁止的内部域名后缀: {hostname}"

            blocked_hostnames = {'localhost', 'internal', 'metadata'}
            if hostname_lower in blocked_hostnames:
                return False, f"禁止的主机名: {hostname}"

            # 5. 检查 IP 地址
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False, f"禁止的私有/内部 IP: {ip}"
            except ValueError:
                # 是域名，检查 DNS 解析结果
                try:
                    resolved_ips = socket.gethostbyname_ex(hostname)[2]
                    for ip_str in resolved_ips:
                        ip = ipaddress.ip_address(ip_str)
                        if ip.is_private or ip.is_loopback or ip.is_link_local:
                            return False, f"域名解析到私有 IP: {ip_str}"
                except socket.gaierror:
                    pass  # DNS 解析失败，允许继续

            # 非白名单域名，发出警告但允许使用
            logger.warning(f"Webhook 域名 '{hostname}' 不在白名单中，请确保其安全性")
            return True, "通过安全检查（非白名单域名）"

        except Exception as e:
            return False, f"URL 验证失败: {e}"

    def send(self, notification: Notification) -> bool:
        """发送单条通知"""
        payload = self._build_payload(notification)
        return self._post(payload)

    def send_batch(self, notifications: List[Notification]) -> bool:
        """批量发送（合并为一条消息）"""
        if not notifications:
            return True

        # 构建汇总消息
        summary = self._build_batch_payload(notifications)
        return self._post(summary)

    def _build_payload(self, notification: Notification) -> Dict:
        """构建请求payload"""
        if self.platform == "slack":
            return {
                "text": f"*[{notification.priority}] {notification.title}*",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*[{notification.priority}] {notification.title}*\n{notification.message}"
                        }
                    }
                ]
            }

        elif self.platform == "wecom":  # 企业微信
            return {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### [{notification.priority}] {notification.title}\n{notification.message}\n> 来源: {notification.source}"
                }
            }

        elif self.platform == "dingtalk":  # 钉钉
            return {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"[{notification.priority}] {notification.title}",
                    "text": f"### [{notification.priority}] {notification.title}\n{notification.message}"
                }
            }

        else:  # generic
            return {
                "priority": notification.priority,
                "title": notification.title,
                "message": notification.message,
                "source": notification.source,
                "timestamp": notification.timestamp,
                "url": notification.url
            }

    def _build_batch_payload(self, notifications: List[Notification]) -> Dict:
        """构建批量消息payload"""
        p0_count = sum(1 for n in notifications if n.priority == "P0")
        p1_count = sum(1 for n in notifications if n.priority == "P1")

        summary_lines = [f"📬 警报汇总 ({len(notifications)}条)"]
        summary_lines.append(f"P0: {p0_count} | P1: {p1_count}")
        summary_lines.append("-" * 30)

        for notif in notifications[:5]:  # 最多显示5条
            summary_lines.append(f"• [{notif.priority}] {notif.title}")

        if len(notifications) > 5:
            summary_lines.append(f"... 还有 {len(notifications) - 5} 条")

        message = "\n".join(summary_lines)

        if self.platform in ["slack", "wecom", "dingtalk"]:
            return self._build_payload(Notification(
                priority="汇总",
                title=f"警报汇总 ({len(notifications)}条)",
                message=message,
                source="monitor",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
        else:
            return {"notifications": [n.to_dict() for n in notifications]}

    def _post(self, payload: Dict) -> bool:
        """发送HTTP POST"""
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Webhook推送成功: {self.platform}")
            return True
        except Exception as e:
            logger.error(f"Webhook推送失败: {e}")
            return False


class Notifier:
    """通知管理器"""

    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.pending_p1: List[Notification] = []
        self.pending_p2: List[Notification] = []

        # 默认启用控制台
        self.add_channel(ConsoleChannel())

    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.channels.append(channel)

    def add_webhook(self, webhook_url: str, platform: str = "generic"):
        """添加Webhook渠道"""
        self.add_channel(WebhookChannel(webhook_url, platform))

    def add_file_channel(self, output_dir: str = "output/alerts"):
        """添加文件记录渠道"""
        self.add_channel(FileChannel(output_dir))

    def notify(self, notification: Notification):
        """
        发送通知（根据优先级处理）

        P0: 立即推送
        P1: 加入队列，等待汇总
        P2: 仅记录
        """
        if notification.priority == "P0":
            self._send_immediate(notification)
        elif notification.priority == "P1":
            self.pending_p1.append(notification)
        else:
            self.pending_p2.append(notification)

    def notify_from_alert(self, alert) -> Notification:
        """从Alert对象创建通知"""
        notification = Notification(
            priority=alert.priority,
            title=alert.title,
            message=alert.summary,
            source=alert.source,
            timestamp=alert.timestamp,
            url=alert.url,
            signal=alert.investment_signal,
            metadata={"alert_type": alert.alert_type}
        )
        self.notify(notification)
        return notification

    def notify_from_blog(self, blog_post: Dict) -> Notification:
        """从博客文章创建通知"""
        notification = Notification(
            priority=blog_post.get("priority", "P2"),
            title=f"[{blog_post.get('company')}] {blog_post.get('title', '')}",
            message=blog_post.get("summary", "")[:300],
            source=blog_post.get("source", "Blog"),
            timestamp=blog_post.get("published", datetime.now().strftime("%Y-%m-%d %H:%M")),
            url=blog_post.get("link"),
            signal=blog_post.get("investment_signal"),
            metadata={"content_type": blog_post.get("content_type")}
        )
        self.notify(notification)
        return notification

    def notify_from_stock(self, stock_alert) -> Notification:
        """从股票警报创建通知"""
        notification = Notification(
            priority=stock_alert.priority,
            title=f"[{stock_alert.symbol}] {stock_alert.company} {stock_alert.change_pct:+.1f}%",
            message=f"价格: ${stock_alert.current_price:.2f} | {stock_alert.alert_reason}",
            source="Stock",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            signal=stock_alert.signal,
            metadata={
                "symbol": stock_alert.symbol,
                "category": stock_alert.category,
                "volume_ratio": stock_alert.volume_ratio
            }
        )
        self.notify(notification)
        return notification

    def _send_immediate(self, notification: Notification):
        """立即发送到所有渠道"""
        for channel in self.channels:
            try:
                channel.send(notification)
            except Exception as e:
                logger.error(f"发送通知失败 ({type(channel).__name__}): {e}")

    def flush_p1(self):
        """汇总发送P1通知"""
        if not self.pending_p1:
            return

        logger.info(f"汇总发送 {len(self.pending_p1)} 条P1通知")

        for channel in self.channels:
            try:
                channel.send_batch(self.pending_p1)
            except Exception as e:
                logger.error(f"批量发送失败 ({type(channel).__name__}): {e}")

        self.pending_p1 = []

    def flush_p2(self):
        """汇总发送P2通知（仅文件）"""
        if not self.pending_p2:
            return

        logger.info(f"记录 {len(self.pending_p2)} 条P2通知")

        for channel in self.channels:
            if isinstance(channel, FileChannel):
                try:
                    channel.send_batch(self.pending_p2)
                except Exception as e:
                    logger.error(f"写入文件失败: {e}")

        self.pending_p2 = []

    def flush_all(self):
        """发送所有待处理通知"""
        self.flush_p1()
        self.flush_p2()

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "channels": len(self.channels),
            "pending_p1": len(self.pending_p1),
            "pending_p2": len(self.pending_p2),
        }


def test_notifier():
    """测试通知系统"""
    print("=" * 60)
    print("通知系统测试")
    print("=" * 60)

    notifier = Notifier()

    # 添加文件渠道
    notifier.add_file_channel("/tmp/test_alerts")

    # 测试P0通知（立即推送）
    print("\n测试1: P0通知（立即推送）")
    p0_notif = Notification(
        priority="P0",
        title="OpenAI提交IPO注册文件",
        message="OpenAI Inc向SEC提交S-1文件，正式启动IPO流程",
        source="SEC EDGAR",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        url="https://sec.gov/openai",
        signal="Positive"
    )
    notifier.notify(p0_notif)

    # 测试P1通知（加入队列）
    print("\n测试2: P1通知（加入队列）")
    for i in range(3):
        p1_notif = Notification(
            priority="P1",
            title=f"测试P1通知 #{i+1}",
            message=f"这是第{i+1}条P1测试通知",
            source="Test",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            signal="Neutral"
        )
        notifier.notify(p1_notif)

    print(f"  队列中有 {len(notifier.pending_p1)} 条P1通知")

    # 测试汇总发送
    print("\n测试3: 汇总发送P1")
    notifier.flush_p1()

    # 测试P2（仅文件记录）
    print("\n测试4: P2通知（仅文件记录）")
    p2_notif = Notification(
        priority="P2",
        title="普通监控信息",
        message="这是一条普通的P2通知，仅记录到文件",
        source="Test",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    notifier.notify(p2_notif)
    notifier.flush_p2()

    # 统计
    print("\n统计:")
    stats = notifier.get_stats()
    print(f"  渠道数: {stats['channels']}")
    print(f"  待处理P1: {stats['pending_p1']}")
    print(f"  待处理P2: {stats['pending_p2']}")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_notifier()
