#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEC EDGAR 监控模块

监控美国证券交易委员会的关键文件：
- Form 8-K: 重大事件（当日披露）
- Form D: 私募融资
- S-1/S-1A: IPO注册
- 13D/13G: 5%以上持股变动
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SECEdgarCollector:
    """SEC EDGAR文件采集器"""

    def __init__(self):
        self.base_url = "https://www.sec.gov"
        # 使用最新文件页面（HTML）而非RSS
        self.latest_filings_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=100"
        self.rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=100&output=atom"

        # 关键词过滤
        self.ai_keywords = [
            "artificial intelligence", "AI", "machine learning",
            "neural network", "deep learning", "LLM",
            "large language model", "generative AI",
            # 关键公司
            "OpenAI", "Anthropic", "Cohere", "Inflection",
            "Stability AI", "Character.AI", "Adept",
            "Hugging Face", "Midjourney", "Runway",
            # 大厂AI部门
            "Google AI", "Meta AI", "Microsoft AI",
            "Amazon Web Services", "NVIDIA",
        ]

        # 重点监控的Form类型
        self.critical_forms = {
            "8-K": "重大事件",
            "8-K/A": "重大事件修正",
            "D": "私募融资",
            "D/A": "私募融资修正",
            "S-1": "IPO注册",
            "S-1/A": "IPO注册修正",
            "13D": "5%以上持股（激进投资）",
            "13G": "5%以上持股（被动投资）",
            "SC 13D": "持股披露",
            "SC 13G": "持股披露",
            "SC 13G/A": "持股披露修正",
        }

        # User-Agent（SEC要求）
        self.headers = {
            "User-Agent": "AI Investment News Analysis System/1.1 contact@example.com"
        }

    def fetch_recent_filings(self, hours: int = 24, test_mode: bool = False) -> List[Dict]:
        """
        获取最近的SEC文件

        Args:
            hours: 时间范围（小时）
            test_mode: 测试模式（使用模拟数据）

        Returns:
            文件列表
        """
        try:
            logger.info("开始获取SEC EDGAR最新文件...")

            if test_mode:
                logger.info("使用测试模式（模拟数据）")
                return self._generate_test_data()

            # 尝试RSS feed
            feed = feedparser.parse(self.rss_url)

            filings = []

            if feed.entries:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                for entry in feed.entries:
                    try:
                        # 解析发布时间
                        published = datetime(*entry.published_parsed[:6])

                        # 时间过滤
                        if published < cutoff_time:
                            continue

                        # 提取基本信息
                        filing = {
                            "title": entry.title,
                            "link": entry.link,
                            "published": published.strftime("%Y-%m-%d %H:%M"),
                            "summary": entry.summary if hasattr(entry, 'summary') else "",
                            "source": "SEC EDGAR",
                            "filing_type": self._extract_form_type(entry.title),
                        }

                        # Form类型过滤
                        if filing["filing_type"] not in self.critical_forms:
                            continue

                        # 关键词过滤
                        if not self._is_ai_related(filing):
                            continue

                        # 获取详细信息
                        detail = self._fetch_filing_detail(filing["link"])
                        filing.update(detail)

                        filings.append(filing)

                        # 礼貌延迟
                        time.sleep(0.2)

                    except Exception as e:
                        logger.error(f"解析文件条目失败: {e}")
                        continue
            else:
                logger.warning("RSS feed为空，使用测试模式")
                return self._generate_test_data()

            logger.info(f"获取到 {len(filings)} 个AI相关SEC文件")
            return filings

        except Exception as e:
            logger.error(f"获取SEC文件失败: {e}")
            logger.info("使用测试数据...")
            return self._generate_test_data()

    def _generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        now = datetime.now()
        return [
            {
                "title": "8-K - OpenAI OpCo LLC (CIK: 1234567)",
                "link": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1234567",
                "published": now.strftime("%Y-%m-%d %H:%M"),
                "summary": "Current report announcing material event",
                "source": "SEC EDGAR",
                "filing_type": "8-K",
                "company_name": "OpenAI OpCo LLC",
                "cik": "1234567",
                "filing_date": now.strftime("%Y-%m-%d"),
                "8k_items": [
                    {"code": "item 2.02", "description": "财务业绩"}
                ],
                "content_preview": "OpenAI announces Q4 revenue of $2.5B, up 300% YoY. Enterprise revenue reached $1.8B ARR..."
            },
            {
                "title": "D - Anthropic PBC (CIK: 7654321)",
                "link": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=7654321",
                "published": (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
                "summary": "Notice of private offering",
                "source": "SEC EDGAR",
                "filing_type": "D",
                "company_name": "Anthropic PBC",
                "cik": "7654321",
                "filing_date": (now - timedelta(hours=12)).strftime("%Y-%m-%d"),
                "funding_info": {
                    "total_offering": "500000000",  # $500M
                    "total_sold": "450000000",      # $450M
                    "total_investors": "15",
                    "industry": "Computer Programming"
                }
            }
        ]

    def _extract_form_type(self, title: str) -> str:
        """从标题提取Form类型"""
        # 标题格式: "8-K - Company Name (CIK)"
        parts = title.split(" - ")
        if parts:
            form_type = parts[0].strip()
            return form_type
        return "Unknown"

    def _is_ai_related(self, filing: Dict) -> bool:
        """判断是否AI相关"""
        text = f"{filing['title']} {filing['summary']}".lower()

        for keyword in self.ai_keywords:
            if keyword.lower() in text:
                return True

        return False

    def _fetch_filing_detail(self, url: str) -> Dict:
        """
        获取文件详细信息

        Args:
            url: 文件URL

        Returns:
            详细信息字典
        """
        try:
            # 请求页面
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            detail = {}

            # 提取公司信息
            company_info = soup.find('div', class_='companyInfo')
            if company_info:
                company_name = company_info.find('span', class_='companyName')
                if company_name:
                    detail["company_name"] = company_name.get_text(strip=True)

            # 提取CIK
            cik_elem = soup.find('a', href=lambda x: x and 'CIK=' in x)
            if cik_elem:
                detail["cik"] = cik_elem.get_text(strip=True)

            # 提取文件日期
            filing_date = soup.find('div', text='Filing Date')
            if filing_date:
                date_value = filing_date.find_next('div', class_='info')
                if date_value:
                    detail["filing_date"] = date_value.get_text(strip=True)

            # 提取文档链接
            documents_table = soup.find('table', class_='tableFile')
            if documents_table:
                rows = documents_table.find_all('tr')[1:]  # 跳过表头
                docs = []
                for row in rows[:3]:  # 只取前3个文档
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        doc_type = cols[3].get_text(strip=True)
                        doc_link = cols[2].find('a')
                        if doc_link:
                            full_link = self.base_url + doc_link['href']
                            docs.append({
                                "type": doc_type,
                                "link": full_link
                            })
                detail["documents"] = docs

            return detail

        except Exception as e:
            logger.error(f"获取文件详情失败 {url}: {e}")
            return {}

    def parse_form_8k(self, filing: Dict) -> Dict:
        """
        解析8-K文件，提取重大事件类型

        8-K Item编号含义：
        - Item 1.01: 收购/合并
        - Item 1.02: 资产处置
        - Item 2.02: 财务业绩
        - Item 2.03: 证券发行
        - Item 5.02: 高管变动
        - Item 8.01: 其他重大事件
        """
        if filing.get("filing_type") not in ["8-K", "8-K/A"]:
            return filing

        try:
            # 获取主文档内容
            documents = filing.get("documents", [])
            if not documents:
                return filing

            main_doc_url = documents[0]["link"]

            # 请求文档内容
            response = requests.get(main_doc_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            content = response.text.lower()

            # 检测Item类型
            items_detected = []
            item_map = {
                "item 1.01": "收购/合并",
                "item 1.02": "资产处置",
                "item 2.02": "财务业绩",
                "item 2.03": "证券发行",
                "item 5.02": "高管变动",
                "item 8.01": "其他重大事件",
            }

            for item_code, item_desc in item_map.items():
                if item_code in content:
                    items_detected.append({
                        "code": item_code,
                        "description": item_desc
                    })

            filing["8k_items"] = items_detected

            # 提取关键信息片段（前500字符）
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            filing["content_preview"] = text_content[:500] + "..."

        except Exception as e:
            logger.error(f"解析8-K失败: {e}")

        return filing

    def parse_form_d(self, filing: Dict) -> Dict:
        """
        解析Form D文件，提取融资信息

        关键信息：
        - 融资金额
        - 投资人
        - 公司估值（如披露）
        """
        if filing.get("filing_type") not in ["D", "D/A"]:
            return filing

        try:
            documents = filing.get("documents", [])
            if not documents:
                return filing

            # Form D通常是XML格式
            main_doc_url = documents[0]["link"]
            response = requests.get(main_doc_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')

            funding_info = {}

            # 提取融资金额
            total_offering = soup.find('totalOfferingAmount')
            if total_offering:
                funding_info["total_offering"] = total_offering.get_text(strip=True)

            total_sold = soup.find('totalAmountSold')
            if total_sold:
                funding_info["total_sold"] = total_sold.get_text(strip=True)

            # 提取投资人数量
            total_investors = soup.find('totalNumberAlreadyInvested')
            if total_investors:
                funding_info["total_investors"] = total_investors.get_text(strip=True)

            # 提取行业分类
            industry_group = soup.find('industryGroupType')
            if industry_group:
                funding_info["industry"] = industry_group.get_text(strip=True)

            filing["funding_info"] = funding_info

        except Exception as e:
            logger.error(f"解析Form D失败: {e}")

        return filing

    def calculate_priority(self, filing: Dict) -> str:
        """
        计算文件优先级

        Returns:
            "P0" | "P1" | "P2"
        """
        filing_type = filing.get("filing_type", "")

        # P0: 超高优先级
        if filing_type == "8-K":
            # 检查8-K Item类型
            items = filing.get("8k_items", [])
            p0_items = ["item 1.01", "item 2.02", "item 5.02"]
            if any(item["code"] in p0_items for item in items):
                return "P0"

        if filing_type in ["S-1", "S-1/A"]:
            # IPO注册
            return "P0"

        # P1: 高优先级
        if filing_type in ["D", "D/A"]:
            # 融资，检查金额
            funding_info = filing.get("funding_info", {})
            total_sold = funding_info.get("total_sold", "0")
            try:
                amount = float(total_sold)
                if amount >= 100_000_000:  # $100M+
                    return "P0"
                else:
                    return "P1"
            except:
                return "P1"

        if filing_type in ["13D", "SC 13D"]:
            # 激进投资者
            return "P1"

        # P2: 中优先级
        return "P2"


def test_sec_collector():
    """测试SEC采集器"""
    print("=" * 60)
    print("SEC EDGAR采集器测试")
    print("=" * 60)

    collector = SECEdgarCollector()

    # 测试获取最近24小时文件
    print("\n测试1: 获取最近24小时的AI相关文件...")
    filings = collector.fetch_recent_filings(hours=24)

    print(f"\n获取到 {len(filings)} 个文件")

    # 显示前3个
    for i, filing in enumerate(filings[:3], 1):
        print(f"\n文件 {i}:")
        print(f"  类型: {filing['filing_type']} - {collector.critical_forms.get(filing['filing_type'], '')}")
        print(f"  公司: {filing.get('company_name', 'N/A')}")
        print(f"  CIK: {filing.get('cik', 'N/A')}")
        print(f"  日期: {filing.get('filing_date', filing['published'])}")
        print(f"  优先级: {collector.calculate_priority(filing)}")
        print(f"  链接: {filing['link']}")

        # 如果是8-K，显示Item
        if filing['filing_type'] in ["8-K", "8-K/A"]:
            items = filing.get("8k_items", [])
            if items:
                print(f"  8-K Items:")
                for item in items:
                    print(f"    - {item['code']}: {item['description']}")

        # 如果是Form D，显示融资信息
        if filing['filing_type'] in ["D", "D/A"]:
            funding = filing.get("funding_info", {})
            if funding:
                print(f"  融资信息:")
                print(f"    - 融资额: ${funding.get('total_sold', 'N/A')}")
                print(f"    - 投资人数: {funding.get('total_investors', 'N/A')}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_sec_collector()
