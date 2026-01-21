"""
事件分析配置模块

该模块包含事件检测、聚类和摘要生成的相关配置参数。
"""

# 事件检测配置
EVENT_DETECTION_THRESHOLD = 0.5  # 事件检测相似度阈值（降低阈值提高灵敏度）
MIN_EVENT_SIZE = 2  # 最小事件规模（新闻数量）
MAX_EVENT_SIZE = 15  # 最大事件规模（增加上限容纳更多相关新闻）

# 聚类配置
CLUSTERING_ALGORITHM = "hdbscan"  # 聚类算法选择
MIN_CLUSTER_SIZE = 2  # 最小聚类大小
CLUSTER_SELECTION_EPSILON = 0.3  # 聚类选择参数（降低参数提高聚类灵敏度）

# 嵌入配置
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 文本嵌入模型
EMBEDDING_DIMENSION = 384  # 嵌入维度
MAX_SEQUENCE_LENGTH = 512  # 最大序列长度

# 摘要生成配置
SUMMARY_MAX_LENGTH = 200  # 摘要最大长度
SUMMARY_MIN_LENGTH = 50  # 摘要最小长度