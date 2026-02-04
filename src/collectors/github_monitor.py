#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub爆款项目监控

监控AI相关的爆款开源项目:
- Star增速 >1000/天
- 来自顶级组织 (OpenAI, Meta, Google, Microsoft等)
- Fork/Star比 >0.3（高实用性）

爆款项目 = 技术趋势信号
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """GitHub爆款项目监控器"""

    def __init__(self):
        # GitHub API基础URL
        self.api_base = "https://api.github.com"

        # 重点关注的组织
        self.priority_orgs = [
            "openai", "anthropics", "google", "meta", "microsoft",
            "huggingface", "langchain-ai", "deepmind", "stability-ai",
            "mistralai", "ollama", "ggerganov",
        ]

        # AI相关关键词
        self.ai_keywords = [
            "llm", "gpt", "transformer", "diffusion", "ai", "ml",
            "neural", "deep-learning", "machine-learning",
            "chatbot", "agent", "rag", "embedding", "vector",
            "llama", "mistral", "claude", "gemini",
        ]

        # 爆款阈值
        self.thresholds = {
            "stars_per_day": 500,      # 日增Star数
            "min_stars": 1000,          # 最小Star数
            "min_fork_ratio": 0.2,      # Fork/Star比
            "trending_days": 7,         # 趋势计算天数
        }

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Investment-Monitor/1.0",
        }

        # 如果有GitHub Token，添加到headers
        # self.headers["Authorization"] = f"token {os.environ.get('GITHUB_TOKEN', '')}"

    def search_trending_repos(self, days: int = 7, min_stars: int = 1000) -> List[Dict]:
        """
        搜索趋势项目

        Args:
            days: 时间范围
            min_stars: 最小Star数

        Returns:
            项目列表
        """
        try:
            # 计算日期范围
            since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # 构建搜索查询
            # 搜索AI相关的高Star项目
            queries = [
                f"stars:>{min_stars} created:>{since_date} language:python topic:llm",
                f"stars:>{min_stars} created:>{since_date} topic:machine-learning",
                f"stars:>{min_stars} pushed:>{since_date} topic:artificial-intelligence",
            ]

            all_repos = []
            seen_ids = set()

            for query in queries:
                try:
                    url = f"{self.api_base}/search/repositories"
                    params = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 30,
                    }

                    response = requests.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=15
                    )

                    if response.status_code == 403:
                        logger.warning("GitHub API速率限制")
                        break

                    response.raise_for_status()
                    data = response.json()

                    for repo in data.get("items", []):
                        if repo["id"] not in seen_ids:
                            seen_ids.add(repo["id"])
                            processed = self._process_repo(repo)
                            if processed:
                                all_repos.append(processed)

                    time.sleep(2)  # API速率限制

                except Exception as e:
                    logger.warning(f"搜索查询失败: {e}")
                    continue

            # 按优先级排序
            all_repos.sort(
                key=lambda x: (
                    0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                    -x["stars"]
                )
            )

            logger.info(f"GitHub: 发现 {len(all_repos)} 个趋势项目")
            return all_repos[:20]  # 最多返回20个

        except Exception as e:
            logger.error(f"搜索GitHub项目失败: {e}")
            return []

    def check_org_repos(self, org: str, days: int = 7) -> List[Dict]:
        """
        检查特定组织的新项目

        Args:
            org: 组织名
            days: 时间范围

        Returns:
            项目列表
        """
        try:
            url = f"{self.api_base}/orgs/{org}/repos"
            params = {
                "sort": "created",
                "direction": "desc",
                "per_page": 10,
            }

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=15
            )

            if response.status_code == 404:
                logger.debug(f"组织不存在: {org}")
                return []

            response.raise_for_status()
            repos = response.json()

            since_date = datetime.now() - timedelta(days=days)
            results = []

            for repo in repos:
                created_at = datetime.strptime(
                    repo["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                )

                if created_at > since_date:
                    processed = self._process_repo(repo, from_priority_org=True)
                    if processed:
                        results.append(processed)

            return results

        except Exception as e:
            logger.error(f"检查组织 {org} 失败: {e}")
            return []

    def fetch_all_trending(self, days: int = 7) -> List[Dict]:
        """
        获取所有趋势项目

        Args:
            days: 时间范围

        Returns:
            项目列表
        """
        all_repos = []

        # 1. 搜索趋势项目
        trending = self.search_trending_repos(days)
        all_repos.extend(trending)

        # 2. 检查重点组织的新项目
        for org in self.priority_orgs[:5]:  # 只检查前5个，避免速率限制
            try:
                org_repos = self.check_org_repos(org, days)
                all_repos.extend(org_repos)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"检查组织 {org} 失败: {e}")

        # 去重
        seen = set()
        unique_repos = []
        for repo in all_repos:
            if repo["full_name"] not in seen:
                seen.add(repo["full_name"])
                unique_repos.append(repo)

        # 排序
        unique_repos.sort(
            key=lambda x: (
                0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                -x["stars"]
            )
        )

        logger.info(f"GitHub: 总计 {len(unique_repos)} 个趋势项目")
        return unique_repos[:20]

    def _process_repo(self, repo: Dict, from_priority_org: bool = False) -> Optional[Dict]:
        """处理仓库数据"""
        try:
            name = repo.get("name", "")
            full_name = repo.get("full_name", "")
            description = repo.get("description", "") or ""
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            owner = repo.get("owner", {}).get("login", "").lower()

            # 检查是否AI相关
            is_ai_related = self._is_ai_related(name, description, repo.get("topics", []))

            if not is_ai_related and not from_priority_org:
                return None

            # 计算优先级
            priority = self._calculate_priority(
                stars, forks, owner, from_priority_org
            )

            # 计算Fork比率
            fork_ratio = forks / stars if stars > 0 else 0

            return {
                "name": name,
                "full_name": full_name,
                "description": description[:200],
                "url": repo.get("html_url", ""),
                "stars": stars,
                "forks": forks,
                "fork_ratio": round(fork_ratio, 2),
                "owner": owner,
                "language": repo.get("language", "Unknown"),
                "topics": repo.get("topics", [])[:5],
                "created_at": repo.get("created_at", ""),
                "updated_at": repo.get("updated_at", ""),
                "source": "GitHub",
                "priority": priority,
                "is_priority_org": owner in self.priority_orgs,
            }

        except Exception as e:
            logger.debug(f"处理仓库失败: {e}")
            return None

    def _is_ai_related(self, name: str, description: str, topics: List[str]) -> bool:
        """判断是否AI相关"""
        text = f"{name} {description} {' '.join(topics)}".lower()

        for keyword in self.ai_keywords:
            if keyword in text:
                return True

        return False

    def _calculate_priority(
        self, stars: int, forks: int, owner: str, from_priority_org: bool
    ) -> str:
        """计算项目优先级"""
        # P0: 来自顶级组织 且 高Star
        if from_priority_org or owner in self.priority_orgs:
            if stars >= 5000:
                return "P0"
            elif stars >= 1000:
                return "P1"

        # P0: 超高Star（爆款）
        if stars >= 10000:
            return "P0"

        # P1: 高Star
        if stars >= 3000:
            return "P1"

        # P2: 一般
        return "P2"

    def generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        return [
            {
                "name": "gpt-5-preview",
                "full_name": "openai/gpt-5-preview",
                "description": "Official GPT-5 API examples and documentation",
                "url": "https://github.com/openai/gpt-5-preview",
                "stars": 45000,
                "forks": 8500,
                "fork_ratio": 0.19,
                "owner": "openai",
                "language": "Python",
                "topics": ["gpt-5", "llm", "openai", "ai"],
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "GitHub",
                "priority": "P0",
                "is_priority_org": True,
            },
            {
                "name": "llama-4",
                "full_name": "meta-llama/llama-4",
                "description": "LLaMA 4: Open foundation language models",
                "url": "https://github.com/meta-llama/llama-4",
                "stars": 32000,
                "forks": 5200,
                "fork_ratio": 0.16,
                "owner": "meta-llama",
                "language": "Python",
                "topics": ["llama", "llm", "meta", "ai"],
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "GitHub",
                "priority": "P0",
                "is_priority_org": True,
            },
            {
                "name": "ai-agent-framework",
                "full_name": "langchain-ai/ai-agent-framework",
                "description": "Production-ready AI agent framework with RAG support",
                "url": "https://github.com/langchain-ai/ai-agent-framework",
                "stars": 8500,
                "forks": 1200,
                "fork_ratio": 0.14,
                "owner": "langchain-ai",
                "language": "Python",
                "topics": ["agent", "rag", "llm", "langchain"],
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "GitHub",
                "priority": "P1",
                "is_priority_org": True,
            },
        ]


def test_github_monitor():
    """测试GitHub监控器"""
    print("=" * 60)
    print("GitHub爆款项目监控器测试")
    print("=" * 60)

    monitor = GitHubMonitor()

    # 测试数据
    print("\n测试1: 测试数据生成")
    test_repos = monitor.generate_test_data()
    print(f"  生成 {len(test_repos)} 个测试项目")

    for repo in test_repos:
        print(f"\n  [{repo['priority']}] {repo['full_name']}")
        print(f"    ⭐ {repo['stars']:,} | 🍴 {repo['forks']:,}")
        print(f"    {repo['description'][:60]}...")

    # 测试AI相关判断
    print("\n测试2: AI相关性判断")
    test_cases = [
        ("llm-chatbot", "A chatbot using LLM", ["chatbot", "ai"], True),
        ("my-website", "Personal portfolio", ["web"], False),
        ("gpt-wrapper", "GPT API wrapper", [], True),
    ]

    for name, desc, topics, expected in test_cases:
        result = monitor._is_ai_related(name, desc, topics)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {name} → {result} (期望: {expected})")

    # 测试真实API（可能失败）
    print("\n测试3: 真实API获取（可能受限）")
    try:
        repos = monitor.search_trending_repos(days=7, min_stars=5000)
        print(f"  获取到 {len(repos)} 个趋势项目")

        for repo in repos[:3]:
            print(f"\n    [{repo['priority']}] {repo['full_name']}")
            print(f"      ⭐ {repo['stars']:,}")

    except Exception as e:
        print(f"  API获取失败: {e}")

    print("\n测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_github_monitor()
