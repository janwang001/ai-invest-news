#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 webapp_exporter 流程

使用 AI 生成的 mock 数据进行测试，数据日期设为一年前（2025-01-21）
"""

import json
import logging
import os
import sys

# 添加 src 目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from webapp_exporter import export_to_webapp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_data() -> dict:
    """
    生成 mock 数据用于测试

    数据日期设为一年前（2025-01-21）

    Returns:
        dict: 模拟的分析结果
    """
    # 使用一年前的日期
    mock_date = "2025-01-21"

    mock_result = {
        "date": mock_date,
        "news": [
            {
                "title": "[Mock] OpenAI发布GPT-5预览版，多模态能力大幅提升",
                "url": "https://mock.example.com/news/1",
                "source": "TechCrunch",
                "published_at": f"{mock_date}T14:30:00Z",
                "ai_summary": "OpenAI正式发布GPT-5预览版，新版本在多模态理解、推理能力和代码生成方面有显著提升，响应速度提高50%。",
                "investment_info": {
                    "core_thesis": "大模型技术持续迭代，OpenAI保持行业领先地位",
                    "market_impact": "利好AI应用开发商和云计算厂商",
                    "risk_factors": ["竞争对手追赶速度加快", "商业化定价策略不确定"],
                    "time_horizon": "短期（3-6个月）",
                    "related_tickers": ["MSFT", "NVDA", "GOOGL"],
                    "confidence_level": "高"
                }
            },
            {
                "title": "[Mock] 英伟达H200芯片供不应求，产能扩张计划提前",
                "url": "https://mock.example.com/news/2",
                "source": "Reuters",
                "published_at": f"{mock_date}T10:15:00Z",
                "ai_summary": "英伟达H200芯片需求远超预期，公司宣布与台积电合作提前扩产，预计2025年Q2产能将翻倍。",
                "investment_info": {
                    "core_thesis": "AI算力需求持续爆发，英伟达硬件霸主地位稳固",
                    "market_impact": "利好半导体产业链，尤其是AI芯片和先进封装",
                    "risk_factors": ["地缘政治风险", "下游客户资本开支波动"],
                    "time_horizon": "中期（6-12个月）",
                    "related_tickers": ["NVDA", "TSM", "ASML"],
                    "confidence_level": "高"
                }
            },
            {
                "title": "[Mock] 特斯拉FSD V13正式推送，完全自动驾驶迈出关键一步",
                "url": "https://mock.example.com/news/3",
                "source": "Electrek",
                "published_at": f"{mock_date}T08:00:00Z",
                "ai_summary": "特斯拉开始向北美用户推送FSD V13版本，新版本采用端到端神经网络，在复杂路况下表现显著提升。",
                "investment_info": {
                    "core_thesis": "自动驾驶技术逐步成熟，特斯拉AI战略加速落地",
                    "market_impact": "利好自动驾驶产业链，特斯拉估值逻辑或将重塑",
                    "risk_factors": ["监管审批进度不确定", "安全事故风险"],
                    "time_horizon": "中长期（12-18个月）",
                    "related_tickers": ["TSLA", "MBLY", "QCOM"],
                    "confidence_level": "中"
                }
            },
            {
                "title": "[Mock] 字节跳动豆包大模型日活突破1亿",
                "url": "https://mock.example.com/news/4",
                "source": "36氪",
                "published_at": f"{mock_date}T16:00:00Z",
                "ai_summary": "字节跳动旗下AI助手豆包日活用户突破1亿，成为国内增速最快的AI应用，C端变现模式逐步清晰。",
                "investment_info": {
                    "core_thesis": "中国AI应用市场快速增长，字节跳动凭借流量优势领跑",
                    "market_impact": "加剧国内AI应用竞争，利好AI基础设施",
                    "risk_factors": ["用户增长可持续性待验证", "变现效率不确定"],
                    "time_horizon": "短期（3-6个月）",
                    "related_tickers": [],
                    "confidence_level": "中"
                }
            },
            {
                "title": "[Mock] 欧盟AI法案正式生效，全球AI监管进入新阶段",
                "url": "https://mock.example.com/news/5",
                "source": "BBC",
                "published_at": f"{mock_date}T12:00:00Z",
                "ai_summary": "欧盟《人工智能法案》正式生效，对高风险AI应用设立严格合规要求，全球AI企业面临监管新挑战。",
                "investment_info": {
                    "core_thesis": "AI监管趋严是长期趋势，合规成本将成为竞争壁垒",
                    "market_impact": "短期利空AI应用商，长期利好合规能力强的大厂",
                    "risk_factors": ["监管细则执行力度不确定", "可能引发其他地区跟进"],
                    "time_horizon": "长期（18-24个月）",
                    "related_tickers": ["META", "GOOGL", "MSFT"],
                    "confidence_level": "中"
                }
            }
        ],
        "events": [
            {
                "representative_title": "[Mock] OpenAI发布GPT-5预览版",
                "summary": "OpenAI正式发布GPT-5预览版，在多模态理解、长上下文处理和推理能力方面实现重大突破。新版本响应速度提高50%，代码生成能力显著增强，有望推动AI应用开发进入新阶段。",
                "news_count": 5,
                "sources": ["TechCrunch", "The Verge", "Wired"],
                "companies": ["OpenAI", "Microsoft"],
                "news_indices": [0],
                "decision": {
                    "importance": "high",
                    "signal": "positive",
                    "action": "buy",
                    "reasoning": "GPT-5是AI领域的标志性进展，将加速AI应用落地，利好微软等OpenAI投资方。"
                }
            },
            {
                "representative_title": "[Mock] 英伟达AI芯片需求持续火爆",
                "summary": "英伟达H200芯片市场需求远超预期，公司与台积电合作提前扩产计划。数据中心客户排队抢购，交付周期延长至6个月以上，AI算力供需紧张局面短期难以缓解。",
                "news_count": 4,
                "sources": ["Reuters", "Bloomberg", "WSJ"],
                "companies": ["NVIDIA", "TSMC", "AMD"],
                "news_indices": [1],
                "decision": {
                    "importance": "high",
                    "signal": "positive",
                    "action": "hold",
                    "reasoning": "AI芯片需求旺盛确认行业趋势，但当前估值已充分反映乐观预期。"
                }
            },
            {
                "representative_title": "[Mock] 特斯拉FSD V13技术突破",
                "summary": "特斯拉FSD V13版本开始向北美用户推送，采用全新端到端神经网络架构，在城市复杂路况下的表现显著提升。分析师认为这是特斯拉向完全自动驾驶迈出的关键一步。",
                "news_count": 3,
                "sources": ["Electrek", "InsideEVs"],
                "companies": ["Tesla", "Mobileye"],
                "news_indices": [2],
                "decision": {
                    "importance": "medium",
                    "signal": "positive",
                    "action": "watch",
                    "reasoning": "技术进步明显，但监管审批和大规模商用仍需时间验证。"
                }
            },
            {
                "representative_title": "[Mock] 中国AI应用市场爆发式增长",
                "summary": "字节跳动豆包日活突破1亿，成为国内增速最快的AI应用。百度文心一言、阿里通义千问也在加速追赶，中国AI应用市场竞争进入白热化阶段。",
                "news_count": 4,
                "sources": ["36氪", "虎嗅", "界面新闻"],
                "companies": ["字节跳动", "百度", "阿里巴巴"],
                "news_indices": [3],
                "decision": {
                    "importance": "medium",
                    "signal": "neutral",
                    "action": "watch",
                    "reasoning": "用户增长迅速但变现模式尚不清晰，需关注商业化进展。"
                }
            },
            {
                "representative_title": "[Mock] 全球AI监管框架逐步成形",
                "summary": "欧盟《人工智能法案》正式生效，对高风险AI应用设立严格合规要求。美国、中国等主要经济体也在加速AI监管立法，全球AI行业进入规范发展新阶段。",
                "news_count": 3,
                "sources": ["BBC", "FT", "Reuters"],
                "companies": ["Meta", "Google", "Microsoft"],
                "news_indices": [4],
                "decision": {
                    "importance": "medium",
                    "signal": "negative",
                    "action": "watch",
                    "reasoning": "监管趋严短期增加合规成本，但长期有利于行业健康发展。"
                }
            }
        ]
    }

    return mock_result


def test_exporter():
    """测试 exporter 流程"""
    logger.info("=" * 60)
    logger.info("开始测试 webapp_exporter 流程")
    logger.info("=" * 60)

    # 生成 mock 数据
    logger.info("生成 mock 数据...")
    mock_result = generate_mock_data()
    logger.info(f"Mock 数据日期: {mock_result['date']}")
    logger.info(f"Mock 新闻数量: {len(mock_result['news'])}")
    logger.info(f"Mock 事件数量: {len(mock_result['events'])}")

    # 调用 exporter
    logger.info("\n调用 export_to_webapp...")
    export_result = export_to_webapp(mock_result)

    # 输出结果
    logger.info("\n" + "=" * 60)
    logger.info("导出结果")
    logger.info("=" * 60)
    print(json.dumps(export_result, ensure_ascii=False, indent=2))

    if export_result.get("success"):
        logger.info("\n✅ 导出成功！")
        logger.info(f"数据文件: {export_result.get('data_file')}")
        logger.info(f"索引文件: {export_result.get('index_file')}")

        # 读取并显示导出的数据文件内容
        data_file = export_result.get("data_file")
        if data_file:
            logger.info("\n" + "=" * 60)
            logger.info("导出的数据文件内容预览")
            logger.info("=" * 60)
            with open(data_file, "r", encoding="utf-8") as f:
                exported_data = json.load(f)
            print(json.dumps(exported_data, ensure_ascii=False, indent=2)[:2000])
            if len(json.dumps(exported_data, ensure_ascii=False, indent=2)) > 2000:
                print("\n... (内容过长，已截断)")

        # 读取并显示索引文件内容
        index_file = export_result.get("index_file")
        if index_file:
            logger.info("\n" + "=" * 60)
            logger.info("索引文件内容")
            logger.info("=" * 60)
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            print(json.dumps(index_data, ensure_ascii=False, indent=2))
    else:
        logger.error(f"\n❌ 导出失败: {export_result.get('error')}")

    return export_result


if __name__ == "__main__":
    test_exporter()
