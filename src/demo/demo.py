import os
import json
import dashscope 
from dashscope  import Generation

# 方式一：直接写（仅用于本地测试）
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

prompt = """你是一名专业的美股投资分析师。

你的任务是：
基于最近 24 小时公开信息，总结 AI 行业的重要投资资讯。

【强制输出格式要求】
你必须严格按照以下 JSON 格式输出，不得输出任何多余文字，不得使用 Markdown，不得添加解释说明。

JSON 格式如下：

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
"""

# 调用模型生成内容
response = Generation.call(
    model="qwen-turbo-latest",
    prompt=prompt
)

# 获取模型生成的内容
raw_text = response.output.text

# 解析 JSON
try:
    data = json.loads(raw_text)
except json.JSONDecodeError as e:
    print("JSON 解析失败:", e)
    data = None  # 添加这行

if data:  # 添加判断
    print(data)

