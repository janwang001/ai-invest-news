# AI Investment News Analysis System

**Version 2.1.0** - Professional Investment Intelligence Platform

一个专业的投资新闻智能分析系统，集成了RSS订阅、自然语言处理和大语言模型(LLM)，提供投资级别的新闻聚合、筛选、分析和决策支持。

## 🆕 v2.1 新功能: 7大数据源精准监控

### 🎯 高敏感度数据源监控
实时监控7大高敏感度投资信号源，精准捕捉投资机会和风险：

| 数据源 | 监控内容 | 检查频率 |
|--------|----------|----------|
| **SEC EDGAR** | 8-K重大事件、Form D融资、S-1 IPO、13D/13G持股 | 5分钟 |
| **监管机构** | FTC反垄断、DOJ调查、EU Commission | 15分钟 |
| **大厂博客** | OpenAI、Google AI、Meta AI、Anthropic、NVIDIA、DeepMind | 30分钟 |
| **股价异动** | NVDA、AMD、TSM、MSFT、GOOGL、AMZN、META等16只AI股票 | 5分钟 |
| **CEO Twitter** 🆕 | @sama、@elonmusk、@satyanadella、@sundarpichai等8位 | 30分钟 |
| **GitHub爆款** 🆕 | OpenAI、Meta、Google等顶级组织的AI相关项目 | 60分钟 |
| **Hacker News** 🆕 | AI相关热门讨论（分数>50，评论>20） | 30分钟 |

### 🚨 3级警报优先级系统
| 优先级 | 触发条件 | 响应时间 |
|--------|----------|----------|
| **P0** | IPO注册、$100M+融资、收购、产品发布、股价>5%、刑事调查 | 立即推送 |
| **P1** | 8-K其他事件、Form D、技术博客、股价3-5% | 1小时汇总 |
| **P2** | 一般监控信息 | 每日汇总 |

### 📢 多渠道通知
- **控制台**: 实时显示警报
- **文件记录**: JSON格式持久化存储
- **Webhook**: 支持 Slack / 企业微信 / 钉钉

### 快速使用
```bash
# 测试模式（所有数据源）
python src/run_monitor.py --test

# 生产模式
python src/run_monitor.py

# 仅SEC和监管监控
python src/run_monitor.py --no-blog --no-stock --no-twitter --no-github --no-hn

# 带Slack通知
python src/run_monitor.py --webhook https://hooks.slack.com/xxx --webhook-platform slack

# 自定义时间范围
python src/run_monitor.py --twitter-hours 6 --github-days 3 --hn-hours 12

# 查看所有选项
python src/run_monitor.py --help
```

---

## ✨ 核心特性（v1.1 新增）

### 🎯 投资论点分析
- **看涨/看跌理由**：每条核心新闻提供3个具体的看涨和看跌理由
- **关键问题**：识别决定投资结果的核心不确定性
- **时间周期**：明确影响兑现的时间范围（即时/1-3月/6-12月/长期）
- **历史类比**：提供类似历史事件作为参考

### 📊 7维度投资评分卡
- **重要性**（0-10）：财务影响规模
- **紧迫性**（0-10）：时间敏感度
- **确信度**（0-10）：证据质量
- **竞争影响**（0-10）：竞争格局变化
- **风险**（0-10）：不确定性水平
- **创新度**（0-10）：技术/产品创新
- **执行力**（0-10）：可执行性
- **综合得分**（0-100）+ 投资评级（Strong Buy Signal / Monitor / Risk Alert / Pass）

### 🔥 智能优先级排序
- **3层级事件结构**：
  - Tier 1（高优先级）：综合得分 >= 70，最多3个事件，包含投资论点和风险收益分析
  - Tier 2（中等优先级）：综合得分 50-69，最多5个事件，精简格式
  - Tier 3（低优先级）：综合得分 < 50，最多3个事件，仅标题

### 🚨 今日重点关注（Executive Alerts）
- 自动识别 Top 3 行动项（按紧迫性 × 重要性排序）
- 每个警报包含：
  - 投资评级（⭐⭐⭐⭐⭐ or ⚠️⚠️⚠️）
  - 建议行动（具体操作指引）
  - 时间窗口（何时行动）
  - 风险等级 + 确信度

### ⚖️ 风险-收益评估
- 上行潜力可视化（🟢 0-5 级）
- 下行风险可视化（🔴 0-5 级）
- 风险调整收益判断（有利/中性/不利）

---

## 📋 系统流程（12步）

该系统通过以下工作流自动化投资新闻分析过程：

1. **搜索阶段** - 从86个RSS源抓取最新新闻（支持24小时时间范围过滤）
2. **规范化处理** - 验证、清理和统一新闻数据格式
3. **原文抓取** - 使用ArticleFetcher抓取网页原文
4. **流程处理** - 去重、合并相似新闻
5. **轻量化特征抽取** - 使用规则/正则提取高信号特征（不用LLM）
6. **智能筛选** - 基于投资事件、关键词和轻量化特征进行评分和排序
7. **投资信息抽取** - 使用LLM抽取6维度结构化投资信息 + 投资论点 🆕
7.5. **投资评分卡计算** - 7维度评分 + 综合得分 + 投资评级 🆕
8. **事件分析** - 新闻聚类和事件检测
9. **事件决策** - 重要性评估、信号分类和动作映射
10. **公众号文章生成** - 生成3层级投资报告（Executive Alerts + 投资论点 + 风险收益）🆕
11. **H5应用数据导出** - 导出JSON格式数据供移动端H5应用展示

## 🏗️ 项目结构

```
ai-invest-news/
├── src/
│   ├── __init__.py
│   ├── main.py                         # 主程序入口（12步流程）
│   ├── run_monitor.py                  # 🆕 精准监控命令行工具
│   ├── collectors/                     # 🆕 精准监控模块
│   │   ├── __init__.py
│   │   ├── sec_edgar_collector.py     # SEC EDGAR采集器
│   │   ├── regulatory_collector.py    # 监管机构采集器
│   │   ├── blog_collector.py          # 大厂博客采集器
│   │   ├── stock_monitor.py           # 股价异动监控器
│   │   ├── twitter_monitor.py         # 🆕 CEO Twitter监控器 (Nitter RSS)
│   │   ├── github_monitor.py          # 🆕 GitHub爆款项目监控器
│   │   ├── hackernews_monitor.py      # 🆕 Hacker News监控器
│   │   ├── alert_system.py            # P0/P1/P2警报系统
│   │   ├── notifier.py                # 通知推送系统
│   │   └── precision_monitor.py       # 统一调度器
│   ├── demo/                           # Demo模块
│   │   ├── __init__.py
│   │   ├── demo.py
│   │   └── demo1.py
│   ├── search/                         # 搜索模块 - RSS抓取和结果预处理
│   │   ├── __init__.py
│   │   ├── rss_config.py              # RSS源配置和参数设置
│   │   ├── search_pipeline.py         # 搜索主流程
│   │   ├── search_pipeline_v2.py      # 并发搜索流程
│   │   ├── concurrent_rss_fetcher.py  # 并发RSS抓取器
│   │   └── search_result_process.py   # 搜索结果处理(去重、合并)
│   ├── selector/                       # 筛选模块 - 新闻选择和评分
│   │   ├── __init__.py
│   │   ├── selector_config.py         # 筛选配置
│   │   ├── news_selector.py           # 新闻评分和选择逻辑（支持轻量化特征）
│   │   └── investment_scorer.py       # 🆕 投资评分卡（7维度评分）
│   ├── event/                         # 事件分析模块 - 新闻事件检测和聚类
│   │   ├── __init__.py
│   │   ├── event_config.py           # 事件分析配置
│   │   ├── embedding.py              # 文本嵌入功能
│   │   ├── clustering.py             # 新闻聚类功能
│   │   ├── event_summary.py          # 事件摘要生成
│   │   ├── event_pipeline.py         # 事件分析流程管理
│   │   └── decision/                 # 事件决策模块
│   │       ├── __init__.py
│   │       ├── decision_config.py   # 决策配置
│   │       ├── importance_evaluator.py # 重要性评估
│   │       ├── signal_classifier.py   # 信号分类
│   │       ├── action_mapper.py       # 动作映射
│   │       └── decision_pipeline.py  # 决策流程
│   ├── content/                        # 公众号文章生成模块
│   │   ├── __init__.py
│   │   ├── article_schema.py          # 文章数据结构定义
│   │   ├── article_builder.py         # 文章构建逻辑
│   │   └── article_renderer.py        # 文章渲染器
│   ├── fetch/                          # 文章抓取与特征抽取模块
│   │   ├── __init__.py
│   │   ├── fetch_config.py            # 抓取配置（超时、长度限制等）
│   │   ├── article_fetcher.py         # 原文抓取（HTML → 正文）
│   │   ├── light_features_extractor.py # 轻量化特征抽取（不用LLM）
│   │   └── investment_extractor.py    # 投资信息抽取（用LLM）
│   ├── webapp_exporter.py              # H5应用数据导出器
│   ├── dev_server.py                   # H5应用本地开发服务器
│   └── venv/                           # Python虚拟环境
├── tests/                              # 测试目录
│   ├── __init__.py                     # 测试包初始化
│   ├── conftest.py                     # pytest配置
│   ├── test_event_integration.py       # Event模块集成测试
│   ├── test_exporter.py                # H5导出器测试脚本
│   ├── test_full_flow.py               # 全流程测试脚本（Mock 200条数据）
│   ├── test_phase1_integration.py      # Phase 1集成测试
│   ├── test_week1_integration.py       # 🆕 Week 1精准监控测试
│   └── test_week2_integration.py       # 🆕 Week 2精准监控测试
├── webapp/                             # H5移动端应用
│   ├── index.html                      # 主页（文章列表）
│   ├── detail.html                     # 详情页（事件列表）
│   ├── event.html                      # 事件详情页
│   ├── css/
│   │   └── style.css                   # 样式文件
│   ├── js/
│   │   ├── app.js                      # 主页逻辑
│   │   ├── detail.js                   # 详情页逻辑
│   │   └── event.js                    # 事件详情页逻辑
│   └── data/                           # 数据目录（动态生成）
│       ├── index.json                  # 索引文件
│       └── YYYYMMDD.json               # 每日数据文件
├── raw_data/                           # 原始数据存储目录
│   └── YYYYMMDD/                       # 按日期分目录存储
├── pyproject.toml                      # 项目配置文件
├── README.md                           # 项目说明
└── .gitignore                          # Git忽略文件配置
```

## 🚀 快速开始

### 前置要求

- Python 3.9 或更高版本
- pip 包管理器
- 阿里云 DashScope API 密钥（用于Qwen模型）

### 安装

1. **克隆项目**
```bash
git clone https://github.com/janwang001/ai-invest-news.git
cd ai-invest-news
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -e .
# 或安装开发依赖
pip install -e ".[dev]"
```

4. **配置环境变量**
```bash
# 创建 .env 文件
echo "DASHSCOPE_API_KEY=your_api_key_here" > .env
```

### 使用

**运行主程序**
```bash
cd src
python main.py
```

**启动H5应用预览服务器**
```bash
cd src
python dev_server.py
# 访问 http://localhost:8080 查看H5应用
```

**运行测试**
```bash
pytest
```

**运行特定模块的测试**
```bash
python -m src.search.search_pipeline
python -m src.selector.news_selector
```

## 📊 功能模块详解

### 1. 搜索模块 (`src/search/`)

**功能**: 从多个RSS源抓取新闻数据，支持串行和并发两种模式

**主要配置** (`rss_config.py`):
- `RSS_SOURCES`: RSS源列表（50+个AI/科技/投资相关源）
- `SEARCH_HOURS`: 搜索时间范围，默认24小时
- `MAX_ITEMS_PER_SOURCE`: 每个源最大条数，默认20
- `MAX_NORMALIZED_ITEMS`: 规范化输出最大条数，默认30
- `USE_CONCURRENT`: 是否启用并发模式，默认True
- `MAX_CONCURRENT`: 并发数，默认10（推荐配置，实现8.38倍加速）

**关键函数**:
- `search_recent_ai_news()`: 从RSS源搜索新闻（支持并发模式）
- `normalize_news()`: 规范化新闻格式
- `deduplicate_news()`: 去重处理
- `merge_similar_news()`: 合并相似新闻

**并发抓取优化** (v0.3.0新增):
- **性能提升**: 并发模式相比串行模式实现88.1%性能提升
- **加速比**: 8.38倍（并发数=10）
- **资源消耗**: CPU仅28.8%，内存增量0.2%，系统资源健康
- **配置灵活**: 支持串行/并发模式切换，并发数可配置
- **向后兼容**: 完全兼容原有代码，一行配置即可切换

### 2. 筛选模块 (`src/selector/`)

**功能**: 评分、排序和选择高价值新闻

**主要配置** (`selector_config.py`):
- `TOP_K_SELECT`: 最终选择的新闻数量，默认150（增加数量以丰富内容）

**评分规则**:
- **事件评分**: 
  - Earnings/Revenue: +3.0分
  - Funding/Investment: +2.5分
  - M&A/Acquisition: +2.5分
  - GPU/Chip: +2.5分
  - Product Launch: +2.0分
  - Regulation: +2.0分

- **公司加权**: 重点公司(NVIDIA, OpenAI等): +1.5分
- **可量化信息**: 包含数字/金额: +1.0分
- **PR过滤**: 营销文案降权: -2.0分
- **观点文章**: 降权: -1.5分
- **内容长度**: 
  - <60字: -1.0分
  - >300字: +0.5分

- **轻量化特征评分（新增）**:
  - 内容长度达标（≥1000字符）: +0.5分
  - 包含数字信息: +1.0分
  - 包含高管/官方引用: +1.5分
  - 提及重点公司: 每个+0.5分（最多+2分）
  - 包含投资信号词: 每个+0.3分（最多+2分）

### 3. 内容生成模块 (`src/content/`)

**功能**: 公众号文章生成 - 将分析结果转换为适合公众号发布的投资资讯文章

**主要功能**:
- **文章结构定义**: 使用dataclass定义公众号文章的数据结构
- **文章构建器**: 对事件进行排序、分类和信息裁剪
- **Markdown渲染器**: 将文章渲染为公众号友好的Markdown格式
- **重要文章列表**: 在关键信息拆解部分显示重要性排名前5的文章标题和超链接

**核心组件**:
- **ArticleSchema**: 定义文章和事件的数据结构（包含news_list字段存储新闻列表）
- **ArticleBuilder**: 负责事件排序、分类和去重表达
- **MarkdownRenderer**: 负责输出Markdown格式的文章，支持重要文章排序展示

**重要文章排序规则**:
- 基于新闻来源权威性评分（Financial Times、Bloomberg等权威来源得分更高）
- 基于发布时间新鲜度（24小时内发布的新闻额外加分）
- 最多展示5篇重要文章，包含标题、链接和来源

**文章结构**:
```
# 今日 AI 投资要点速览 | 日期

## 一、今日核心事件（3–5 条）
  - 事件概述
  - 关键信息拆解（含重要文章列表）
  - 投资信号解读
  - 潜在风险
## 二、市场信号汇总
## 三、今日值得持续关注的方向
```

### 4. 事件分析模块 (`src/event/`)

**功能**: 对新闻进行事件检测、聚类和摘要生成，支持智能聚类策略和事件有效性判断

**主要配置** (`event_config.py`):
- `EVENT_DETECTION_THRESHOLD = 0.5` - 事件检测相似度阈值（降低阈值提高灵敏度）
- `MIN_EVENT_SIZE = 2` - 最小事件规模（新闻数量）
- `CLUSTERING_ALGORITHM = "hdbscan"` - 聚类算法选择
- `EMBEDDING_MODEL = "all-MiniLM-L6-v2"` - 文本嵌入模型
- `SUMMARY_MAX_LENGTH = 200` - 摘要最大长度

**关键函数**:
- `EventPipeline.analyze_events()`: 完整的事件分析流程
- `TextEmbedder.embed_news()`: 新闻文本嵌入（支持结构化提示和缓存优化）
- `NewsClusterer.cluster_news()`: 智能聚类分析（支持算法自适应选择）
- `EventSummarizer.summarize_events()`: 事件摘要生成

**事件分析流程**:
1. **文本嵌入**: 将新闻标题和内容转换为向量表示，使用结构化提示优化语义理解
2. **智能聚类**: 根据数据规模自适应选择聚类算法
3. **事件检测**: 识别具有相似主题的新闻组
4. **有效性判断**: 基于公司数量、信号类型和投资分数进行事件过滤
5. **摘要生成**: 为每个事件生成结构化摘要
6. **统计输出**: 提供详细的流程统计信息

**聚类优化特性**:
- **智能算法选择**: 小规模数据（≤10条）使用贪心余弦聚类，大规模数据使用HDBSCAN
- **事件有效性判断**: 确保每个事件至少涉及1家公司、1个信号类型，平均投资分数≥0.3
- **结构化嵌入提示**: 使用标题、内容、信号、公司的结构化格式优化语义理解
- **嵌入缓存机制**: 支持嵌入结果缓存，节省50%+成本
- **批量处理优化**: 优化大规模数据处理性能

**事件有效性标准**:
- ✅ 公司数量 ≥ 1
- ✅ 信号类型 ≥ 1  
- ✅ 平均投资分数 ≥ 0.3
- ✅ 事件规模 ≥ MIN_EVENT_SIZE

### 5. 事件决策模块 (`src/event/decision/`)

**功能**: 对事件进行重要性评估、信号分类和投资动作映射，提供可解释的决策支持

**在主流程中的位置**:
```
news
 → normalize（规范化）
 → AI summary（AI摘要生成）
 → selector（High / Medium）
 → event（聚类 + summary）
 → decision（重要性 + 信号 + 动作）
 → content（公众号文章生成）
```

**决策层架构**:
```
event
 → decision
   ├── importance (High / Medium / Low)
   ├── signal (Positive / Neutral / Risk)
   └── action (Watch / Hold / Avoid)
```

**核心职责拆分**:
| 层 | 输入 | 输出 |
|----|------|------|
| Importance | event | High / Medium / Low |
| Signal | event | Positive / Neutral / Risk |
| Action | importance + signal | Watch / Hold / Avoid |

**核心组件**:
- **重要性评估器** (`EventImportanceEvaluator`): 基于新闻数量、来源多样性和投资分数判断事件重要性
- **信号分类器** (`EventSignalClassifier`): 根据信号关键词判断市场信号方向
- **动作映射器** (`EventActionMapper`): 结合重要性和信号生成投资动作
- **决策流水线** (`EventDecisionPipeline`): 整合所有决策组件的统一接口

**决策配置** (`decision_config.py`):
- `IMPORTANCE_THRESHOLDS`: 重要性判断阈值配置
- `POSITIVE_SIGNALS`: 正面信号关键词集合
- `RISK_SIGNALS`: 风险信号关键词集合

**决策逻辑**:
- **重要性判断**: 基于新闻数量、来源数量和平均投资分数
- **信号分类**: 分析事件中的正面和风险信号关键词
- **动作映射**: 重要性 + 信号 → 投资动作的规则映射

**集成特性**:
- **主流程集成**: 在事件分析之后，AI摘要生成之前执行
- **异常处理**: 决策失败不影响后续流程，继续使用原始事件
- **详细统计**: 提供完整的决策成功率、分布统计和错误信息
- **日志记录**: 每个步骤都有清晰的日志输出

**决策输出示例**:
```json
{
  "event_id": "evt_20260120_03",
  "news_count": 4,
  "sources": ["Reuters", "Bloomberg"],
  "summary": "NVIDIA announces new AI GPU platform with major cloud partners.",
  "decision": {
    "importance": "High",
    "signal": "Positive", 
    "action": "Hold"
  }
}
```

**统计信息输出**:
```python
# 决策统计信息
decision_stats = {
    "total_events": 5,           # 总事件数量
    "success_count": 4,          # 成功决策的事件数量
    "error_count": 1,           # 决策失败的事件数量
    "success_rate": 0.8,        # 决策成功率
    "importance_distribution": { # 重要性分布
        "High": 2,
        "Medium": 1,
        "Low": 1
    },
    "signal_distribution": {     # 信号分布
        "Positive": 3,
        "Neutral": 1,
        "Risk": 0
    },
    "action_distribution": {    # 动作分布
        "Watch": 1,
        "Hold": 2,
        "Avoid": 1
    },
    "errors": ["事件ID: evt_20260120_02 - 缺少必要字段"]
}
```

### 6. 抓取与特征抽取模块 (`src/fetch/`)

**功能**: 文章原文抓取、轻量化特征抽取和投资信息抽取

**模块组成**:
- **article_fetcher.py**: 原文抓取器（HTML → 正文）
- **light_features_extractor.py**: 轻量化特征抽取器（不用LLM）
- **investment_extractor.py**: 投资信息抽取器（使用LLM）
- **fetch_config.py**: 统一配置管理

**集成时机**:
- **原文抓取（第三步）**: 在规范化之后立即抓取，供后续所有步骤使用
- **投资信息抽取（第七步）**: 在新闻选择之后，对高价值新闻进行LLM抽取

**article_fetcher 功能**:
- **原文抓取**: 对筛选出的高价值新闻URL进行原文抓取
- **正文提取**: 使用readability-lxml（Firefox阅读模式算法）提取干净正文
- **噪声清洗**: 自动过滤cookie提示、广告、订阅弹窗等噪声内容
- **长度控制**: 限制输出长度（默认6000字符），优化token消耗
- **本地存储**: 按日期分目录存储到`raw_data/YYYYMMDD/`
- **统计信息**: 提供详细的抓取统计（原始大小、清洗后长度、耗时等）

**light_features_extractor 功能**:
- **设计目的**: 给selector提供更多判断维度，而不是生成内容
- **技术特点**: 不使用LLM，只用规则/正则/BeautifulSoup
- **执行速度**: 快速、成本低，提取高信号特征

**输出结构** (`LightArticleFeatures`):
```python
LightArticleFeatures = {
    "content_length": int,        # 正文长度
    "title_length": int,          # 标题长度
    "has_numbers": bool,          # 是否有金额/百分比
    "has_quote": bool,            # 是否有高管/官方引用
    "number_count": int,          # 数字出现次数
    "mentioned_companies": [str],  # 提及的公司列表
    "company_count": int,        # 公司数量
    "contains_terms": [str],     # 包含的投资信号词
    "signal_term_count": int,    # 信号词数量
    "paragraph_count": int,      # 段落数量
    "avg_sentence_length": float, # 平均句子长度
}
```

**investment_extractor 功能**:
- **6维度投资信息抽取**:
  - `facts`: 明确事实（已发生的客观事件）
  - `numbers`: 数字/量化信息（金额、比例、增长率）
  - `business`: 商业化信息（定价、客户、营收）
  - `industry_impact`: 行业影响（竞争格局、上下游关系）
  - `management_claims`: 管理层表态（高管说法、官方声明）
  - `uncertainties`: 不确定性/风险（执行、技术、政策风险）
- **专业Prompt设计**: 以20年+二级市场研究经验的投资分析师视角
- **智能抽取**: 调用千问Plus模型进行结构化信息提取
- **结果存储**: JSON格式存储，文件名带`_investment.json`后缀

**投资信息抽取输出结构** (`InvestmentInfo`):
```python
InvestmentInfo = {
    "facts": [str],                # 明确事实
    "numbers": [str],              # 数字/量化信息
    "business": [str],             # 商业化信息
    "industry_impact": [str],      # 行业影响
    "management_claims": [str],    # 管理层表态
    "uncertainties": [str],        # 不确定性/风险
    "ai_summary": str,             # AI 内容总结（2-3句话概括核心内容）
}
```

**技术优势**:
- 基于Firefox阅读模式的成熟算法，提取准确率高
- 失败可跳过机制，不影响主流程运行
- 详细的错误处理和重试机制
- 支持批量抓取和单篇抓取两种模式
- 投资信息结构化输出，便于后续策略使用

## 📈 数据流程

### 完整的处理流程（基于main.py实现）

```
┌─────────────┐
│  RSS源列表  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ 第一步：搜索阶段 (SearchPipeline)   │
│ - 时间过滤(24小时)              │
│ - 抓取新闻(每源20条)            │
└──────┬──────────────────────────┘
       │ 输出: raw_news (原始新闻列表)
       ▼
┌──────────────────────────────┐
│ 第二步：规范化 (normalize_news)   │
│ - 验证必需字段           │
│ - 清理数据格式           │
│ - 限制最大条数(30)       │
└──────┬───────────────────┘
       │ 输出: news_list (规范化新闻列表)
       ▼
┌────────────────────────────────┐
│ 第三步：原文抓取                 │
│ - 抓取原文 (ArticleFetcher)    │
│ - 提取干净正文               │
└──────┬─────────────────────────┘
       │ 输出: 带抓取内容的新闻列表
       ▼
┌────────────────────────────────┐
│ 第四步：流程处理                 │
│ 1. 去重 (deduplicate_news)     │
│ 2. 合并 (merge_similar_news)   │
└──────┬─────────────────────────┘
       │ 输出: processed_news (去重合并的新闻列表)
       ▼
┌────────────────────────────────┐
│ 第五步：轻量化特征抽取（不用LLM）  │
│ - 内容长度、数字检测           │
│ - 引用检测、公司识别           │
│ - 投资信号词提取               │
└──────┬─────────────────────────┘
       │ 输出: 带轻量化特征的新闻列表
       ▼
┌────────────────────────────────┐
│ 第六步：新闻选择                 │
│ - 综合评分（含轻量化特征）       │
│ - 排序                         │
│ - 选择前k条(150条)             │
└──────┬─────────────────────────┘
       │ 输出: final_news (高价值新闻列表)
       ▼
┌────────────────────────────────┐
│ 第七步：投资信息抽取（使用LLM）   │
│ - 6维度结构化信息抽取          │
│ - AI内容总结                   │
└──────┬─────────────────────────┘
       │ 输出: 带投资信息的新闻列表
       ▼
┌────────────────────────────────┐
│ 第八步：事件分析                 │
│ - 文本嵌入                     │
│ - 智能聚类                     │
│ - 事件摘要                     │
└──────┬─────────────────────────┘
       │ 输出: events (事件列表)
       ▼
┌────────────────────────────────┐
│ 第九步：事件决策                 │
│ - 重要性评估                   │
│ - 信号分类                     │
│ - 动作映射                     │
└──────┬─────────────────────────┘
       │ 输出: events_with_decision (带决策的事件列表)
       ▼
┌────────────────────────────────┐
│ 第十步：公众号文章生成             │
│ - 事件排序                     │
│ - 分类渲染                     │
│ - Markdown输出                 │
└──────┬─────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 最终分析结果(JSON格式)    │
│ - 日期                   │
│ - 新闻列表(带投资信息)   │
│ - 事件列表               │
└──────────────────────────┘
```

### 实际执行顺序（main.py中的流程）

1. **搜索阶段**：使用SearchPipeline搜索最近新闻
2. **规范化**：验证和清理新闻数据
3. **原文抓取**：使用ArticleFetcher抓取网页正文
4. **流程处理**：去重和合并相似新闻
5. **轻量化特征抽取**：使用规则/正则提取高信号特征（不用LLM）
6. **新闻选择**：综合评分（含轻量化特征）、排序和选择
7. **投资信息抽取**：使用LLM抽取6维度投资信息
8. **事件分析**：嵌入、聚类和事件摘要
9. **事件决策**：重要性评估、信号分类和动作映射
10. **公众号文章生成**：事件排序、分类和Markdown渲染

### 轻量化特征抽取模块（新增）

**设计目的**：给 selector 提供更多判断维度，而不是生成内容

**技术特点**：
- 不使用 LLM，只用规则/正则/BeautifulSoup
- 提取 cheap but high-signal 的字段
- 执行速度快、成本低

**输出结构 (LightArticleFeatures)**：
```python
LightArticleFeatures = {
    "content_length": int,        # 正文长度
    "title_length": int,          # 标题长度
    "has_numbers": bool,          # 是否有金额/百分比
    "has_quote": bool,            # 是否有高管/官方引用
    "number_count": int,          # 数字出现次数
    "mentioned_companies": [str], # 提及的公司列表
    "company_count": int,         # 公司数量
    "contains_terms": [str],      # 包含的投资信号词
    "signal_term_count": int,     # 信号词数量
    "paragraph_count": int,       # 段落数量
    "avg_sentence_length": float, # 平均句子长度
}
```

**支持的公司识别**：
- 大型科技公司：NVIDIA, OpenAI, Google, Microsoft, Meta, Amazon, Apple, TSMC, AMD, Intel, ARM等
- AI公司：Anthropic, DeepMind, Hugging Face, Stability AI, Midjourney, Cohere等
- 中国公司：Baidu, Alibaba, Tencent, ByteDance, Huawei, Xiaomi等

**支持的投资信号词**：
- 财务相关：revenue, earnings, profit, guidance, forecast, billion, million等
- 交易相关：acquire, acquisition, merger, deal, investment, funding, ipo等
- 监管相关：sec, ftc, regulation, antitrust, compliance, lawsuit等
- 产品相关：launch, release, partnership, contract, patent, license等
- 供应链相关：supply, shortage, capacity, production, shipment等
### fetch模块的集成位置和作用

**集成时机**：
- **原文抓取（第三步）**：在规范化之后立即抓取，供后续所有步骤使用
- **投资信息抽取（第七步）**：在新闻选择之后，对高价值新闻进行LLM抽取

**模块组成**：
- **article_fetcher.py**：原文抓取器
- **light_features_extractor.py**：轻量化特征抽取器（新增）
- **investment_extractor.py**：投资信息抽取器（使用LLM）
- **fetch_config.py**：统一配置管理

**article_fetcher 功能**：
- **原文抓取**：对筛选出的高价值新闻URL进行原文抓取
- **正文提取**：使用readability-lxml（Firefox阅读模式算法）提取干净正文
- **噪声清洗**：自动过滤cookie提示、广告、订阅弹窗等噪声内容
- **长度控制**：限制输出长度（默认6000字符），优化token消耗
- **本地存储**：按日期分目录存储到`raw_data/YYYYMMDD/`
- **统计信息**：提供详细的抓取统计（原始大小、清洗后长度、耗时等）

**investment_extractor 功能**：
- **6维度投资信息抽取**：
  - `facts`：明确事实（已发生的客观事件）
  - `numbers`：数字/量化信息（金额、比例、增长率）
  - `business`：商业化信息（定价、客户、营收）
  - `industry_impact`：行业影响（竞争格局、上下游关系）
  - `management_claims`：管理层表态（高管说法、官方声明）
  - `uncertainties`：不确定性/风险（执行、技术、政策风险）
- **专业Prompt设计**：以20年+二级市场研究经验的投资分析师视角
- **智能抽取**：调用千问Plus模型进行结构化信息提取
- **结果存储**：JSON格式存储，文件名带`_investment.json`后缀

**技术优势**：
- 基于Firefox阅读模式的成熟算法，提取准确率高
- 失败可跳过机制，不影响主流程运行
- 详细的错误处理和重试机制
- 支持批量抓取和单篇抓取两种模式
- 投资信息结构化输出，便于后续策略使用

### 投资信息抽取输出结构 (InvestmentInfo)
```python
InvestmentInfo = {
    "facts": [str],                # 明确事实
    "numbers": [str],              # 数字/量化信息
    "business": [str],             # 商业化信息
    "industry_impact": [str],      # 行业影响
    "management_claims": [str],    # 管理层表态
    "uncertainties": [str],        # 不确定性/风险
    "ai_summary": str,             # AI 内容总结（2-3句话概括核心内容）
}
```

### 详细数据结构定义

#### 1. 搜索阶段输出 (raw_news)
```python
raw_news = [
    {
        "title": str,           # 新闻标题
        "content": str,         # 新闻内容/摘要
        "source": str,          # 新闻来源
        "url": str,             # 新闻链接
        "date": str             # 发布日期 (格式: "YYYY-MM-DD HH:MM")
    },
    # ... 更多新闻条目
]
```

#### 2. 规范化输出 (news_list)
```python
news_list = [
    {
        "title": str,           # 清理后的标题 (最大500字符)
        "content": str,         # 清理后的内容 (最大2000字符)
        "source": str,          # 清理后的来源
        "url": str,             # 清理后的链接
        "date": str             # 清理后的日期
    },
    # ... 最多 MAX_NORMALIZED_ITEMS 条
]
```

#### 3. 流程处理输出 (processed_news)
```python
processed_news = [
    {
        "title": str,           # 去重合并后的标题
        "content": str,         # 去重合并后的内容
        "source": str,          # 合并后的来源列表
        "url": str,             # 主要链接
        "date": str             # 最新日期
    },
    # ... 去重合并后的新闻
]
```

#### 4. 筛选输出 (final_news)
```python
final_news = [
    {
        "title": str,           # 新闻标题
        "content": str,         # 新闻内容（可能是原始内容或抓取内容）
        "source": str,          # 新闻来源
        "url": str,             # 新闻链接
        "date": str,            # 发布日期
        "fetched_content": str, # 抓取的原文件内容（如果有）
        "fetched_title": str,   # 抓取的原文件标题（如果有）
        "investment_score": float,  # 投资价值评分 (0-5分)
        "light_feature_score": float, # 轻量化特征评分
        "signals": List[str],   # 检测到的投资信号 (如: ["earnings", "funding"])
        "companies": List[str],  # 检测到的公司名称 (如: ["OpenAI", "Microsoft"])
        "light_features": {     # 轻量化特征（新增）
            "content_length": int,        # 正文长度
            "title_length": int,          # 标题长度
            "has_numbers": bool,          # 是否有金额/百分比
            "has_quote": bool,            # 是否有高管/官方引用
            "number_count": int,          # 数字出现次数
            "mentioned_companies": [str], # 提及的公司列表
            "company_count": int,         # 公司数量
            "contains_terms": [str],      # 包含的投资信号词
            "signal_term_count": int,     # 信号词数量
            "paragraph_count": int,       # 段落数量
            "avg_sentence_length": float, # 平均句子长度
            "extraction_success": bool,   # 抽取是否成功
            "error_message": str,         # 错误信息（可选）
        }
    },
# ... 最多 TOP_K_SELECT 条 (默认150条)
]
```

#### 5. 投资信息抽取输出 (新闻列表，第七步后)
```python
news_with_investment = [
    {
        # 所有筛选输出中的字段...
        "investment_info": {    # 投资信息抽取结果
            "facts": [str],                # 明确事实（已发生的客观事件）
            "numbers": [str],              # 数字/量化信息（金额、比例、增长率）
            "business": [str],             # 商业化信息（定价、客户、营收）
            "industry_impact": [str],      # 行业影响（竞争格局、上下游关系）
            "management_claims": [str],    # 管理层表态（高管说法、官方声明）
            "uncertainties": [str],        # 不确定性/风险（执行/技术/政策/市场/竞争风险）
        },
        "ai_summary": str,     # AI 内容总结（2-3句话概括核心内容）
    },
# ... 被选中进行LLM抽取的新闻
]
```

#### 6. 事件分析输出 (events, stats)
```python
# 事件摘要列表
events = [
    {
        "event_id": str,        # 事件唯一标识
        "news_count": int,      # 事件包含的新闻数量
        "sources": List[str],   # 事件涉及的新闻来源
        "date_range": {         # 事件时间范围
            "earliest": str,    # 最早新闻日期
            "latest": str      # 最新新闻日期
        },
        "keywords": List[str],  # 事件关键词
        "representative_title": str,  # 代表性标题
        "summary": str,        # 事件摘要
        "news_list": List[Dict] # 事件包含的新闻列表（包含所有新闻信息）
    },
    # ... 更多事件
]

# 流程统计信息
stats = {
    "total_news": int,          # 总新闻数量
    "embedding_completed": bool, # 嵌入是否完成
    "clusters_detected": int,   # 检测到的聚类数量
    "valid_events": int,        # 有效事件数量
    "events_summarized": int,   # 生成摘要的事件数量
    "total_news_in_events": int, # 事件中的总新闻数量
    "coverage_rate": float,     # 事件覆盖率
    "avg_event_size": float,    # 平均事件规模
    "max_event_size": int,      # 最大事件规模
    "min_event_size": int       # 最小事件规模
}
```

#### 7. 事件决策输出 (events_with_decision, decision_stats)
```python
# 带决策的事件列表
events_with_decision = [
    {
        "event_id": str,        # 事件唯一标识
        "news_count": int,      # 事件包含的新闻数量
        "sources": List[str],   # 事件涉及的新闻来源
        "date_range": {         # 事件时间范围
            "earliest": str,    # 最早新闻日期
            "latest": str      # 最新新闻日期
        },
        "keywords": List[str],  # 事件关键词
        "representative_title": str,  # 代表性标题
        "summary": str,        # 事件摘要
        "news_list": List[Dict], # 事件包含的新闻列表（包含所有新闻信息）
        "decision": {          # 事件决策信息
            "importance": str,  # 重要性级别 (High/Medium/Low)
            "signal": str,      # 市场信号 (Positive/Neutral/Risk)
            "action": str       # 投资动作 (Watch/Hold/Avoid)
        }
    },
    # ... 更多带决策的事件
]

# 决策统计信息
decision_stats = {
    "total_events": int,        # 总事件数量
    "success_count": int,       # 成功决策的事件数量
    "error_count": int,         # 决策失败的事件数量
    "success_rate": float,      # 决策成功率 (0-1)
    "importance_distribution": {  # 重要性分布
        "High": int,
        "Medium": int,
        "Low": int
    },
    "signal_distribution": {    # 信号分布
        "Positive": int,
        "Neutral": int,
        "Risk": int
    },
    "action_distribution": {    # 动作分布
        "Watch": int,
        "Hold": int,
        "Avoid": int
    },
    "errors": List[str]         # 错误信息列表
}
```

#### 8. 事件分析输入 (news_list - 带投资信息)
```python
news_list = [
    {
        "title": str,           # 新闻标题
        "content": str,         # 新闻内容（可能是原始内容或抓取内容）
        "source": str,          # 新闻来源
        "url": str,             # 新闻链接
        "date": str,            # 发布日期
        "fetched_content": str, # 抓取的原文件内容（如果有）
        "fetched_title": str,   # 抓取的原文件标题（如果有）
        "investment_score": float,  # 投资价值评分 (0-5分)
        "light_feature_score": float, # 轻量化特征评分
        "signals": List[str],   # 检测到的投资信号 (如: ["earnings", "funding"])
        "companies": List[str],  # 检测到的公司名称 (如: ["OpenAI", "Microsoft"])
        "light_features": {     # 轻量化特征
            "content_length": int,        # 正文长度
            "has_numbers": bool,          # 是否有金额/百分比
            "has_quote": bool,            # 是否有高管/官方引用
            "number_count": int,          # 数字出现次数
            "mentioned_companies": [str], # 提及的公司列表
            "company_count": int,         # 公司数量
            "contains_terms": [str],      # 包含的投资信号词
            "signal_term_count": int,     # 信号词数量
        },
        "investment_info": {    # 投资信息抽取结果（第七步后）
            "facts": [str],                # 明确事实（已发生的客观事件）
            "numbers": [str],              # 数字/量化信息（金额、比例、增长率）
            "business": [str],             # 商业化信息（定价、客户、营收）
            "industry_impact": [str],      # 行业影响（竞争格局、上下游关系）
            "management_claims": [str],    # 管理层表态（高管说法、官方声明）
            "uncertainties": [str],        # 不确定性/风险（执行/技术/政策/市场/竞争风险）
        },
        "ai_summary": str,     # AI 内容总结（2-3句话概括核心内容）
    },
    # ... 新闻列表
]
```

#### 9. 最终分析结果 (main.py 输出)
```python
result = {
    "date": str,                # 分析日期 (格式: "YYYY-MM-DD")
    "news": List[Dict],         # 带投资信息的新闻列表（见第5节结构）
    "events": List[Dict]        # 带决策的事件列表（见第7节结构）
}

stats = {
    # 各阶段统计信息（搜索、规范化、抓取、轻量化抽取、选择、投资抽取、事件分析、事件决策、文章生成）
    "search_stats": Dict,
    "normalize_stats": Dict,
    "fetch_stats": Dict,
    "light_features_stats": Dict,
    "select_stats": Dict,
    "investment_extract_stats": Dict,
    "event_stats": Dict,
    "decision_stats": Dict,
    "article_stats": Dict,
}
```

### 处理流程说明

1. **搜索阶段**: 从RSS源抓取原始新闻数据，包含基础字段（标题、内容、来源、URL、日期）
2. **规范化**: 验证必需字段、清理数据格式、限制最大条数（30条）
3. **原文抓取**: 使用ArticleFetcher抓取网页原文，提取干净正文，存储在`fetched_content`字段中
4. **流程处理**: 去重和合并相似新闻，优化数据质量
5. **轻量化特征抽取**: 使用规则/正则提取高信号特征（内容长度、数字、引用、公司、信号词等），存储在`light_features`字段中
6. **新闻选择**: 综合评分（含轻量化特征）、排序和选择高价值新闻（最多150条），输出包含`light_feature_score`等新字段
7. **投资信息抽取**: 使用LLM抽取6维度结构化投资信息（事实、数字、商业化、行业影响、管理层表态、不确定性）和AI总结，存储在`investment_info`和`ai_summary`字段中
8. **事件分析**: 对带投资信息的新闻进行聚类分析，识别投资事件和模式
9. **事件决策**: 评估事件重要性、分类市场信号、生成投资动作（Watch/Hold/Avoid）
10. **最终分析**: 输出包含完整新闻和事件分析的结构化结果

每个阶段都会对新闻数据进行逐步优化、增强和筛选，最终输出的新闻包含完整的轻量化特征和投资信息分析。

## 📊 统计信息输出

系统在每个处理阶段都输出详细的统计信息：

### 搜索阶段统计
- **源分类统计**:
  - ✓ 有效源：有搜索结果且有未过期新闻
  - ⏱ 过期源：有搜索结果但都是过期新闻
  - ✗ 无效源：没有搜索结果

- **各源详细统计**:
  - 总找到: 源中的总条数
  - 有效获取: 未过期且被选中的条数
  - 跳过(无时间): 缺少发布时间的条数
  - 跳过(过期): 超出时间范围的条数

### 规范化阶段统计
- 各源最终条数

### 流程处理统计(去重→合并)
- 输入条数
- 去重后条数(移除数)
- 合并后条数(合并数)

### 新闻选择统计(评分→排序→选择)
- 输入条数
- 输出条数
- 平均评分
- 分数分布

### 事件分析统计(嵌入→聚类→摘要)
- 输入新闻总数
- 检测到的聚类数量
- 有效事件数量
- 事件覆盖率
- 平均事件规模
- 关键词分布

### 事件决策统计(重要性评估→信号分类→动作映射)
- 输入事件总数
- 决策成功率
- 重要性分布 (High/Medium/Low)
- 信号分布 (Positive/Neutral/Risk)
- 动作分布 (Watch/Hold/Avoid)
- 错误信息统计

## 🔧 配置说明

### RSS源配置 (`src/search/rss_config.py`)

```python
SEARCH_HOURS = 24  # 搜索时间范围
MAX_ITEMS_PER_SOURCE = 20  # 每源最大条数
MAX_NORMALIZED_ITEMS = 30  # 规范化输出最大条数
```

### 筛选配置 (`src/selector/selector_config.py`)

```python
TOP_K_SELECT = 150  # 最终选择数量（增加数量以丰富内容）
```

### 评分规则配置 (`src/selector/news_selector.py`)

可根据需要调整事件权重和公司重点列表。

## 🧪 测试

每个模块都包含独立的测试函数，可直接运行：

```bash
# 测试搜索模块
python -m src.search.search_pipeline

# 测试筛选模块
python -m src.selector.news_selector

# 测试处理模块
python -m src.search.search_result_process
```

### 全流程测试

使用 `test_full_flow.py` 可以测试从 normalize_news 开始的完整流程：

```bash
# 从项目根目录运行
python tests/test_full_flow.py

# 或使用 pytest
pytest tests/test_full_flow.py -v
```

该脚本会：
1. 生成 200 条 Mock AI 投资新闻数据（日期设为一年前）
2. 执行规范化 → 原文抓取(Mock) → 去重合并 → 轻量化特征 → 新闻选择
3. 执行事件分析 → 事件决策 → 公众号文章生成
4. 导出数据到 webapp/data/ 目录
5. 在控制台显示测试结果统计

测试完成后可访问 http://localhost:8080 查看 Mock 数据的渲染效果。

### H5 导出器测试

使用 `test_exporter.py` 可以单独测试 webapp 导出功能：

```bash
# 从项目根目录运行
python tests/test_exporter.py
```

### Event 模块集成测试

使用 `test_event_integration.py` 测试 Event 模块集成：

```bash
# 从项目根目录运行
python tests/test_event_integration.py
```

## 🔐 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | 阿里云DashScope API密钥 | `sk-xxx` |

## 📦 依赖项

- **feedparser** - RSS源解析
- **dashscope** - 阿里云AI服务
- **requests** - HTTP请求
- **pydantic** - 数据验证
- **python-dotenv** - 环境变量管理
- **readability-lxml** - 文章正文提取（Firefox阅读模式算法）
- **beautifulsoup4** - HTML解析和清洗
- **sentence-transformers** - 文本嵌入和相似度计算
- **aiohttp** - 异步HTTP客户端（并发RSS抓取）
- **yfinance** - 🆕 股价数据获取（可选，用于股价监控）

## 🐛 故障排除

### 问题: 选择后输出0条新闻
**原因**: 新闻评分全部为负或0分，被过滤掉
**解决**: 
- 检查RSS源是否有新数据
- 调整评分规则参数
- 检查关键词配置

### 问题: API调用失败
**原因**: DashScope API密钥不有效或网络问题
**解决**:
- 检查 `DASHSCOPE_API_KEY` 环境变量
- 确认网络连接
- 查看API调用日志

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 👥 贡献

欢迎提交Issue和Pull Request

## 📧 联系方式

- GitHub: https://github.com/janwang001/ai-invest-news
- Email: janwang001@outlook.com

## 🔄 更新日志

### v2.0.0 (2026-02-04) - 精准监控系统 🎯
**Week 1: SEC + 监管监控**
- **SEC EDGAR采集器**: 监控8-K、Form D、S-1、13D/13G等关键文件
- **监管机构采集器**: FTC、DOJ、EU Commission新闻监控
- **3级警报系统**: P0(立即)/P1(1小时)/P2(每日)优先级分类
- **投资信号判断**: 自动识别Positive/Negative/Neutral信号

**Week 2: 博客 + 股价 + 通知**
- **大厂博客采集器**: OpenAI、Google AI、Meta AI、Anthropic、NVIDIA、DeepMind
- **股价异动监控**: 16只AI相关股票，5%涨跌触发P0
- **通知推送系统**: 支持控制台、文件、Webhook(Slack/企业微信/钉钉)
- **命令行工具**: `run_monitor.py`统一入口，支持丰富参数配置

### v1.1.0 (2026-02-04) - Phase 1: Investment Intelligence Upgrade 🚀
- **投资论点分析**: 看涨/看跌理由、关键问题、时间周期、历史类比
- **7维度投资评分卡**: 重要性、紧迫性、确信度、竞争影响、风险、创新度、执行力
- **3层级事件结构**: Tier 1（详细）/ Tier 2（精简）/ Tier 3（标题）
- **今日重点关注**: Top 3 Executive Alerts with action recommendations
- **风险-收益评估**: 可视化上行潜力和下行风险
- **报告质量提升**: 从"描述性"到"可行动"的投资洞察
- **成本增加**: +60% ($0.50 → $0.80/report)
- **时间增加**: +10% (10 → 11 minutes)

### v0.3.0 (2026-01-23) - RSS并发抓取优化
- **新增并发RSS抓取功能**: 实现基于asyncio的高性能并发抓取
- **性能大幅提升**: 并发模式（并发数=10）实现88.1%性能提升，加速比达到8.38倍
- **资源消耗健康**: CPU峰值仅28.8%，内存增量仅0.2%
- **技术实现**: 使用asyncio + aiohttp实现异步并发，信号量控制并发数
- **向后兼容**: 支持串行/并发模式切换，一行配置即可切换

### v0.2.0 (2026-01-20)
- **新增轻量化特征抽取模块**: 不使用LLM，只用规则/正则提取高信号特征
- **流程重构为10步**: 优化处理流程，减少LLM调用次数
- **NewsSelectorPipeline增强**: 支持基于轻量化特征的综合评分

### v0.1.9 (2026-01-20)
- **移除generation模块**: 将AI摘要生成功能迁移到fetch模块
- **主流程优化**: 简化流程结构，提高代码维护性

### v0.1.8 (2026-01-20)
- **investment_extractor.py完整实现**: 6维度投资信息抽取
- **专业投资分析师视角Prompt设计**: 20年+二级市场研究经验

### v0.1.7 (2026-01-20)
- **新增fetch模块**: 文章原文抓取功能
- **技术选型**: readability-lxml + BeautifulSoup4 + requests

### v0.1.6 (2026-01-20)
- **重要文章列表功能**: 在关键信息拆解部分新增重要性排名前5的文章
- **排序规则优化**: 基于权威性和新鲜度评分

### v0.1.5 (2026-01-20)
- **decision模块主流程集成**: 将事件决策层集成到main.py主流程
- **决策统计输出**: 完整的决策成功率、分布统计和错误信息

### v0.1.4 (2026-01-20)
- **聚类算法优化**: 实现智能聚类策略，根据数据规模自适应选择算法
- **事件有效性判断**: 添加多维度验证确保事件质量

### v0.1.3 (2026-01-20)
- **新增event模块**: 添加事件分析功能，支持新闻聚类和事件检测

### v0.1.2 (2026-01-20)
- **文档完善**: 详细定义每一步的news结构，清晰展示输入输出格式

### v0.1.1 (2026-01-20)
- **代码重构**: 将AI生成摘要功能内聚到generation模块

### v0.1.0 (2026-01-20)
- **初始版本发布**: 完整的搜索→规范化→处理→筛选→AI分析流程
- **支持50+个RSS源**: AI/科技/投资相关新闻源
- **集成Qwen LLM**: 进行深度投资新闻分析

---

**最后更新**: 2026-02-04 (v2.0.0)

## 📚 更多文档

- **[Phase 1 Implementation Details](docs/PHASE1_IMPLEMENTATION.md)** - 完整实现文档
- **[Quick Reference Guide](docs/PHASE1_QUICK_REFERENCE.md)** - 快速参考指南
- **[Changelog](CHANGELOG.md)** - 版本更新历史
- **[Example Report](/tmp/test_phase1_report.md)** - 示例报告（测试生成）

---

*一个专业的AI驱动投资新闻分析平台，帮助投资者从海量信息中提取高价值洞察*

**Professional Investment Intelligence Platform - Powered by AI**
