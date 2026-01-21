# -*- coding: utf-8 -*-
"""
文章抓取模块

使用 readability-lxml 实现文章正文抽取
设计目标：稳定、干净、控制长度、失败可跳过
"""
import hashlib
import json
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Optional

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
    """

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

    def fetch(self, url: str, save_to_disk: bool = True) -> ArticleResult:
        """
        抓取单篇文章

        :param url: 文章 URL
        :param save_to_disk: 是否保存到本地磁盘
        :return: ArticleResult 对象
        """
        start_time = time.time()
        result = ArticleResult(url=url, success=False)

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
