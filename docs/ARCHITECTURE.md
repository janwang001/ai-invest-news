# AI 投资新闻分析系统 - 架构文档

## 项目结构

```
ai-invest-news/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── main.py                   # 主入口：12步Pipeline
│   ├── run_monitor.py            # 精准监控入口
│   ├── dev_server.py             # 开发服务器
│   ├── webapp_exporter.py        # H5导出器
│   │
│   ├── collectors/               # 数据采集模块 (Week 1-2)
│   │   ├── __init__.py
│   │   ├── sec_edgar_collector.py    # SEC EDGAR采集
│   │   ├── regulatory_collector.py   # 监管机构采集(FTC/DOJ/EU)
│   │   ├── blog_collector.py         # AI公司博客采集
│   │   ├── stock_monitor.py          # 股价监控
│   │   ├── twitter_monitor.py        # Twitter/X监控
│   │   ├── github_monitor.py         # GitHub趋势监控
│   │   ├── hackernews_monitor.py     # Hacker News监控
│   │   ├── alert_system.py           # 3级警报系统
│   │   ├── notifier.py               # 通知推送
│   │   └── precision_monitor.py      # 精准监控调度器
│   │
│   ├── search/                   # 搜索模块
│   │   ├── __init__.py
│   │   ├── rss_config.py             # RSS源配置(86个)
│   │   ├── concurrent_rss_fetcher.py # 并发RSS抓取
│   │   ├── search_pipeline_v2.py     # 搜索Pipeline
│   │   └── search_result_process.py  # 去重合并
│   │
│   ├── fetch/                    # 抓取模块
│   │   ├── __init__.py
│   │   ├── article_fetcher.py        # 文章内容抓取
│   │   ├── light_features_extractor.py # 轻量特征提取
│   │   └── investment_extractor.py   # LLM投资信息提取
│   │
│   ├── selector/                 # 筛选模块
│   │   ├── __init__.py
│   │   ├── news_selector.py          # 新闻质量评分
│   │   ├── selector_config.py        # 筛选配置
│   │   └── investment_scorer.py      # 投资评分卡计算
│   │
│   ├── event/                    # 事件模块
│   │   ├── __init__.py
│   │   ├── embedding.py              # 文本嵌入
│   │   ├── clustering.py             # 新闻聚类
│   │   ├── event_summary.py          # 事件摘要
│   │   ├── event_pipeline.py         # 事件Pipeline
│   │   └── decision/                 # 决策子系统
│   │       ├── importance_evaluator.py
│   │       ├── signal_classifier.py
│   │       ├── action_mapper.py
│   │       └── decision_pipeline.py
│   │
│   ├── content/                  # 内容生成模块
│   │   ├── __init__.py
│   │   ├── article_schema.py         # 数据结构定义
│   │   ├── article_builder.py        # 文章构建器
│   │   └── article_renderer.py       # Markdown渲染器
│   │
│   └── demo/                     # 演示模块
│       └── ...
│
├── tests/                        # 测试
│   ├── __init__.py
│   ├── conftest.py                   # pytest配置
│   ├── test_phase1_integration.py    # Phase 1集成测试
│   ├── test_week1_integration.py     # Week 1集成测试
│   ├── test_week2_integration.py     # Week 2集成测试
│   ├── test_event_integration.py     # 事件模块测试
│   ├── test_exporter.py              # 导出器测试
│   ├── test_full_flow.py             # 完整流程测试
│   ├── safe_progressive_test.py      # 渐进式测试
│   └── benchmark_rss_performance.py  # 性能基准测试
│
├── docs/                         # 文档
│   ├── ARCHITECTURE.md               # 架构文档(本文件)
│   ├── PHASE1_IMPLEMENTATION.md      # Phase 1实现详情
│   ├── PHASE1_QUICK_REFERENCE.md     # Phase 1快速参考
│   ├── PHASE1_COMPLETE.md            # Phase 1完成总结
│   ├── PRECISION_DATA_SOURCES_PLAN.md    # 精准数据源计划
│   ├── FREE_DATA_SOURCES_PLAN.md         # 免费数据源计划
│   ├── INFORMATION_COLLECTION_OPTIMIZATION_PLAN.md  # 信息采集优化计划
│   ├── INTEGRATION_SUMMARY.md        # 集成总结
│   ├── FINAL_PERFORMANCE_TEST_REPORT.md  # 性能测试报告
│   └── archive/                      # 归档文档
│       ├── PROJECT_STRUCTURE.md      # 旧项目结构
│       ├── MIGRATION_GUIDE.md        # 迁移指南
│       └── ...
│
├── examples/                     # 示例代码
│   └── concurrent_rss_examples.py
│
├── webapp/                       # H5 Web应用
│   ├── index.html
│   ├── event.html
│   ├── detail.html
│   ├── test.html
│   ├── css/
│   ├── js/
│   └── data/                     # 导出的JSON数据
│
├── output/                       # 输出目录 (gitignore)
│   ├── alerts/                   # 警报JSON
│   └── *.md                      # 生成的报告
│
├── raw_data/                     # 原始数据 (gitignore)
│   └── YYYYMMDD/                 # 按日期存储
│
├── CLAUDE.md                     # Claude Code指引
├── CHANGELOG.md                  # 版本变更日志
├── README.md                     # 项目说明
├── requirements.txt              # Python依赖
├── pyproject.toml                # 项目配置
├── LICENSE                       # 许可证
├── .gitignore                    # Git忽略配置
└── .claudeignore                 # Claude忽略配置
```

## 模块依赖关系

```
                    ┌─────────────────┐
                    │    main.py      │
                    │  (12步Pipeline) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    search/    │   │    fetch/     │   │   selector/   │
│  RSS抓取+规范 │   │ 内容+特征抽取 │   │  评分+筛选    │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    event/     │
                    │ 聚类+决策     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   content/    │
                    │  报告生成     │
                    └───────────────┘


                    ┌─────────────────┐
                    │  run_monitor.py │
                    │  (精准监控入口)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │    collectors/    │
                    │  precision_monitor│
                    └────────┬──────────┘
                             │
    ┌────────────┬───────────┼───────────┬────────────┐
    │            │           │           │            │
    ▼            ▼           ▼           ▼            ▼
┌────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│SEC     │ │regulatory│ │  blog   │ │  stock  │ │twitter/  │
│EDGAR   │ │collector │ │collector│ │ monitor │ │github/hn │
└────────┘ └──────────┘ └─────────┘ └─────────┘ └──────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │ alert_system  │
                    │  (P0/P1/P2)   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   notifier    │
                    │ (Webhook推送) │
                    └───────────────┘
```

## 数据流

### 主Pipeline数据流

```
RSS Feeds (86个源)
       │
       ▼ Step 1-2: 抓取+规范化
raw_news[] → news_list[]
       │
       ▼ Step 3: 原文抓取
news_list[] + fetched_content
       │
       ▼ Step 4: 去重合并
processed_news[]
       │
       ▼ Step 5: 轻量特征
+light_features
       │
       ▼ Step 6: 筛选
final_news[] (top-k)
       │
       ▼ Step 7: LLM投资信息抽取
+investment_info
       │
       ▼ Step 7.5: 评分卡计算
+investment_scorecard
       │
       ▼ Step 8-9: 事件分析+决策
events[]
       │
       ▼ Step 10: 报告生成
DailyArticle (3层级)
       │
       ▼ Step 11: H5导出
webapp/data/YYYYMMDD.json
```

### 精准监控数据流

```
多数据源
├── SEC EDGAR → SEC Filings
├── FTC/DOJ/EU → Regulatory News
├── AI Blogs → Blog Posts
├── Stock API → Price Alerts
├── Twitter → KOL Tweets
├── GitHub → Trending Repos
└── HN → Hot Stories
       │
       ▼ 统一处理
Alert Objects
       │
       ▼ 优先级分类
├── P0: 立即推送 (IPO, $100M+融资, 调查)
├── P1: 1小时汇总 (8-K, 一般监管)
└── P2: 每日汇总 (13G, 常规更新)
       │
       ▼ 通知推送
Webhook (Slack/WeCom/DingTalk)
```

## 版本历史

- **v1.0.0**: 初始版本，基础12步Pipeline
- **v1.1.0**: Phase 1 - 投资评分卡、3层级事件、投资论点
- **v1.2.0**: Week 1 - SEC/监管精准监控
- **v1.3.0**: Week 2 - 博客/股价/社交媒体监控
