# 项目结构说明

## 目录树

```
ai-invest-news/
├── src/                                    # 主源代码目录
│   ├── __init__.py                        # Python包初始化
│   ├── main.py                            # 程序入口点 - 7步流程编排
│   │
│   ├── demo/                              # 演示模块 (可选)
│   │   ├── __init__.py
│   │   ├── demo1.py                       # 演示脚本1
│   │   └── demo2.py                       # 演示脚本2
│   │
│   ├── search/                            # 搜索模块 - RSS抓取和预处理
│   │   ├── __init__.py
│   │   ├── rss_config.py                 # 配置文件
│   │   │   ├── RSS_SOURCES               # 50+个RSS源列表
│   │   │   ├── SEARCH_HOURS              # 搜索时间范围(默认24小时)
│   │   │   ├── MAX_ITEMS_PER_SOURCE      # 每源最大条数(默认20)
│   │   │   ├── MAX_NORMALIZED_ITEMS      # 规范化最大条数(默认30)
│   │   │   └── TOP_K_SELECT              # 最终选择数(默认5)
│   │   │
│   │   ├── search_pipeline.py            # 搜索主流程
│   │   │   └── search_recent_ai_news()   # 从RSS源搜索新闻
│   │   │       ├── 时间过滤(24小时范围)
│   │   │       ├── 解析RSS源
│   │   │       ├── 每源限制条数(20)
│   │   │       └── 返回: (新闻列表, 统计信息)
│   │   │
│   │   └── search_result_process.py      # 搜索结果处理
│   │       ├── normalize_news()          # 规范化(验证、清理、限制条数)
│   │       │   ├── validate_news_item()  # 验证单条新闻
│   │       │   └── 返回: (规范化列表, 统计)
│   │       │
│   │       ├── deduplicate_news()        # 去重(基于title+url)
│   │       │   └── 返回: (去重列表, 统计)
│   │       │
│   │       ├── merge_similar_news()      # 合并相似(词重叠度>0.6)
│   │       │   └── 返回: (合并列表, 统计)
│   │       │
│   │       └── process_search_results()  # 完整流程: 去重→合并
│   │           └── 返回: (处理列表, 统计)
│   │
│   ├── selector/                          # 筛选模块 - 评分和选择
│   │   ├── __init__.py
│   │   ├── selector_config.py            # 筛选配置(暂未使用)
│   │   │
│   │   └── news_selector.py              # 新闻评分和选择
│   │       ├── EVENT_RULES               # 投资事件定义和权重
│   │       │   ├── earnings: +3.0分
│   │       │   ├── funding: +2.5分
│   │       │   ├── acquisition: +2.5分
│   │       │   ├── chip_supply: +2.5分
│   │       │   ├── product_commercial: +2.0分
│   │       │   └── regulation: +2.0分
│   │       │
│   │       ├── IMPORTANT_COMPANIES      # 重点公司列表
│   │       │   └── 10家重点公司: +1.5分
│   │       │
│   │       ├── PR_PATTERNS               # PR营销识别
│   │       │   └── 匹配时: -2.0分
│   │       │
│   │       ├── OPINION_PATTERNS          # 观点文章识别
│   │       │   └── 匹配时: -1.5分
│   │       │
│   │       ├── _score_news()             # 评分单条新闻
│   │       │   ├── 事件匹配评分
│   │       │   ├── 公司加权
│   │       │   ├── 可量化信息检测
│   │       │   ├── 内容长度权重
│   │       │   ├── PR/观点过滤
│   │       │   └── 返回分数 0.0-10.0
│   │       │
│   │       └── news_select()             # 完整选择流程
│   │           ├── 步骤1: 质量评分(所有新闻)
│   │           ├── 步骤2: 排序(按分数降序)
│   │           ├── 步骤3: 选择(前k条,分数>0)
│   │           └── 返回: (选中列表, 统计信息)
│   │
│   └── generation/                        # 生成模块 - AI分析
│       ├── __init__.py
│       ├── summary_prompt_builder.py    # 构建AI提示词
│       │   └── build_prompt()           # 组装新闻为提示文本
│       │
│       └── news_summary_generation.py   # AI摘要生成(预留)
│           └── generate_ai_news()       # 调用LLM进行分析
│
├── venv/                                   # Python虚拟环境
│
├── pyproject.toml                          # 项目配置
│   ├── [project]: 项目元数据
│   ├── [dependencies]: 运行依赖
│   ├── [optional-dependencies]: 可选依赖(dev, docs)
│   └── [tool.xxx]: 工具配置(black, isort, mypy等)
│
├── .gitignore                              # Git忽略规则
│   ├── __pycache__/, *.pyc
│   ├── venv/, .venv
│   ├── .env
│   ├── .idea/, .vscode/
│   ├── build/, dist/
│   └── *.egg-info/
│
├── README.md                               # 项目文档
│
└── PROJECT_STRUCTURE.md                    # 本文件
```

## 关键数据流

### 完整处理流程 (main.py)

```
第1步: 搜索阶段
  input:  时间范围(小时)
  process: search_recent_ai_news()
  output: (原始新闻列表, 搜索统计)
          原始新闻数: 100-500条

第2步: 规范化
  input:  原始新闻列表
  process: normalize_news()
  output: (规范化列表, 规范化统计)
          规范化数: 30条(MAX_NORMALIZED_ITEMS)

第3步: 流程处理(去重→合并)
  input:  规范化列表
  process: process_search_results()
           ├─ deduplicate_news()    # 去重
           └─ merge_similar_news()  # 合并
  output: (处理后列表, 处理统计)
          处理后数: 20-30条

第4步: 新闻选择(评分→排序→选择)
  input:  处理后列表
  process: news_select()
           ├─ _score_news()        # 每条评分
           ├─ sort()               # 排序
           └─ filter & select()    # 选择前k
  output: (选中列表, 选择统计)
          选中数: 5条(TOP_K_SELECT)

第5步: 提示词构建
  input:  选中列表(5条)
  process: build_prompt()
  output: AI提示词文本

第6步: AI分析
  input:  提示词文本
  process: Generation.call(DashScope)
  output: AI响应(JSON格式)

第7步: 响应解析
  input:  AI响应
  process: json.loads()
  output: 最终分析结果 + 全流程统计
```

## 统计信息分布

```
【搜索阶段统计】
  源分类:
    ✓ 有效源(有未过期新闻)
    ⏱ 过期源(结果都过期)
    ✗ 无效源(无结果)
  各源详情:
    - 总找到/有效获取/跳过(无时间)/跳过(过期)

【规范化阶段统计】
  - 各源最终条数

【流程处理统计】
  去重:
    - 输入/移除/保留
  合并:
    - 输入/输出/合并数

【选择统计】
  - 输入/输出/平均分数/分数分布
```

## 配置参数一览

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `SEARCH_HOURS` | `src/search/rss_config.py` | 24 | 搜索时间范围(小时) |
| `MAX_ITEMS_PER_SOURCE` | `src/search/rss_config.py` | 20 | 每源最大条数 |
| `MAX_NORMALIZED_ITEMS` | `src/search/rss_config.py` | 30 | 规范化最大条数 |
| `TOP_K_SELECT` | `src/search/rss_config.py` | 5 | 最终选择数量 |
| `SIMILARITY_THRESHOLD` | `src/search/search_result_process.py` | 0.6 | 合并相似度阈值 |
| `REQUIRED_FIELDS` | `src/search/search_result_process.py` | 5 | 必需字段个数 |

## 导入约定

### 相对导入 (在包内)
```python
from .rss_config import RSS_SOURCES
from .search_result_process import deduplicate_news
```

### 绝对导入 (main.py)
```python
from search.search_pipeline import search_recent_ai_news
from selector.news_selector import news_select
from generation.summary_prompt_builder import build_prompt
```

## 日志输出

每个模块包含详细的日志:
- 时间戳: `2026-01-20 09:35:00`
- 级别: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- 内容: 处理进度、统计数据、错误信息

## 环境变量

```bash
# .env 文件
DASHSCOPE_API_KEY=sk_xxx...  # 阿里云API密钥
```

## 运行入口

```bash
# 从项目根目录运行
cd src
python main.py
```

---
**文档更新**: 2026-01-20
