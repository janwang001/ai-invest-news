# -*- coding: utf-8 -*-
"""
文章抓取模块

使用 readability-lxml 实现文章正文抽取
设计目标：稳定、干净、控制长度、失败可跳过
"""
import hashlib
import ipaddress
import json
import socket
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

from .fetch_config import (
    DATE_FORMAT,
    DEFAULT_HEADERS,
    MAX_ARTICLE_CHARS,
    MAX_RETRIES,
    MIN_LINE_LENGTH,
    NOISE_KEYWORDS,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    get_daily_data_dir,
    url_to_filename,
)


@dataclass
class ArticleResult:
    """
    文章抓取结果

    包含抓取的文本内容和统计信息
    """
    url: str
    success: bool
    content: Optional[str] = None
    title: Optional[str] = None
    file_path: Optional[str] = None

    # 统计信息
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "url": self.url,
            "success": self.success,
            "content": self.content,
            "title": self.title,
            "file_path": self.file_path,
            "stats": self.stats,
        }


class ArticleFetcher:
    """
    文章抓取器

    使用 readability-lxml 提取文章正文，支持：
    - 自动清洗噪声内容
    - 控制输出长度
    - 本地文件存储
    - 抓取统计信息
    - SSRF 防护
    """

    # 禁止访问的主机名（内网/元数据服务）
    BLOCKED_HOSTNAMES = {
        'localhost', 'internal', 'metadata', 'metadata.google.internal',
        '169.254.169.254',  # AWS/GCP metadata
        'kubernetes.default', 'kubernetes.default.svc',
    }

    # 禁止访问的主机名后缀
    BLOCKED_HOSTNAME_SUFFIXES = (
        '.local', '.internal', '.lan', '.localdomain',
        '.kubernetes.default.svc.cluster.local',
    )

    def __init__(
        self,
        timeout: int = REQUEST_TIMEOUT,
        max_chars: int = MAX_ARTICLE_CHARS,
        headers: Optional[dict] = None,
    ):
        """
        初始化抓取器

        :param timeout: 请求超时时间（秒）
        :param max_chars: 最大保留字符数
        :param headers: 自定义请求头
        """
        self.timeout = timeout
        self.max_chars = max_chars
        self.headers = headers or DEFAULT_HEADERS

    def _is_safe_url(self, url: str) -> tuple[bool, str]:
        """
        验证 URL 是否安全（SSRF 防护）

        :param url: 要验证的 URL
        :return: (is_safe, reason) 元组
        """
        try:
            parsed = urlparse(url)

            # 1. 只允许 http/https 协议
            if parsed.scheme not in ('http', 'https'):
                return False, f"不允许的协议: {parsed.scheme}"

            # 2. 必须有主机名
            hostname = parsed.hostname
            if not hostname:
                return False, "缺少主机名"

            # 3. 检查被禁止的主机名
            hostname_lower = hostname.lower()
            if hostname_lower in self.BLOCKED_HOSTNAMES:
                return False, f"被禁止的主机名: {hostname}"

            # 4. 检查被禁止的主机名后缀
            if hostname_lower.endswith(self.BLOCKED_HOSTNAME_SUFFIXES):
                return False, f"被禁止的主机名后缀: {hostname}"

            # 5. 检查 IP 地址
            try:
                # 尝试解析为 IP 地址
                ip = ipaddress.ip_address(hostname)
                # 禁止私有/保留/回环/链路本地地址
                if ip.is_private:
                    return False, f"私有 IP 地址: {ip}"
                if ip.is_reserved:
                    return False, f"保留 IP 地址: {ip}"
                if ip.is_loopback:
                    return False, f"回环地址: {ip}"
                if ip.is_link_local:
                    return False, f"链路本地地址: {ip}"
            except ValueError:
                # 不是 IP 地址，是域名，进行 DNS 解析检查
                try:
                    resolved_ips = socket.gethostbyname_ex(hostname)[2]
                    for ip_str in resolved_ips:
                        ip = ipaddress.ip_address(ip_str)
                        if ip.is_private or ip.is_loopback or ip.is_link_local:
                            return False, f"域名解析到私有/内部 IP: {ip_str}"
                except socket.gaierror:
                    # DNS 解析失败，允许继续（可能是网络问题）
                    pass

            return True, "URL 安全"

        except Exception as e:
            return False, f"URL 验证失败: {e}"

    def fetch(self, url: str, save_to_disk: bool = True) -> ArticleResult:
        """
        抓取单篇文章

        :param url: 文章 URL
        :param save_to_disk: 是否保存到本地磁盘
        :return: ArticleResult 对象
        """
        start_time = time.time()
        result = ArticleResult(url=url, success=False)

        # SSRF 防护：验证 URL 安全性
        is_safe, reason = self._is_safe_url(url)
        if not is_safe:
            result.stats["error"] = f"URL 安全检查失败: {reason}"
            return result

        try:
            # 发起请求
            resp = self._request_with_retry(url)
            if resp is None:
                result.stats["error"] = "request_failed"
                return result

            # 记录原始 HTML 大小
            raw_html_size = len(resp.text)

            # 使用 readability 提取正文
            doc = Document(resp.text)
            result.title = doc.title()
            html_content = doc.summary(html_partial=True)

            # 转换为纯文本
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text(separator="\n")

            # 清洗文本
            cleaned_text = self._clean(text)

            # 截断到最大长度
            final_text = cleaned_text[:self.max_chars]

            # 填充结果
            result.success = True
            result.content = final_text

            # 统计信息
            result.stats = {
                "raw_html_size": raw_html_size,
                "extracted_text_length": len(text),
                "cleaned_text_length": len(cleaned_text),
                "final_text_length": len(final_text),
                "truncated": len(cleaned_text) > self.max_chars,
                "fetch_time_ms": int((time.time() - start_time) * 1000),
                "title": result.title,
            }

            # 保存到磁盘
            if save_to_disk and result.success:
                result.file_path = self._save_to_disk(url, result)

        except Exception as e:
            result.stats["error"] = str(e)
            result.stats["fetch_time_ms"] = int((time.time() - start_time) * 1000)

        return result

    def fetch_batch(
        self,
        urls: list[str],
        save_to_disk: bool = True,
    ) -> list[ArticleResult]:
        """
        批量抓取文章

        :param urls: URL 列表
        :param save_to_disk: 是否保存到本地磁盘
        :return: ArticleResult 列表
        """
        results = []
        for url in urls:
            result = self.fetch(url, save_to_disk=save_to_disk)
            results.append(result)
            # 简单的请求间隔，避免被封
            time.sleep(0.5)
        return results

    def _request_with_retry(self, url: str) -> Optional[requests.Response]:
        """
        带重试的请求

        :param url: 请求 URL
        :return: Response 对象或 None
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url,
                    timeout=self.timeout,
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    return resp

                # 非 200 状态码，可能需要重试
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

            except requests.RequestException:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        return None

    def _clean(self, text: str) -> str:
        """
        清洗文本

        - 过滤过短的行
        - 过滤包含噪声关键词的行

        :param text: 原始文本
        :return: 清洗后的文本
        """
        lines = []
        for line in text.splitlines():
            line = line.strip()

            # 过滤过短的行
            if len(line) < MIN_LINE_LENGTH:
                continue

            # 过滤噪声关键词
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in NOISE_KEYWORDS):
                continue

            lines.append(line)

        return "\n".join(lines)

    def _save_to_disk(self, url: str, result: ArticleResult) -> str:
        """
        保存抓取结果到本地磁盘

        :param url: 文章 URL
        :param result: 抓取结果
        :return: 保存的文件路径
        """
        # 获取今日数据目录
        today_str = datetime.now().strftime(DATE_FORMAT)
        daily_dir = get_daily_data_dir(today_str)

        # 生成文件名
        filename = url_to_filename(url)
        file_path = daily_dir / filename

        # 构建保存内容（包含元信息）
        save_data = {
            "url": url,
            "title": result.title,
            "content": result.content,
            "stats": result.stats,
            "fetched_at": datetime.now().isoformat(),
        }

        # 覆盖写入
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        return str(file_path)


def fetch_article(url: str, save_to_disk: bool = True) -> ArticleResult:
    """
    便捷函数：抓取单篇文章

    :param url: 文章 URL
    :param save_to_disk: 是否保存到本地磁盘
    :return: ArticleResult 对象
    """
    fetcher = ArticleFetcher()
    return fetcher.fetch(url, save_to_disk=save_to_disk)


if __name__ == "__main__":
    # 简单测试
    test_url = "https://techcrunch.com/2024/01/15/example-article/"
    result = fetch_article(test_url)
    print(f"Success: {result.success}")
    print(f"Title: {result.title}")
    print(f"Stats: {result.stats}")
    if result.content:
        print(f"Content preview: {result.content[:200]}...")
