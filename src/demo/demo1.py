import os
import json
import logging
import dashscope 
from dashscope  import Generation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置 API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    logger.warning("未设置 DASHSCOPE_API_KEY 环境变量")


def generate_news_json():
    """
    生成投资资讯结构化 JSON
    """
    logger.info("开始 Day 2：生成投资资讯 JSON")

    prompt = """
你是一名专业的美股投资分析师。

你的任务是：
基于最近 24 小时公开信息，总结 AI 行业的重要投资资讯。

【强制输出格式要求】
你必须严格按照以下 JSON 格式输出，不得输出任何多余文字，不得使用 Markdown，不得添加解释说明。

{
  "date": "YYYY-MM-DD",
  "source": "AI Investment Daily",
  "news": [
    {
      "title": "资讯标题",
      "summary": "不超过 100 字的摘要",
      "source": "Reuters / Bloomberg / 官方公告",
      "publish_time": "YYYY-MM-DD HH:mm",
      "related_companies": ["公司名1", "公司名2"],
      "investment_signal": "利好 / 中性 / 利空"
    }
  ]
}

【内容约束】
- news 数组固定 3 条
- summary 必须是完整中文句子
- investment_signal 只能是：利好 / 中性 / 利空
- 如果无法确认是最近 24 小时新闻，请返回空数组
"""

    try:
        logger.debug("调用 Generation API...")
        response = Generation.call(
            model="qwen-turbo-latest",
            prompt=prompt
        )
        logger.info("API 请求成功")
    except Exception as e:
        logger.error(f"API 请求失败: {e}")
        raise RuntimeError(f"Day2 API 调用失败: {e}")

    raw_text = response.output.text
    logger.debug(f"原始响应文本长度: {len(raw_text)}")

    try:
        news_json = json.loads(raw_text)
        logger.info(f"Day 2 JSON 解析成功，获取 {len(news_json.get('news', []))} 条资讯")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败，原始文本: {raw_text[:200]}...")
        raise RuntimeError(f"Day2 JSON 解析失败: {e}")

    return news_json


def generate_article_json(news_json):
    """
    基于  news_json 生成公众号文章结构 JSON
    """
    logger.info("开始 Day 3：生成公众号文章结构 JSON")

    prompt = f"""
你是一名专业的美股投资内容编辑。

以下是已经整理好的真实投资资讯（JSON），这是你唯一可以使用的信息来源：

{json.dumps(news_json, ensure_ascii=False)}

你的任务是：
基于上述资讯，生成一篇适合发布在微信公众号的投资分析文章结构。

【强制输出要求】
- 你必须严格按照以下 JSON 格式输出
- 不得输出任何解释性文字
- 不得引入输入 JSON 以外的事实或观点
- 不得使用 Markdown

{{
  "title": "",
  "lead": "",
  "sections": [
    {{
      "heading": "",
      "content": ""
    }}
  ],
  "risk_warning": "",
  "conclusion": ""
}}

【内容约束】
- sections 数组固定 3 个
- 每段 content 不超过 300 字
- 语气专业、理性、偏投资分析
- 禁止使用营销性词语
"""

    try:
        logger.debug("调用 Generation API...")
        response = Generation.call(
            model="qwen-plus",
            prompt=prompt
        )
        logger.info("API 请求成功")
    except Exception as e:
        logger.error(f"API 请求失败: {e}")
        raise RuntimeError(f"Day3 API 调用失败: {e}")

    raw_text = response.output.text
    logger.debug(f"原始响应文本长度: {len(raw_text)}")

    try:
        article_json = json.loads(raw_text)
        logger.info(f"Day 3 JSON 解析成功，生成文章标题: {article_json.get('title', '无标题')}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败，原始文本: {raw_text[:200]}...")
        raise RuntimeError(f"Day3 JSON 解析失败: {e}")

    return article_json


def main():
    logger.info("="*50)
    logger.info("开始 AI 投资管道流程")
    logger.info("="*50)
    
    try:
        news_json = generate_news_json()
        print("\n" + "="*50)
        print("Day 2 - 投资资讯 JSON：")
        print("="*50)
        print(json.dumps(news_json, ensure_ascii=False, indent=2))

        if not news_json.get("news"):
            logger.warning("未获取到有效的最新资讯，终止流程")
            return

        article_json = generate_article_json(news_json)
        print("\n" + "="*50)
        print("Day 3 - 公众号文章结构 JSON：")
        print("="*50)
        print(json.dumps(article_json, ensure_ascii=False, indent=2))
        
        logger.info("="*50)
        logger.info("流程完成成功")
        logger.info("="*50)
        
    except RuntimeError as e:
        logger.error(f"流程执行失败: {e}")
        raise
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        raise


if __name__ == "__main__":
    main()
