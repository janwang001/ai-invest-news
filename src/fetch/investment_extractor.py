# -*- coding: utf-8 -*-
"""
投资信息抽取模块

通过大模型从文章正文中抽取投资级别的结构化信息
设计目标：提取可量化事实、商业化信息、行业影响、管理层表态、风险因素
"""
import json
import logging
import os
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dashscope import Generation

from .fetch_config import (
    DATE_FORMAT,
    EXTRACTED_FILE_SUFFIX,
    EXTRACTOR_MODEL_NAME,
    INVESTMENT_DIMENSIONS,
    MAX_ITEMS_PER_DIMENSION,
    get_daily_data_dir,
    url_to_filename,
)


@dataclass
class InvestmentThesis:
    """
    投资论点结构

    包含看涨/看跌理由、关键问题、时间周期、历史类比
    """
    bull_case: List[str] = field(default_factory=list)         # 看涨理由（3个）
    bear_case: List[str] = field(default_factory=list)         # 看跌理由（3个）
    key_question: str = ""                                      # 关键问题（决定投资结果）
    time_horizon: str = ""                                      # 影响兑现时间
    comparable_events: List[str] = field(default_factory=list) # 历史类似事件

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_question": self.key_question,
            "time_horizon": self.time_horizon,
            "comparable_events": self.comparable_events,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestmentThesis":
        """从字典创建实例"""
        return cls(
            bull_case=data.get("bull_case", []),
            bear_case=data.get("bear_case", []),
            key_question=data.get("key_question", ""),
            time_horizon=data.get("time_horizon", ""),
            comparable_events=data.get("comparable_events", []),
        )


@dataclass
class InvestmentInfo:
    """
    投资信息结构

    包含 6 个维度的结构化投资信息 + AI 总结 + 投资论点
    """
    facts: List[str] = field(default_factory=list)              # 明确事实
    numbers: List[str] = field(default_factory=list)            # 数字/量化信息
    business: List[str] = field(default_factory=list)           # 商业化信息
    industry_impact: List[str] = field(default_factory=list)    # 行业影响
    management_claims: List[str] = field(default_factory=list)  # 管理层表态
    uncertainties: List[str] = field(default_factory=list)      # 不确定性/风险
    ai_summary: str = ""                                        # AI 内容总结
    investment_thesis: Optional[InvestmentThesis] = None        # 投资论点

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "facts": self.facts,
            "numbers": self.numbers,
            "business": self.business,
            "industry_impact": self.industry_impact,
            "management_claims": self.management_claims,
            "uncertainties": self.uncertainties,
            "ai_summary": self.ai_summary,
            "investment_thesis": self.investment_thesis.to_dict() if self.investment_thesis else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestmentInfo":
        """从字典创建实例"""
        investment_thesis_data = data.get("investment_thesis")
        investment_thesis = InvestmentThesis.from_dict(investment_thesis_data) if investment_thesis_data else None

        return cls(
            facts=data.get("facts", []),
            numbers=data.get("numbers", []),
            business=data.get("business", []),
            industry_impact=data.get("industry_impact", []),
            management_claims=data.get("management_claims", []),
            uncertainties=data.get("uncertainties", []),
            ai_summary=data.get("ai_summary", ""),
            investment_thesis=investment_thesis,
        )

    def is_empty(self) -> bool:
        """检查是否所有维度都为空"""
        return not any([
            self.facts,
            self.numbers,
            self.business,
            self.industry_impact,
            self.management_claims,
            self.uncertainties,
        ])

    def total_items(self) -> int:
        """返回所有维度的条目总数"""
        return (
            len(self.facts) +
            len(self.numbers) +
            len(self.business) +
            len(self.industry_impact) +
            len(self.management_claims) +
            len(self.uncertainties)
        )


@dataclass
class ExtractionResult:
    """
    抽取结果

    包含抽取的投资信息和统计数据
    """
    url: str
    success: bool
    title: Optional[str] = None
    investment_info: Optional[InvestmentInfo] = None
    file_path: Optional[str] = None

    # 统计信息
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "url": self.url,
            "success": self.success,
            "title": self.title,
            "investment_info": self.investment_info.to_dict() if self.investment_info else None,
            "file_path": self.file_path,
            "stats": self.stats,
        }


class InvestmentExtractor:
    """
    投资信息抽取器

    使用大模型从文章正文中抽取结构化的投资信息，支持：
    - 6 个维度的投资信息抽取
    - 专业投资分析师视角的 prompt 设计
    - 本地文件存储
    - 抽取统计信息
    """

    def __init__(
        self,
        model_name: str = EXTRACTOR_MODEL_NAME,
        max_items: int = MAX_ITEMS_PER_DIMENSION,
    ):
        """
        初始化抽取器

        :param model_name: AI 模型名称
        :param max_items: 每个维度的最大条目数
        """
        self.model_name = model_name
        self.max_items = max_items
        self.logger = self._setup_logger()

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

    def _get_api_key(self) -> str:
        """
        获取 API 密钥

        :return: API 密钥
        :raises ValueError: 未设置 API 密钥环境变量
        """
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            self.logger.warning("未设置 DASHSCOPE_API_KEY 环境变量，使用本地模式")
            return "local_mode"
        return api_key

    def _build_prompt(self, content: str, title: Optional[str] = None) -> str:
        """
        构建专业投资分析师视角的提示词

        :param content: 文章正文内容
        :param title: 文章标题（可选）
        :return: 构建好的提示词
        """
        title_section = f"文章标题：{title}\n" if title else ""

        prompt = f"""你是一位资深的投资分析师，拥有 20 年以上的二级市场研究经验。
你的任务是从以下新闻/文章中抽取对投资决策有价值的结构化信息。

{title_section}文章正文：
====================
{content}
====================

请严格按照以下 8 个维度进行信息抽取，每个维度最多提取 {self.max_items} 条最重要的信息：

1. **facts（明确事实）**
   - 已经发生的客观事实
   - 可验证的事件、协议、合作
   - 排除：预测、计划、表态

2. **numbers（数字/量化信息）**
   - 具体数字：金额、比例、增长率、市值、估值
   - 时间节点、周期
   - 对比数据（同比、环比）

3. **business（商业化信息）**
   - 定价策略、客户情况
   - 订单、营收、利润相关
   - 商业模式变化

4. **industry_impact（行业影响）**
   - 竞争格局变化
   - 上下游关系影响
   - 替代关系、市场份额变动
   - 行业趋势信号

5. **management_claims（管理层表态）**
   - 公司高管、创始人的说法
   - 官方声明、指引
   - 注意：这是"说法"而非"事实"

6. **uncertainties（不确定性/风险）**
   - 执行风险
   - 技术风险
   - 政策风险
   - 市场风险
   - 竞争风险

7. **ai_summary（内容总结）**
   - 用 2-3 句话总结文章核心内容
   - 突出对投资决策最重要的信息
   - 包含关键数字和事实

8. **investment_thesis（投资论点）** - 结构化投资分析
   - bull_case: 3个最强的看涨理由（具体、可验证、包含数字支撑）
   - bear_case: 3个最强的看跌理由（具体、可验证、包含风险量化）
   - key_question: 决定投资结果的关键问题（一句话，聚焦核心不确定性）
   - time_horizon: 影响兑现时间（"即时" | "1-3个月" | "6-12个月" | "长期"）
   - comparable_events: 历史类似事件（例如："类似NVIDIA 2016年加密热潮"，最多2个）

请严格返回以下 JSON 格式，不要添加任何其他内容：
{{
    "facts": ["事实1", "事实2", ...],
    "numbers": ["数字信息1", "数字信息2", ...],
    "business": ["商业信息1", "商业信息2", ...],
    "industry_impact": ["行业影响1", "行业影响2", ...],
    "management_claims": ["表态1", "表态2", ...],
    "uncertainties": ["风险1", "风险2", ...],
    "ai_summary": "文章核心内容的简洁总结...",
    "investment_thesis": {{
        "bull_case": ["看涨理由1（具体）", "看涨理由2（具体）", "看涨理由3（具体）"],
        "bear_case": ["看跌理由1（具体）", "看跌理由2（具体）", "看跌理由3（具体）"],
        "key_question": "决定投资结果的关键问题？",
        "time_horizon": "1-3个月",
        "comparable_events": ["历史类似事件1", "历史类似事件2"]
    }}
}}

注意事项：
- 每条信息应简洁明了，不超过 100 字
- 如果某个维度没有相关信息，返回空数组 []
- ai_summary 应为一段完整的文字，不超过 200 字
- 不要编造信息，只提取文章中明确提到的内容
- 区分"事实"和"表态"：已发生的是事实，管理层说的是表态
- 保持专业、客观的投资分析师视角
"""
        return prompt

    def _generate_local_result(self, content: str) -> InvestmentInfo:
        """
        本地模式生成模拟结果

        :param content: 文章内容
        :return: 模拟的投资信息
        """
        self.logger.info("使用本地模式生成模拟结果...")
        return InvestmentInfo(
            facts=["[本地模式] 文章内容已接收，待实际 API 调用分析"],
            numbers=[],
            business=[],
            industry_impact=[],
            management_claims=[],
            uncertainties=["[本地模式] 无法进行真实分析，请配置 API 密钥"],
            ai_summary="[本地模式] 无法生成总结，请配置 DASHSCOPE_API_KEY 环境变量",
        )

    def _call_ai_model(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """
        调用 AI 模型

        :param prompt: 提示词
        :param api_key: API 密钥
        :return: 模型响应的 JSON 数据
        :raises RuntimeError: 模型调用失败
        """
        if api_key == "local_mode":
            return None

        try:
            self.logger.debug(f"调用模型: {self.model_name}")
            self.logger.debug(f"提示词长度: {len(prompt)} 字符")

            response = Generation.call(
                api_key=api_key,
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional investment analyst. "
                                   "Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                result_format="message",
            )

            if not response or not response.output or not response.output.choices:
                raise RuntimeError("API 响应格式异常：缺少必要字段")

            content = response.output.choices[0].message["content"]
            self.logger.debug(f"原始响应长度: {len(content)} 字符")

            # 尝试解析 JSON
            # 处理可能的 markdown 代码块包裹
            if content.startswith("```"):
                lines = content.split("\n")
                # 移除首尾的 ``` 行
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```") and not in_json:
                        in_json = True
                        continue
                    elif line.startswith("```") and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}")
            raise RuntimeError(f"JSON 解析失败: {e}")
        except Exception as e:
            self.logger.error(f"AI 模型调用失败: {e}")
            raise RuntimeError(f"AI 模型调用失败: {e}")

    def _validate_and_truncate(self, data: Dict[str, Any]) -> InvestmentInfo:
        """
        验证并截断抽取结果

        :param data: 原始抽取数据
        :return: 验证后的 InvestmentInfo
        """
        result = InvestmentInfo()

        for dim in INVESTMENT_DIMENSIONS:
            items = data.get(dim, [])
            if not isinstance(items, list):
                items = []

            # 过滤非字符串和空字符串
            items = [str(item).strip() for item in items if item]
            items = [item for item in items if item]

            # 截断到最大数量
            items = items[:self.max_items]

            setattr(result, dim, items)

        # 处理 ai_summary 字段
        ai_summary = data.get("ai_summary", "")
        if isinstance(ai_summary, str):
            result.ai_summary = ai_summary.strip()
        else:
            result.ai_summary = ""

        # 处理 investment_thesis 字段
        thesis_data = data.get("investment_thesis", {})
        if isinstance(thesis_data, dict):
            try:
                # 验证并清理 bull_case
                bull_case = thesis_data.get("bull_case", [])
                if isinstance(bull_case, list):
                    bull_case = [str(item).strip() for item in bull_case if item][:3]
                else:
                    bull_case = []

                # 验证并清理 bear_case
                bear_case = thesis_data.get("bear_case", [])
                if isinstance(bear_case, list):
                    bear_case = [str(item).strip() for item in bear_case if item][:3]
                else:
                    bear_case = []

                # 验证并清理 key_question
                key_question = thesis_data.get("key_question", "")
                if not isinstance(key_question, str):
                    key_question = ""
                key_question = key_question.strip()

                # 验证并清理 time_horizon
                time_horizon = thesis_data.get("time_horizon", "")
                if not isinstance(time_horizon, str):
                    time_horizon = ""
                time_horizon = time_horizon.strip()

                # 验证并清理 comparable_events
                comparable_events = thesis_data.get("comparable_events", [])
                if isinstance(comparable_events, list):
                    comparable_events = [str(item).strip() for item in comparable_events if item][:2]
                else:
                    comparable_events = []

                result.investment_thesis = InvestmentThesis(
                    bull_case=bull_case,
                    bear_case=bear_case,
                    key_question=key_question,
                    time_horizon=time_horizon,
                    comparable_events=comparable_events,
                )
            except Exception as e:
                self.logger.warning(f"处理 investment_thesis 失败: {e}")
                result.investment_thesis = None

        return result

    def extract(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
        save_to_disk: bool = True,
    ) -> ExtractionResult:
        """
        从文章内容中抽取投资信息

        :param content: 文章正文内容
        :param url: 文章 URL（用于标识和存储）
        :param title: 文章标题（可选）
        :param save_to_disk: 是否保存到本地磁盘
        :return: ExtractionResult 对象
        """
        start_time = time.time()
        result = ExtractionResult(url=url, success=False, title=title)

        if not content or not content.strip():
            result.stats["error"] = "empty_content"
            return result

        try:
            # 获取 API 密钥
            api_key = self._get_api_key()

            # 构建提示词
            prompt = self._build_prompt(content, title)

            # 调用模型或使用本地模式
            if api_key == "local_mode":
                investment_info = self._generate_local_result(content)
            else:
                raw_data = self._call_ai_model(prompt, api_key)
                investment_info = self._validate_and_truncate(raw_data)

            # 填充结果
            result.success = True
            result.investment_info = investment_info

            # 统计信息
            result.stats = {
                "content_length": len(content),
                "prompt_length": len(prompt),
                "total_items": investment_info.total_items(),
                "items_per_dimension": {
                    dim: len(getattr(investment_info, dim))
                    for dim in INVESTMENT_DIMENSIONS
                },
                "extract_time_ms": int((time.time() - start_time) * 1000),
                "model": self.model_name,
            }

            # 保存到磁盘
            if save_to_disk and result.success:
                result.file_path = self._save_to_disk(url, result)

            self.logger.info(
                f"抽取完成: {investment_info.total_items()} 条信息, "
                f"耗时 {result.stats['extract_time_ms']}ms"
            )

        except Exception as e:
            result.stats["error"] = str(e)
            result.stats["extract_time_ms"] = int((time.time() - start_time) * 1000)
            self.logger.error(f"抽取失败: {e}")

        return result

    def extract_batch(
        self,
        articles: List[Dict[str, Any]],
        save_to_disk: bool = True,
    ) -> List[ExtractionResult]:
        """
        批量抽取投资信息

        :param articles: 文章列表，每个元素包含 content, url, title（可选）
        :param save_to_disk: 是否保存到本地磁盘
        :return: ExtractionResult 列表
        """
        results = []
        total = len(articles)

        for idx, article in enumerate(articles, 1):
            self.logger.info(f"处理文章 [{idx}/{total}]: {article.get('title', article.get('url', 'Unknown'))}")

            result = self.extract(
                content=article.get("content", ""),
                url=article.get("url", ""),
                title=article.get("title"),
                save_to_disk=save_to_disk,
            )
            results.append(result)

            # 请求间隔，避免 API 限流
            if idx < total:
                time.sleep(1)

        # 汇总统计
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"批量抽取完成: {success_count}/{total} 成功")

        return results

    def _save_to_disk(self, url: str, result: ExtractionResult) -> str:
        """
        保存抽取结果到本地磁盘

        :param url: 文章 URL
        :param result: 抽取结果
        :return: 保存的文件路径
        """
        # 获取今日数据目录
        today_str = datetime.now().strftime(DATE_FORMAT)
        daily_dir = get_daily_data_dir(today_str)

        # 生成文件名（基于原文件名添加后缀）
        base_filename = url_to_filename(url)
        # 替换扩展名
        filename = base_filename.replace(".txt", EXTRACTED_FILE_SUFFIX)
        if not filename.endswith(EXTRACTED_FILE_SUFFIX):
            filename = base_filename.rsplit(".", 1)[0] + EXTRACTED_FILE_SUFFIX

        file_path = daily_dir / filename

        # 构建保存内容
        save_data = {
            "url": url,
            "title": result.title,
            "investment_info": result.investment_info.to_dict() if result.investment_info else None,
            "stats": result.stats,
            "extracted_at": datetime.now().isoformat(),
        }

        # 覆盖写入
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"抽取结果已保存: {file_path}")
        return str(file_path)


def extract_investment_info(
    content: str,
    url: str,
    title: Optional[str] = None,
    save_to_disk: bool = True,
) -> ExtractionResult:
    """
    便捷函数：从文章内容中抽取投资信息

    :param content: 文章正文内容
    :param url: 文章 URL
    :param title: 文章标题（可选）
    :param save_to_disk: 是否保存到本地磁盘
    :return: ExtractionResult 对象
    """
    extractor = InvestmentExtractor()
    return extractor.extract(content, url, title, save_to_disk)


if __name__ == "__main__":
    # 测试代码
    test_content = """
    OpenAI在最新一轮融资中获得66亿美元投资，估值达到1570亿美元，
    较上一轮融资时的290亿美元估值增长超过5倍。本轮融资由Thrive Capital领投，
    微软、英伟达、软银等知名投资者跟投。

    OpenAI CEO Sam Altman表示，这笔资金将用于扩展AI基础设施和加速AGI研究。
    他预计公司将在2025年实现盈利，并计划在未来18个月内推出GPT-5。

    分析师指出，此次融资反映了市场对AI行业的持续看好，但也存在估值过高的风险。
    竞争对手Anthropic和Google也在加大AI投入，行业竞争日趋激烈。

    值得注意的是，OpenAI正在考虑转型为营利性公司，这一变化可能影响其与微软的
    合作关系。监管层面，FTC正在审查AI行业的投资和合作行为。
    """

    test_url = "https://example.com/openai-funding-2024"
    test_title = "OpenAI获66亿美元融资，估值达1570亿美元"

    print("=" * 60)
    print("投资信息抽取模块测试")
    print("=" * 60)

    result = extract_investment_info(
        content=test_content,
        url=test_url,
        title=test_title,
        save_to_disk=False,  # 测试时不保存
    )

    print(f"\n抽取成功: {result.success}")
    print(f"统计信息: {json.dumps(result.stats, ensure_ascii=False, indent=2)}")

    if result.investment_info:
        print("\n抽取结果:")
        info = result.investment_info.to_dict()

        # 显示 AI 总结
        if info.get("ai_summary"):
            print(f"\n【AI 总结】\n  {info['ai_summary']}")

        # 显示各维度信息
        for dim in ["facts", "numbers", "business", "industry_impact",
                    "management_claims", "uncertainties"]:
            items = info.get(dim, [])
            if items:
                print(f"\n【{dim}】")
                for item in items:
                    print(f"  - {item}")
