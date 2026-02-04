# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

**AI投资新闻分析系统** - 一个专业的投资情报平台，通过12步流程pipeline将原始新闻转化为可行动的投资洞察，结合了RSS聚合、自然语言处理、大语言模型分析和投资评分。

**当前版本**: 1.3.0 (Phase 1 + Week 1-2 精准监控)

---

## 运行系统

### 主流程
```bash
# 运行完整的12步pipeline（生成投资报告）
python3 src/main.py

# 或使用虚拟环境
venv/bin/python src/main.py
```

### 精准监控（Week 1 新增）
```bash
# 测试模式（使用模拟数据）
venv/bin/python src/run_monitor.py --test

# 生产模式（真实数据）
venv/bin/python src/run_monitor.py

# 自定义时间范围
venv/bin/python src/run_monitor.py --sec-hours 1 --regulatory-hours 2

# 导出警报到JSON
venv/bin/python src/run_monitor.py --export alerts.json

# 仅运行SEC监控
venv/bin/python src/run_monitor.py --no-regulatory
```

### 测试
```bash
# 运行Phase 1集成测试（验证v1.1功能）
venv/bin/python tests/test_phase1_integration.py

# 运行Week 1集成测试（精准监控）
venv/bin/python tests/test_week1_integration.py

# 使用pytest运行（需要安装）
venv/bin/python -m pytest tests/

# 带覆盖率运行
venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

### H5 Web应用
```bash
# 启动本地开发服务器（提供web界面）
python3 src/dev_server.py

# 访问地址: http://localhost:8000
```

### 环境设置
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # 或: venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置必需的API密钥
export DASHSCOPE_API_KEY="your-key-here"
```

---

## 架构: 12步Pipeline

系统通过顺序pipeline处理新闻。每一步都会向流经的新闻对象添加数据：

### Pipeline流程

```
步骤1: RSS抓取（86个源）
  ↓ raw_news[]
步骤2: 规范化
  ↓ news_list[] {url, title, content, date, source}
步骤3: 原文抓取
  ↓ +fetched_content, +fetch_stats
步骤4: 去重和合并
  ↓ processed_news[]
步骤5: 轻量化特征抽取
  ↓ +light_features {has_quote, has_numbers, signals[], companies[]}
步骤6: 新闻筛选
  ↓ final_news[] (top-k过滤后)
步骤7: 投资信息抽取（LLM）
  ↓ +investment_info {facts[], numbers[], business[], industry_impact[],
                       management_claims[], uncertainties[], ai_summary,
                       investment_thesis {bull_case[], bear_case[], key_question, time_horizon}}
步骤7.5: 投资评分卡计算（基于规则）
  ↓ +investment_scorecard {7个维度, composite_score, investment_rating}
步骤8: 事件分析
  ↓ events[] {news_list[], summary, representative_title}
步骤9: 事件决策
  ↓ +decision {importance, signal, action}
步骤10: 文章生成
  ↓ 3层级报告（Tier1: 详细, Tier2: 精简, Tier3: 标题）
步骤11: H5导出
  ↓ webapp/data/YYYYMMDD.json
```

### 关键数据结构

**新闻对象**（完整pipeline后）:
```python
{
    "url": str,
    "title": str,
    "content": str,
    "date": str,  # "YYYY-MM-DD HH:MM"
    "source": str,
    "fetched_content": str,  # 步骤3
    "light_features": {...},  # 步骤5
    "investment_info": {      # 步骤7
        "facts": [...],               # 明确事实
        "numbers": [...],             # 数字/量化信息
        "business": [...],            # 商业化信息
        "industry_impact": [...],     # 行业影响
        "management_claims": [...],   # 管理层表态
        "uncertainties": [...],       # 不确定性/风险
        "ai_summary": str,            # AI总结
        "investment_thesis": {        # 投资论点
            "bull_case": [str, str, str],        # 看涨理由
            "bear_case": [str, str, str],        # 看跌理由
            "key_question": str,                 # 关键问题
            "time_horizon": str,  # "即时" | "1-3个月" | "6-12个月" | "长期"
            "comparable_events": [str, str]      # 历史类似事件
        }
    },
    "investment_scorecard": {  # 步骤7.5
        "materiality_score": float,    # 0-10 重要性
        "urgency_score": float,        # 0-10 紧迫性
        "conviction_score": float,     # 0-10 确信度
        "competitive_score": float,    # 0-10 竞争影响
        "risk_score": float,           # 0-10 风险
        "innovation_score": float,     # 0-10 创新度
        "execution_score": float,      # 0-10 执行力
        "composite_score": float,      # 0-100 综合得分
        "investment_rating": str,      # "Strong Buy Signal" | "Monitor" | "Risk Alert" | "Pass"
        "reasoning": {...}             # 评分理由
    }
}
```

**事件对象**（步骤8-9后）:
```python
{
    "event_id": str,
    "news_list": [news_object, ...],
    "news_count": int,
    "summary": str,
    "representative_title": str,
    "sources": [str, ...],
    "companies": [str, ...],
    "decision": {  # 步骤9
        "importance": str,  # "High" | "Medium" | "Low"
        "signal": str,      # "Positive" | "Neutral" | "Risk"
        "action": str       # "Watch" | "Monitor" | "Ignore"
    }
}
```

---

## 模块架构

### 0. 精准监控模块 (`src/collectors/`) [Week 1 新增]
**用途**: 高敏感度数据源的精准监控

- `sec_edgar_collector.py`: SEC EDGAR文件采集
  - 监控Form类型: 8-K(重大事件), D(私募融资), S-1(IPO), 13D/13G(持股)
  - AI公司关键词过滤
  - 优先级计算(P0/P1/P2)

- `regulatory_collector.py`: 监管机构新闻采集
  - FTC: 反垄断、消费者保护
  - DOJ: 刑事调查、反垄断
  - EU Commission: AI法案、数字市场法

- `alert_system.py`: 3级警报系统
  - P0: 5分钟内推送（IPO、$100M+融资、刑事调查）
  - P1: 1小时内汇总（8-K事件、一般监管新闻）
  - P2: 每日汇总（一般Form D、13G等）

- `precision_monitor.py`: 统一调度器
  - SEC检查间隔: 5分钟
  - 监管检查间隔: 15分钟
  - P0回调通知机制

**使用方式**:
```python
from src.collectors import run_precision_monitor

# 单次运行
results = run_precision_monitor(test_mode=True)

# 访问警报
p0_alerts = results["alerts"]["p0"]  # 紧急警报
```

### 1. 搜索模块 (`src/search/`)
**用途**: RSS源聚合和初步处理

- `rss_config.py`: RSS源URL配置（86个源），并发设置
- `concurrent_rss_fetcher.py`: 使用aiohttp的异步RSS抓取
- `search_pipeline_v2.py`: 主搜索编排器（支持串行/并发）
- `search_result_process.py`: 去重和基于相似度的合并

**关键配置**:
```python
USE_CONCURRENT = True  # 切换串行/并发模式
MAX_CONCURRENT = 10    # 并发抓取限制
MAX_NORMALIZED_ITEMS = 200  # 最大处理新闻数
```

### 2. 抓取模块 (`src/fetch/`)
**用途**: 文章内容提取和特征分析

- `article_fetcher.py`: HTML → 清洁文本（readability-lxml + BeautifulSoup）
- `light_features_extractor.py`: 基于规则的特征抽取（不用LLM）
- `investment_extractor.py`: 基于LLM的投资信息抽取（Qwen）
  - **关键**: 包含InvestmentThesis和InvestmentInfo数据类
  - 使用DashScope API（需要DASHSCOPE_API_KEY）
  - Prompt约2000 tokens（8个维度）

### 3. 筛选模块 (`src/selector/`)
**用途**: 新闻质量评分和过滤

- `news_selector.py`: 多维度质量评分（来源、关键词、特征）
- `investment_scorer.py`: **[v1.1 新增]** 7维度投资评分卡计算器
  - 基于规则（不用LLM），零额外成本
  - 权重: 重要性(25%), 紧迫性(20%), 确信度(20%)
  - 输出综合得分(0-100) + 评级

**评分权重** (在`investment_scorer.py`中):
```python
self.weights = {
    "materiality": 0.25,    # 重要性
    "urgency": 0.20,        # 紧迫性
    "conviction": 0.20,     # 确信度
    "competitive": 0.15,    # 竞争影响
    "risk": 0.10,           # 风险（反向，风险越低分数越高）
    "innovation": 0.10,     # 创新度
}
```

### 4. 事件模块 (`src/event/`)
**用途**: 新闻聚类和决策逻辑

- `embedding.py`: 通过sentence-transformers生成文本嵌入
- `clustering.py`: HDBSCAN聚类（自动检测聚类数量）
- `event_summary.py`: 从聚类新闻生成事件摘要
- `event_pipeline.py`: 编排 嵌入 → 聚类 → 摘要生成
- `decision/`: 事件决策子系统
  - `importance_evaluator.py`: 评估重要性（High/Medium/Low）
  - `signal_classifier.py`: 分类信号（Positive/Neutral/Risk）
  - `action_mapper.py`: 映射到行动（Watch/Monitor/Ignore）
  - `decision_pipeline.py`: 组合评估器 + 分类器 + 映射器

**聚类逻辑**: 基于数据规模使用智能策略:
- <10条新闻: 不聚类（每条新闻 = 1个事件）
- 10-50条新闻: DBSCAN
- 50-200条新闻: HDBSCAN
- 200+条新闻: 层次聚类

### 5. 内容模块 (`src/content/`)
**用途**: 投资报告生成

- `article_schema.py`: 数据类（ArticleEvent, DailyArticle）
- `article_builder.py`: **[v1.1]** 根据综合得分将事件分为3个层级
  - Tier 1 (>=70): 最多3个事件，完整详情
  - Tier 2 (50-69): 最多5个事件，精简格式
  - Tier 3 (<50): 最多3个事件，仅标题
- `article_renderer.py`: **[v1.1]** Markdown渲染器，包含新增部分:
  - 今日重点关注（Top 3，按紧迫性 × 重要性排序）
  - 投资评分卡（7维度可视化）
  - 投资论点（看涨/看跌/关键问题）
  - 风险-收益评估（可视化条形图）

---

## 关键实现细节

### LLM集成（步骤7）
**模型**: Qwen Plus（DashScope API）
**成本**: 每份报告约$0.80（从v1.0的$0.50增加）
**超时**: 每次API调用120秒
**错误处理**: 如果缺少API密钥，回退到本地模式

**Prompt结构** (在`investment_extractor.py`中):
```python
def _build_prompt(self, content: str, title: Optional[str] = None) -> str:
    # 8个维度:
    # 1. facts（明确事实）, 2. numbers（数字）, 3. business（商业化）,
    # 4. industry_impact（行业影响）, 5. management_claims（管理层表态）,
    # 6. uncertainties（不确定性）, 7. ai_summary（AI总结）,
    # 8. investment_thesis（投资论点，v1.1新增）
```

### 投资评分卡计算（步骤7.5）
**位置**: `src/selector/investment_scorer.py`
**触发时机**: 投资信息抽取后、事件分析前
**性能**: 每条新闻约10ms（基于规则，无API调用）

**关键逻辑**:
```python
# 重要性: 数字 + 商业信息 + tier1公司
# 紧迫性: 紧急信号 + 管理层表态 + 时间周期
# 确信度: tier1来源 + 有引用 + 事实
# 竞争影响: 行业影响关键词 + 多公司
# 风险: 不确定性 + 看跌理由数量
# 创新度: 创新信号 + 关键词
```

### 3层级事件结构（步骤10）
**位置**: `src/content/article_builder.py:_filter_and_sort_events()`

**层级分配**:
```python
avg_composite = sum(news["investment_scorecard"]["composite_score"]
                    for news in event["news_list"]) / len(event["news_list"])

if avg_composite >= 70: tier1_events.append(event)
elif avg_composite >= 50: tier2_events.append(event)
else: tier3_events.append(event)
```

### 今日重点关注（步骤10）
**位置**: `src/content/article_renderer.py:_render_executive_alerts()`

**排序逻辑**:
```python
urgency_score = news["investment_scorecard"]["urgency_score"]
materiality_score = news["investment_scorecard"]["materiality_score"]
alerts.sort(key=lambda x: x["urgency_score"] * x["materiality_score"], reverse=True)
```

---

## 配置文件

### RSS源 (`src/search/rss_config.py`)
- 86个RSS feeds（TechCrunch, Bloomberg, Reuters等）
- 按源类型组织（tech_news, ai_news, finance_news）
- 每个包含: 名称、URL、优先级（1-3）

### 筛选关键词 (`src/selector/selector_config.py`)
- 高价值关键词（AI, GPT, LLM等）
- 投资信号（IPO, 融资, 收购等）
- 用于步骤6的质量评分

### 事件决策规则 (`src/event/decision/decision_config.py`)
- 重要性规则（新闻数、公司、来源质量）
- 信号分类（积极/风险关键词）
- 行动阈值

---

## 测试策略

### 集成测试 (`tests/test_phase1_integration.py`)
**验证**: 所有v1.1功能，无需API密钥
**模拟数据**: 创建带评分卡的真实新闻/事件
**覆盖范围**:
- 投资论点提取
- 7维度评分卡计算
- 3层级事件排序
- 今日重点关注生成
- 风险-收益评估
- 完整markdown渲染

**运行时间**: 约2秒

### 预期测试输出
```
✅ 投资论点(Bull Case): 通过
✅ 投资论点(Bear Case): 通过
✅ 投资评分卡: 通过
✅ 今日重点关注: 通过
✅ 风险-收益评估: 通过
✅ 核心事件(高优先级): 通过
```

---

## 性能特征

### 延迟（端到端）
- **v1.0**: 约10分钟
- **v1.1**: 约11分钟（+10%）
  - 步骤7（LLM）: 约8分钟（最大瓶颈）
  - 步骤7.5（评分卡）: 约10秒（200条新闻 × 50ms）
  - 其他步骤: 约3分钟

### 成本（每份报告）
- **v1.0**: $0.50（Qwen Plus，6个维度）
- **v1.1**: $0.80（+60%）
  - 投资论点包含在现有LLM调用中
  - 评分卡计算: $0（基于规则）

### 输出大小
- **报告**: 约5,000-15,000字符（Markdown）
- **H5导出**: 约100-500 KB（JSON）
- **原始数据**: 存储在`raw_data/YYYYMMDD/`

---

## 常见开发模式

### 添加新的Pipeline步骤

1. 在`src/main.py`中创建函数:
```python
def _my_new_step(news_list: List[Dict], stats: Dict) -> List[Dict]:
    """步骤X: 我的新功能"""
    for news in news_list:
        # 添加新字段
        news["my_field"] = calculate_something(news)
    stats["my_stats"] = {"processed": len(news_list)}
    return news_list
```

2. 在`generate_ai_news()`pipeline中适当位置插入
3. 更新docstring中的步骤编号
4. 在`tests/`中添加测试

### 添加新的评分维度

**文件**: `src/selector/investment_scorer.py`

1. 在`InvestmentScorecard`数据类中添加评分字段
2. 实现`_calculate_my_dimension()`方法
3. 更新`calculate_scorecard()`以调用新方法
4. 如需要调整`self.weights`（总和必须≤1.0）

### 修改报告格式

**文件**: `src/content/article_renderer.py`

- Tier 1渲染: `_render_single_event(event, detailed=True)`
- Tier 2/3渲染: `_render_single_event(event, detailed=False)`
- 添加新部分: 创建`_render_my_section()`并在`render()`中调用

---

## 重要约束

### LLM API限制
- **速率限制**: 约10请求/秒（DashScope）
- **Token限制**: 每次请求8,192 tokens（输入+输出）
- **超时**: 每次调用120秒
- **缓解措施**: 批处理中请求间使用`time.sleep(1)`

### 内存使用
- **嵌入模型**: 约500MB（sentence-transformers）
- **峰值内存**: 聚类时约2GB（200+新闻条目）
- **建议**: 生产环境4GB+内存

### 文件存储
- **原始数据**: 每天约1MB（无限期存储）
- **H5导出**: 每天约100KB（保留最近30天）
- **日志**: 不持久化（仅控制台）

---

## 故障排除

### "ModuleNotFoundError: No module named 'readability'"
```bash
venv/bin/python -m pip install readability-lxml
```

### "DASHSCOPE_API_KEY not set"
- 投资信息抽取会静默失败（回退到本地模式）
- 检查: `echo $DASHSCOPE_API_KEY`
- 设置: `export DASHSCOPE_API_KEY="sk-..."`

### investment_thesis字段为空
- LLM可能返回无效JSON或遗漏字段
- 检查日志中的"JSON 解析失败"错误
- `_validate_and_truncate()`中的验证逻辑会优雅处理

### 所有事件都分类为Tier 3
- 表示综合得分低（<50）
- 检查: `news["investment_scorecard"]["composite_score"]`
- 可能需要调整`investment_scorer.py`中的评分逻辑

### 聚类产生1个巨大集群
- 当新闻条目非常相似时发生
- 调整`src/event/clustering.py`中的`min_cluster_size`
- 默认值: 2（每个集群最少2条新闻）

---

## 文档

- **README.md**: 面向用户的概述、安装、功能
- **CHANGELOG.md**: 版本历史和变更
- **docs/PHASE1_IMPLEMENTATION.md**: 技术实现细节
- **docs/PHASE1_QUICK_REFERENCE.md**: 开发者和分析师指南
- **docs/PHASE1_COMPLETE.md**: Phase 1总结和指标

---

## 开发规范

### 工程架构保持干净
**重要**: 始终保持工程架构整洁：
1. 及时清理临时文件（.history/、*.log、*.bak）
2. 旧文档归档到 `docs/archive/` 而非删除
3. 目录结构清晰，避免根目录文件堆积
4. 测试产物不提交到 git（已在 .gitignore 配置）

### requirements.txt 和 pyproject.toml 保持一致
**重要**: 修改依赖时，必须同时更新两个文件：
1. `requirements.txt` - 用于 `pip install -r`
2. `pyproject.toml` 的 `dependencies` 部分 - 用于 `pip install -e .`
3. 两个文件的包名和版本号必须完全一致
4. 添加新依赖后运行测试验证导入正常

### Feature 完成后必须更新文档
**重要**: 完成 feature 开发和测试后，必须更新 README.md，确保：
1. 新功能在功能列表中有体现
2. 使用方式/命令行参数有更新
3. 安装依赖有更新（如果有新增）
4. 版本号有更新

### 代码提交规范
- 提交前运行测试确保通过
- 提交信息清晰描述变更内容
- 重大功能变更需更新 CHANGELOG.md

---

## 未来阶段（路线图）

- **Phase 2**（第3-4周）: 竞争情报、价值链分析、情绪动量
- **Phase 3**（第2个月）: 前瞻催化剂日历、历史背景数据库
- **Phase 4**（第3-6个月）: 论点追踪、替代数据、个性化

详见对话历史中的优化计划。

---

## Claude Code 权限配置

以下是本项目预授权的安全操作，Claude Code 可以在不额外询问的情况下执行这些操作：

```json
{
  "permissions": {
    "allow": [
      "read:./**",
      "write:./**",
      "command:git *",
      "command:npm *",
      "command:pnpm *",
      "command:yarn *",
      "command:go *",
      "command:pytest",
      "command:make *"
    ]
  }
}
```

### 权限说明

| 权限 | 说明 |
|------|------|
| `read:./**` | 读取项目内任意文件 |
| `write:./**` | 写入项目内任意文件 |
| `command:git *` | 执行 git 命令（status, add, commit, push, pull 等） |
| `command:npm *` | 执行 npm 命令（install, run, test 等） |
| `command:pnpm *` | 执行 pnpm 命令 |
| `command:yarn *` | 执行 yarn 命令 |
| `command:go *` | 执行 go 命令（build, test, run 等） |
| `command:pytest` | 运行 pytest 测试 |
| `command:make *` | 执行 make 构建命令 |

### 安全边界

这些权限仅限于项目目录内的操作，不包括：
- 系统级文件修改
- 网络请求（除构建工具需要的依赖下载）
- 敏感文件（.env、credentials 等）的自动提交
- 破坏性 git 操作（force push、reset --hard 等）
