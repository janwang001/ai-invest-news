"""
Decision Layer 配置参数
事件决策层的配置参数，包括重要性阈值和信号分类规则
"""

# 事件重要性阈值配置
IMPORTANCE_THRESHOLDS = {
    "high": {
        "min_news": 3,
        "min_sources": 2,
        "min_score": 0.6,
    },
    "medium": {
        "min_news": 2,
        "min_sources": 1,
        "min_score": 0.3,
    }
}

# 正面信号关键词集合
POSITIVE_SIGNALS = {
    "earnings",
    "revenue", 
    "profit",
    "funding",
    "investment",
    "contract",
    "partnership",
    "product_launch",
}

# 风险信号关键词集合
RISK_SIGNALS = {
    "regulation",
    "ban",
    "lawsuit",
    "antitrust",
    "investigation",
    "security",
    "data_leak",
    "delay",
}