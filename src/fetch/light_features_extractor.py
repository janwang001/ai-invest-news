# -*- coding: utf-8 -*-
"""
轻量化特征抽取模块

目的：给 selector 提供更多判断维度，而不是生成内容
设计原则：不使用 LLM，只用规则/正则/BeautifulSoup 提取 cheap but high-signal 的字段
"""
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set


# ============================================
# 配置常量
# ============================================

# 公司名称列表（用于 NER 替代）
COMPANY_PATTERNS = {
    # 大型科技公司
    "nvidia", "openai", "google", "microsoft", "meta", "amazon",
    "apple", "alphabet", "tsmc", "amd", "intel", "arm", "qualcomm",
    "broadcom", "samsung", "ibm", "oracle", "salesforce", "adobe",
    # AI 公司
    "anthropic", "deepmind", "hugging face", "huggingface", "stability ai",
    "midjourney", "cohere", "ai21", "inflection", "xai", "mistral",
    # 中国公司
    "baidu", "alibaba", "tencent", "bytedance", "huawei", "xiaomi",
}

# 高管/官方引用标识词
QUOTE_INDICATORS = [
    "said", "says", "told", "announced", "stated", "confirmed",
    "according to", "ceo", "cfo", "cto", "chief", "president",
    "spokesperson", "executive", "founder", "chairman", "director",
]

# 投资相关结构信号词（高价值关键词）
INVESTMENT_SIGNAL_TERMS = {
    # 财务相关
    "revenue", "earnings", "profit", "guidance", "forecast",
    "billion", "million", "quarter", "fiscal", "growth",
    # 交易相关
    "acquire", "acquisition", "merger", "deal", "investment",
    "funding", "raise", "raised", "valuation", "ipo",
    # 监管相关
    "sec", "ftc", "regulation", "antitrust", "compliance",
    "lawsuit", "settlement", "investigation",
    # 产品/技术相关
    "launch", "release", "partnership", "contract", "agreement",
    "patent", "license", "exclusive",
    # 供应链相关
    "supply", "shortage", "capacity", "production", "shipment",
}

# 数字/金额匹配模式
NUMBER_PATTERNS = [
    r"\$\s*\d+(?:\.\d+)?\s*(?:billion|million|bn|mn|m|b)",  # $10 billion
    r"\d+(?:\.\d+)?\s*(?:billion|million|bn|mn)",  # 10 billion
    r"\d+(?:\.\d+)?%",  # 百分比
    r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?",  # $1,000,000
    r"\d+(?:,\d{3})+",  # 大数字 1,000,000
]


@dataclass
class LightArticleFeatures:
    """
    轻量化文章特征

    包含从正文中提取的高信号字段，用于辅助 selector 评分
    """
    # 基础特征
    content_length: int = 0                          # 正文长度
    title_length: int = 0                            # 标题长度

    # 结构信号
    has_numbers: bool = False                        # 是否有金额/百分比
    has_quote: bool = False                          # 是否有高管/官方引用
    number_count: int = 0                            # 数字出现次数

    # 实体识别
    mentioned_companies: List[str] = field(default_factory=list)  # 提及的公司
    company_count: int = 0                           # 公司数量

    # 信号词
    contains_terms: List[str] = field(default_factory=list)       # 包含的结构信号词
    signal_term_count: int = 0                       # 信号词数量

    # 内容质量指标
    paragraph_count: int = 0                         # 段落数量
    avg_sentence_length: float = 0.0                 # 平均句子长度

    # 抽取是否成功
    extraction_success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content_length": self.content_length,
            "title_length": self.title_length,
            "has_numbers": self.has_numbers,
            "has_quote": self.has_quote,
            "number_count": self.number_count,
            "mentioned_companies": self.mentioned_companies,
            "company_count": self.company_count,
            "contains_terms": self.contains_terms,
            "signal_term_count": self.signal_term_count,
            "paragraph_count": self.paragraph_count,
            "avg_sentence_length": self.avg_sentence_length,
            "extraction_success": self.extraction_success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LightArticleFeatures":
        """从字典创建实例"""
        return cls(
            content_length=data.get("content_length", 0),
            title_length=data.get("title_length", 0),
            has_numbers=data.get("has_numbers", False),
            has_quote=data.get("has_quote", False),
            number_count=data.get("number_count", 0),
            mentioned_companies=data.get("mentioned_companies", []),
            company_count=data.get("company_count", 0),
            contains_terms=data.get("contains_terms", []),
            signal_term_count=data.get("signal_term_count", 0),
            paragraph_count=data.get("paragraph_count", 0),
            avg_sentence_length=data.get("avg_sentence_length", 0.0),
            extraction_success=data.get("extraction_success", True),
            error_message=data.get("error_message"),
        )

    def get_quality_score(self) -> float:
        """
        计算内容质量分数（0-10分）

        基于多维度特征计算综合质量分数
        """
        score = 0.0

        # 内容长度评分（0-2分）
        if self.content_length > 2000:
            score += 2.0
        elif self.content_length > 1000:
            score += 1.5
        elif self.content_length > 500:
            score += 1.0
        elif self.content_length > 200:
            score += 0.5

        # 数字信息评分（0-2分）
        if self.has_numbers:
            score += 1.0
            score += min(self.number_count * 0.2, 1.0)  # 最多加1分

        # 引用评分（0-1.5分）
        if self.has_quote:
            score += 1.5

        # 公司提及评分（0-1.5分）
        if self.company_count > 0:
            score += min(self.company_count * 0.5, 1.5)

        # 信号词评分（0-2分）
        if self.signal_term_count > 0:
            score += min(self.signal_term_count * 0.3, 2.0)

        # 段落结构评分（0-1分）
        if self.paragraph_count >= 3:
            score += 1.0
        elif self.paragraph_count >= 2:
            score += 0.5

        return round(score, 2)


class LightFeaturesExtractor:
    """
    轻量化特征抽取器

    使用规则、正则表达式从文章正文中提取高信号特征
    不使用 LLM，执行速度快、成本低
    """

    def __init__(self):
        """初始化抽取器"""
        self.logger = self._setup_logger()
        # 预编译正则表达式
        self._number_patterns = [re.compile(p, re.IGNORECASE) for p in NUMBER_PATTERNS]
        self._company_patterns = self._build_company_patterns()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger

    def _build_company_patterns(self) -> List[re.Pattern]:
        """构建公司名称匹配模式"""
        patterns = []
        for company in COMPANY_PATTERNS:
            # 使用单词边界匹配，避免部分匹配
            pattern = re.compile(rf"\b{re.escape(company)}\b", re.IGNORECASE)
            patterns.append((company, pattern))
        return patterns

    def _extract_numbers(self, text: str) -> tuple:
        """
        提取数字/金额信息

        :param text: 文本内容
        :return: (has_numbers, number_count)
        """
        count = 0
        for pattern in self._number_patterns:
            matches = pattern.findall(text)
            count += len(matches)

        return count > 0, count

    def _extract_quotes(self, text: str) -> bool:
        """
        检测是否有高管/官方引用

        :param text: 文本内容
        :return: 是否包含引用
        """
        text_lower = text.lower()
        for indicator in QUOTE_INDICATORS:
            if indicator in text_lower:
                return True
        return False

    def _extract_companies(self, text: str) -> List[str]:
        """
        提取提及的公司名称

        :param text: 文本内容
        :return: 公司名称列表
        """
        mentioned = set()
        for company, pattern in self._company_patterns:
            if pattern.search(text):
                mentioned.add(company)
        return list(mentioned)

    def _extract_signal_terms(self, text: str) -> List[str]:
        """
        提取投资信号词

        :param text: 文本内容
        :return: 信号词列表
        """
        text_lower = text.lower()
        found_terms = []
        for term in INVESTMENT_SIGNAL_TERMS:
            if term in text_lower:
                found_terms.append(term)
        return found_terms

    def _calculate_text_metrics(self, text: str) -> tuple:
        """
        计算文本度量指标

        :param text: 文本内容
        :return: (paragraph_count, avg_sentence_length)
        """
        # 段落数量（以双换行或单换行分隔）
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n', text) if p.strip()]
        paragraph_count = len(paragraphs)

        # 句子长度（简单按句号分割）
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        else:
            avg_sentence_length = 0.0

        return paragraph_count, avg_sentence_length

    def extract(
        self,
        content: str,
        title: Optional[str] = None,
    ) -> LightArticleFeatures:
        """
        从文章内容中提取轻量化特征

        :param content: 文章正文内容
        :param title: 文章标题（可选）
        :return: LightArticleFeatures 对象
        """
        features = LightArticleFeatures()

        if not content:
            features.extraction_success = False
            features.error_message = "empty_content"
            return features

        try:
            # 基础特征
            features.content_length = len(content)
            features.title_length = len(title) if title else 0

            # 合并标题和内容进行分析
            full_text = f"{title or ''} {content}"

            # 提取数字信息
            features.has_numbers, features.number_count = self._extract_numbers(full_text)

            # 提取引用信息
            features.has_quote = self._extract_quotes(full_text)

            # 提取公司信息
            features.mentioned_companies = self._extract_companies(full_text)
            features.company_count = len(features.mentioned_companies)

            # 提取信号词
            features.contains_terms = self._extract_signal_terms(full_text)
            features.signal_term_count = len(features.contains_terms)

            # 计算文本度量
            features.paragraph_count, features.avg_sentence_length = \
                self._calculate_text_metrics(content)

            features.extraction_success = True

            self.logger.debug(
                f"轻量化特征提取完成: 长度={features.content_length}, "
                f"数字={features.has_numbers}, 引用={features.has_quote}, "
                f"公司={features.company_count}, 信号词={features.signal_term_count}"
            )

        except Exception as e:
            features.extraction_success = False
            features.error_message = str(e)
            self.logger.error(f"轻量化特征提取失败: {e}")

        return features

    def extract_batch(
        self,
        articles: List[Dict[str, Any]],
    ) -> List[LightArticleFeatures]:
        """
        批量提取轻量化特征

        :param articles: 文章列表，每个元素包含 content 和 title（可选）
        :return: LightArticleFeatures 列表
        """
        results = []
        total = len(articles)

        for idx, article in enumerate(articles, 1):
            content = article.get("content", article.get("fetched_content", ""))
            title = article.get("title", "")

            features = self.extract(content, title)
            results.append(features)

            if idx % 10 == 0:
                self.logger.info(f"轻量化特征提取进度: {idx}/{total}")

        success_count = sum(1 for f in results if f.extraction_success)
        self.logger.info(f"批量提取完成: {success_count}/{total} 成功")

        return results


def extract_light_features(
    content: str,
    title: Optional[str] = None,
) -> LightArticleFeatures:
    """
    便捷函数：从文章内容中提取轻量化特征

    :param content: 文章正文内容
    :param title: 文章标题（可选）
    :return: LightArticleFeatures 对象
    """
    extractor = LightFeaturesExtractor()
    return extractor.extract(content, title)


if __name__ == "__main__":
    # 测试代码
    test_content = """
    NVIDIA announced today that it has achieved record quarterly revenue of $26.0 billion,
    up 122% from a year ago. The company's data center revenue reached $22.6 billion,
    driven by strong demand for AI training and inference chips.

    CEO Jensen Huang said, "We are experiencing an unprecedented demand for our H100 and
    upcoming H200 GPUs. The AI revolution is just beginning."

    The company also announced a partnership with Microsoft to accelerate AI deployment
    in the cloud. This deal is valued at approximately $5 billion over the next three years.

    Analysts at Goldman Sachs raised their price target to $1,200, citing the company's
    dominant position in the AI chip market. However, some concerns remain about potential
    supply chain constraints and regulatory scrutiny from the SEC.
    """

    test_title = "NVIDIA Reports Record $26B Quarterly Revenue Amid AI Boom"

    print("=" * 60)
    print("轻量化特征抽取模块测试")
    print("=" * 60)

    features = extract_light_features(test_content, test_title)

    print(f"\n内容长度: {features.content_length}")
    print(f"标题长度: {features.title_length}")
    print(f"包含数字: {features.has_numbers} (数量: {features.number_count})")
    print(f"包含引用: {features.has_quote}")
    print(f"提及公司: {features.mentioned_companies}")
    print(f"信号词: {features.contains_terms}")
    print(f"段落数量: {features.paragraph_count}")
    print(f"平均句子长度: {features.avg_sentence_length:.1f}")
    print(f"\n质量分数: {features.get_quality_score()}")
