# AI 投资信息系统优化方案

## 一、当前系统架构评估

### 1.1 系统优势
| 维度 | 优势点 |
|------|--------|
| **架构设计** | 10步流水线设计清晰，模块化程度高，职责分离良好 |
| **成本控制** | 轻量化特征抽取在前，LLM调用后置，有效控制成本 |
| **数据完整性** | 全链路数据保留，不丢失信息 |
| **可扩展性** | 配置驱动，易于调整参数和规则 |

### 1.2 核心问题诊断

```
┌─────────────────────────────────────────────────────────┐
│  🔴 关键问题优先级排序                                    │
├─────────────────────────────────────────────────────────┤
│  P0 - 信息源单一（仅RSS，缺乏一手数据源）                   │
│  P0 - 评分模型过于简单（规则硬编码，无法学习优化）           │
│  P1 - 时效性不足（24小时窗口，无实时追踪）                  │
│  P1 - 缺乏行业图谱（公司/行业/产业链关系）                  │
│  P2 - 决策层过于粗糙（仅3级重要性+3类信号）                 │
│  P2 - 缺乏历史对比和趋势分析                              │
└─────────────────────────────────────────────────────────┘
```

---

## 二、信息源优化方案（广度提升）

### 2.1 当前信息源分析

当前RSS源分布（70+个）：
- A. 一线科技/投资媒体：10个
- B. AI专业媒体：10个
- C. 大厂官方博客：10个
- D. 投融资/创投：10个
- E. 芯片/半导体：10个
- F. 社区信号：8个
- G. 研究/学术：10个

**问题**：
1. **缺乏一手数据源**：SEC Filing、专利数据库、招聘数据
2. **缺乏社交媒体信号**：Twitter/X、LinkedIn（高管动态）
3. **缺乏财报数据**：Earnings Call Transcript、财务数据API
4. **地域覆盖不均**：中国市场信息源不足（仅公司博客）

### 2.2 建议新增信息源

#### 2.2.1 一手数据源（高价值）

| 数据源 | 类型 | 价值 | 实现方式 |
|--------|------|------|----------|
| **SEC EDGAR** | 监管文件 | ⭐⭐⭐⭐⭐ | 8-K、10-K、13F 文件解析 |
| **专利数据库** | 技术动态 | ⭐⭐⭐⭐ | USPTO API、Google Patents |
| **招聘平台** | 业务信号 | ⭐⭐⭐⭐ | LinkedIn Jobs、Greenhouse |
| **GitHub** | 技术趋势 | ⭐⭐⭐ | Star/Fork 趋势、Release 监控 |
| **Crunchbase API** | 融资数据 | ⭐⭐⭐⭐⭐ | 实时融资、估值数据 |

#### 2.2.2 社交媒体信号

```python
# 建议新增的社交媒体监控配置
SOCIAL_SOURCES = {
    "twitter_accounts": [
        # 行业关键人物
        "@sama",           # Sam Altman
        "@elonmusk",       # Elon Musk  
        "@satlonak",       # Satya Nadella
        "@JensenHuang",    # Jensen Huang
        "@ylecun",         # Yann LeCun
        # 机构账号
        "@OpenAI",
        "@AnthropicAI",
        "@nvidia",
        "@Microsoft",
    ],
    "linkedin_company_pages": [
        "nvidia", "openai", "anthropic", "microsoft-ai"
    ],
    "reddit_subreddits": [
        "r/wallstreetbets",    # 散户情绪
        "r/stocks",            # 投资讨论
        "r/LocalLLaMA",        # 开源AI动态
    ]
}
```

#### 2.2.3 中国市场信息源

| 数据源 | 内容 | RSS/API |
|--------|------|---------|
| 36氪 | 科技创投 | https://36kr.com/feed |
| 机器之心 | AI专业 | https://www.jiqizhixin.com/rss |
| 量子位 | AI动态 | RSS可获取 |
| 巨潮资讯 | A股公告 | API（需申请） |
| 东方财富 | 财经资讯 | RSS可获取 |
| 雪球 | 投资社区 | API（需爬取） |

### 2.3 信息源质量评估体系

建议新增**信息源动态权重**机制：

```python
# 信息源质量评估配置
SOURCE_QUALITY_CONFIG = {
    # 权威性评分（静态）
    "authority_scores": {
        "Financial Times": 10,
        "Bloomberg": 10,
        "Reuters": 9,
        "Wall Street Journal": 9,
        "SEC EDGAR": 10,  # 一手数据最高分
        "TechCrunch": 7,
        "VentureBeat": 6,
        "Reddit": 4,
        "Twitter": 3,
    },
    # 时效性权重（动态计算）
    "freshness_decay": {
        "1h": 1.0,
        "6h": 0.9,
        "12h": 0.7,
        "24h": 0.5,
        "48h": 0.3,
    },
    # 准确性追踪（需要历史数据）
    "accuracy_tracking": True,  # 追踪预测准确率
}
```

---

## 三、分析策略优化方案

### 3.1 评分模型优化

#### 3.1.1 当前评分规则问题

```python
# 当前硬编码规则（问题示例）
EVENT_RULES = {
    "earnings": {"keywords": ["earnings", "revenue", "profit"], "score": 3.0},
    "funding": {"keywords": ["funding", "raised", "series"], "score": 2.5},
    # ... 固定分数，无法适应市场变化
}
```

**问题**：
1. 分数固定，无法根据市场热点动态调整
2. 关键词匹配过于简单，容易误判
3. 缺乏上下文理解（如"亏损"和"盈利"都匹配"profit"）

#### 3.1.2 建议：多维度评分模型

```python
# 建议的评分模型架构
class InvestmentScorer:
    """多维度投资评分模型"""
    
    def __init__(self):
        self.dimensions = {
            # 维度1：事件重要性（0-10分）
            "event_importance": EventImportanceScorer(),
            # 维度2：信息质量（0-10分）
            "information_quality": InformationQualityScorer(),
            # 维度3：市场影响（0-10分）
            "market_impact": MarketImpactScorer(),
            # 维度4：时效性（0-10分）
            "timeliness": TimelinessScorer(),
            # 维度5：可信度（0-10分）
            "credibility": CredibilityScorer(),
        }
        
        # 动态权重（可基于历史表现调整）
        self.weights = {
            "event_importance": 0.30,
            "information_quality": 0.20,
            "market_impact": 0.25,
            "timeliness": 0.15,
            "credibility": 0.10,
        }
    
    def score(self, news: Dict) -> float:
        """计算综合评分"""
        total = 0
        breakdown = {}
        for dim, scorer in self.dimensions.items():
            dim_score = scorer.score(news)
            breakdown[dim] = dim_score
            total += dim_score * self.weights[dim]
        return total, breakdown
```

#### 3.1.3 事件重要性细化

```python
# 细化的事件类型（从投资视角）
EVENT_TAXONOMY = {
    "financial_events": {
        "earnings_beat": {"base_score": 8, "volatility": "high"},
        "earnings_miss": {"base_score": 7, "volatility": "high"},
        "guidance_raise": {"base_score": 9, "volatility": "high"},
        "guidance_cut": {"base_score": 9, "volatility": "high"},
        "dividend_change": {"base_score": 5, "volatility": "low"},
    },
    "corporate_events": {
        "ceo_change": {"base_score": 8, "volatility": "medium"},
        "major_acquisition": {"base_score": 9, "volatility": "high"},
        "layoffs": {"base_score": 6, "volatility": "medium"},
        "new_product": {"base_score": 7, "volatility": "medium"},
    },
    "regulatory_events": {
        "sec_investigation": {"base_score": 8, "volatility": "high"},
        "antitrust_action": {"base_score": 9, "volatility": "high"},
        "new_regulation": {"base_score": 7, "volatility": "medium"},
    },
    "market_events": {
        "funding_round": {"base_score": 6, "volatility": "low"},
        "ipo_filing": {"base_score": 8, "volatility": "high"},
        "partnership": {"base_score": 5, "volatility": "low"},
    },
}
```

### 3.2 LLM 分析策略优化

#### 3.2.1 当前 Prompt 问题

当前 Prompt 设计良好，但存在以下问题：
1. **缺乏投资视角的优先级判断**：6维度平权，未区分轻重
2. **缺乏竞品对比分析**：无法自动关联竞争对手动态
3. **缺乏历史context**：每次分析独立，无法参考历史事件

#### 3.2.2 建议：增强 Prompt 设计

```python
ENHANCED_INVESTMENT_PROMPT = """
你是一位管理500亿美元AUM的AI/科技行业投资组合经理。

【分析框架】请从以下维度分析，按投资决策价值排序：

1. 【可交易信号】（最高优先级）
   - 是否有明确的买入/卖出信号？
   - 预期股价影响幅度？（+/-）
   - 最佳交易窗口？

2. 【财务影响】
   - 对收入/利润的具体影响
   - 对估值模型的影响
   - 与市场预期的差异

3. 【竞争格局】
   - 对竞争对手的影响（受益者/受损者）
   - 市场份额变化预期
   - 护城河变化

4. 【产业链影响】
   - 上游供应商影响
   - 下游客户影响
   - 替代品/互补品

5. 【风险评估】
   - 执行风险（概率、影响）
   - 监管风险
   - 市场风险

【输出格式】
{{
    "trading_signal": {{
        "direction": "BUY/SELL/HOLD",
        "confidence": 0.0-1.0,
        "target_companies": ["公司1", "公司2"],
        "time_horizon": "short/medium/long"
    }},
    "financial_impact": {{...}},
    "competitive_impact": {{...}},
    "supply_chain_impact": {{...}},
    "risk_assessment": {{...}},
    "ai_summary": "..."
}}
"""
```

### 3.3 事件聚类优化

#### 3.3.1 当前聚类问题

1. **单一嵌入模型**：`all-MiniLM-L6-v2` 对中文支持弱
2. **静态阈值**：`EVENT_DETECTION_THRESHOLD = 0.5` 无法自适应
3. **缺乏时间维度**：相同主题在不同时间应视为不同事件

#### 3.3.2 建议：多维度聚类策略

```python
class EnhancedEventClusterer:
    """增强的事件聚类器"""
    
    def __init__(self):
        # 多语言嵌入模型
        self.embedding_models = {
            "en": "all-MiniLM-L6-v2",
            "zh": "paraphrase-multilingual-MiniLM-L12-v2",
        }
        
    def cluster(self, news_list: List[Dict]) -> List[Event]:
        """多维度聚类"""
        # 1. 语义相似度聚类
        semantic_clusters = self._semantic_cluster(news_list)
        
        # 2. 实体共现聚类（相同公司/人物）
        entity_clusters = self._entity_cluster(news_list)
        
        # 3. 时间窗口聚类
        temporal_clusters = self._temporal_cluster(news_list)
        
        # 4. 融合聚类结果
        final_clusters = self._merge_clusters(
            semantic_clusters, 
            entity_clusters,
            temporal_clusters
        )
        
        return final_clusters
```

---

## 四、决策层优化方案

### 4.1 当前决策层问题

```python
# 当前过于简化的决策逻辑
IMPORTANCE_THRESHOLDS = {
    "high": {"min_news": 3, "min_sources": 2, "min_score": 0.6},
    "medium": {"min_news": 2, "min_sources": 1, "min_score": 0.3},
}
# 仅基于数量判断，缺乏内容深度分析
```

### 4.2 建议：细化决策框架

```python
# 细化的投资决策框架
DECISION_FRAMEWORK = {
    # 决策类型（从Watch/Hold/Avoid扩展）
    "actions": {
        "STRONG_BUY": "立即买入信号，高确定性",
        "BUY": "买入信号，需要进一步确认",
        "ACCUMULATE": "逢低加仓，长期看好",
        "HOLD": "持有观望，无明确信号",
        "REDUCE": "减仓信号，风险上升",
        "SELL": "卖出信号，需要及时行动",
        "AVOID": "回避，风险过高",
    },
    
    # 时间维度
    "time_horizons": {
        "IMMEDIATE": "24小时内需要行动",
        "SHORT": "1周内观察",
        "MEDIUM": "1-3个月趋势",
        "LONG": "长期结构性变化",
    },
    
    # 确定性等级
    "confidence_levels": {
        "HIGH": "> 80% 确定性",
        "MEDIUM": "50-80% 确定性",
        "LOW": "< 50% 确定性",
    },
}
```

### 4.3 建议：增加投资组合视角

```python
class PortfolioDecisionEngine:
    """投资组合决策引擎"""
    
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio  # 当前持仓
        
    def decide(self, event: Event) -> PortfolioAction:
        """基于持仓的决策"""
        affected_holdings = self._find_affected_holdings(event)
        
        actions = []
        for holding in affected_holdings:
            impact = self._assess_impact(event, holding)
            action = self._generate_action(impact)
            actions.append(action)
        
        # 考虑整体组合风险
        portfolio_risk = self._assess_portfolio_risk(actions)
        
        return PortfolioAction(
            individual_actions=actions,
            portfolio_adjustment=self._optimize_portfolio(portfolio_risk),
            risk_metrics=portfolio_risk,
        )
```

---

## 五、新增功能建议

### 5.1 行业知识图谱

```python
# 建议新增：行业知识图谱模块
INDUSTRY_KNOWLEDGE_GRAPH = {
    # 公司关系图谱
    "company_relations": {
        "NVIDIA": {
            "competitors": ["AMD", "Intel", "Qualcomm"],
            "customers": ["Microsoft", "Google", "Meta", "Amazon"],
            "suppliers": ["TSMC", "Samsung"],
            "partners": ["Microsoft", "SAP", "VMware"],
        },
        "OpenAI": {
            "competitors": ["Anthropic", "Google DeepMind", "Meta AI"],
            "investors": ["Microsoft", "Khosla Ventures", "Thrive Capital"],
            "partners": ["Microsoft", "Apple"],
        },
    },
    
    # 产业链映射
    "supply_chain": {
        "AI_chips": ["NVIDIA", "AMD", "Intel", "Qualcomm"],
        "foundry": ["TSMC", "Samsung", "GlobalFoundries"],
        "memory": ["SK Hynix", "Micron", "Samsung"],
        "cloud_infra": ["AWS", "Azure", "GCP"],
    },
    
    # 自动关联：当NVIDIA有重大新闻时，自动分析对AMD/Intel/TSMC的影响
}
```

### 5.2 历史趋势分析

```python
# 建议新增：历史对比分析模块
class HistoricalAnalyzer:
    """历史趋势分析器"""
    
    def analyze_trend(self, company: str, event_type: str) -> TrendAnalysis:
        """分析历史趋势"""
        # 1. 获取历史同类事件
        historical_events = self._get_historical_events(company, event_type)
        
        # 2. 分析股价反应模式
        price_patterns = self._analyze_price_reaction(historical_events)
        
        # 3. 计算预期影响
        expected_impact = self._calculate_expected_impact(price_patterns)
        
        return TrendAnalysis(
            historical_events=historical_events,
            price_patterns=price_patterns,
            expected_impact=expected_impact,
            confidence=self._calculate_confidence(len(historical_events)),
        )
```

### 5.3 实时监控与预警

```python
# 建议新增：实时监控模块
ALERT_CONFIG = {
    # 价格异动预警
    "price_alerts": {
        "threshold": 0.05,  # 5% 波动
        "companies": ["NVDA", "MSFT", "GOOGL", "META"],
    },
    
    # 关键人物动态
    "key_person_alerts": [
        "@sama", "@elonmusk", "@JensenHuang",
    ],
    
    # 监管动态
    "regulatory_alerts": [
        "SEC", "FTC", "DOJ", "EU Commission",
    ],
    
    # 自定义关键词
    "keyword_alerts": [
        "layoffs", "acquisition", "IPO", "bankruptcy",
    ],
}
```

---

## 六、技术实现优先级

### 6.1 实施路线图

```
Phase 1（1-2周）- 快速提升
├── 增加 SEC EDGAR 数据源
├── 优化评分模型（细化事件类型）
├── 增加中国市场信息源
└── 优化 LLM Prompt

Phase 2（3-4周）- 深度优化
├── 实现行业知识图谱
├── 增加社交媒体监控
├── 实现历史趋势分析
└── 细化决策框架

Phase 3（5-8周）- 高级功能
├── 实时监控与预警系统
├── 投资组合决策引擎
├── 多语言支持（中英文）
└── 可视化仪表盘
```

### 6.2 预期效果

| 指标 | 当前水平 | 优化后预期 |
|------|----------|------------|
| 信息源覆盖 | 70+ RSS | 150+ 多类型 |
| 一手信息比例 | 0% | 30%+ |
| 中国市场覆盖 | 10% | 50%+ |
| 事件识别准确率 | ~70% | 85%+ |
| 投资信号可操作性 | 低 | 中高 |
| 决策响应时间 | 24h | 实时 |

---

## 七、总结

### 7.1 核心改进方向

1. **信息源广度**：从RSS扩展到一手数据源（SEC、专利、招聘）
2. **分析深度**：从关键词匹配到多维度投资评分模型
3. **决策精度**：从3级粗糙决策到细化投资行动建议
4. **时效性**：从24小时批处理到实时监控预警
5. **关联分析**：从单条新闻分析到产业链影响分析

### 7.2 风险提示

- 增加信息源会增加系统复杂度和维护成本
- LLM API调用成本会随着分析深度增加
- 实时监控需要稳定的基础设施支持
- 投资决策最终需要人工审核确认

---

*本优化方案将随着讨论持续更新，版本：v1.0*

---

## 八、阿里云部署方案

### 8.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     阿里云                                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  定时任务 (main)  │    │      静态网站托管 (webapp)       │ │
│  │                 │    │                                 │ │
│  │  方案: ECS      │    │  方案: OSS + CDN                │ │
│  │                 │    │                                 │ │
│  │  每天 18:00 执行  │───▶│  外网访问 H5 应用                │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                    ▲
                    │ 部署
┌─────────────────────────────────────────────────────────────┐
│               本地开发环境 (Mac)                              │
│  - rsync/scp 同步代码                                        │
│  - ossutil 同步 webapp                                       │
│  - 一键部署脚本                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 成本估算（月）

| 服务 | 规格 | 费用 |
|------|------|------|
| ECS | ecs.t6-c1m1.large (2核2G) | ~¥50-80 |
| OSS | 标准存储 + 流量 | ~¥5-10 |
| **总计** | | **~¥60-90/月** |

---

### 8.3 Part 1: main 定时任务部署（ECS）

#### 8.3.1 购买 ECS 服务器

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 创建实例：
   - **地域**：选择离你近的（如华东1-杭州）
   - **实例规格**：ecs.t6-c1m1.large（2核2G，足够运行）
   - **镜像**：Ubuntu 22.04 LTS
   - **存储**：40GB 高效云盘
   - **带宽**：按流量计费，5Mbps
   - **安全组**：开放 22(SSH)、80、443 端口

3. 记录服务器信息：
   ```
   公网IP: <YOUR_ECS_IP>
   用户名: root
   密码/密钥: <YOUR_PASSWORD>
   ```

#### 8.3.2 服务器环境配置

SSH 登录服务器后执行：

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装 Python 3.10+ 和依赖
apt install -y python3 python3-pip python3-venv git

# 3. 创建项目目录
mkdir -p /opt/ai-invest
cd /opt/ai-invest

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装 ossutil（用于同步 webapp 数据到 OSS）
wget https://gosspublic.alicdn.com/ossutil/1.7.16/ossutil-v1.7.16-linux-amd64.zip
unzip ossutil-v1.7.16-linux-amd64.zip
mv ossutil-v1.7.16-linux-amd64/ossutil64 /usr/local/bin/ossutil
chmod +x /usr/local/bin/ossutil
```

#### 8.3.3 配置环境变量

```bash
# 创建环境变量文件
cat > /opt/ai-invest/.env << 'EOF'
# 阿里云 DashScope API Key（用于 AI 模型调用）
DASHSCOPE_API_KEY=your_dashscope_api_key

# OSS 配置（用于同步 webapp 数据）
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET=your-bucket-name
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
EOF

# 配置 ossutil
ossutil config -e oss-cn-hangzhou.aliyuncs.com -i <ACCESS_KEY_ID> -k <ACCESS_KEY_SECRET>
```

#### 8.3.4 创建定时任务脚本

在服务器上创建 `/opt/ai-invest/run_daily.sh`：

```bash
#!/bin/bash
# AI 投资新闻每日定时任务

set -e

# 配置
PROJECT_DIR="/opt/ai-invest"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/run_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p ${LOG_DIR}

# 激活虚拟环境
source ${PROJECT_DIR}/venv/bin/activate

# 加载环境变量
export $(cat ${PROJECT_DIR}/.env | xargs)

# 切换到源码目录
cd ${PROJECT_DIR}/src

# 执行主程序
echo "========== 开始执行 $(date) ==========" >> ${LOG_FILE}
python main.py >> ${LOG_FILE} 2>&1
echo "========== 执行完成 $(date) ==========" >> ${LOG_FILE}

# 同步 webapp/data 到 OSS
echo "========== 同步到 OSS ==========" >> ${LOG_FILE}
ossutil cp -r ${PROJECT_DIR}/webapp/data/ oss://${OSS_BUCKET}/data/ --update >> ${LOG_FILE} 2>&1

echo "========== 全部完成 $(date) ==========" >> ${LOG_FILE}

# 清理 7 天前的日志
find ${LOG_DIR} -name "run_*.log" -mtime +7 -delete
```

设置执行权限：
```bash
chmod +x /opt/ai-invest/run_daily.sh
```

#### 8.3.5 配置 Crontab 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 18:00 执行）
0 18 * * * /opt/ai-invest/run_daily.sh

# 查看定时任务
crontab -l
```

---

### 8.4 Part 2: webapp 部署（OSS + CDN）

#### 8.4.1 创建 OSS Bucket

1. 登录 [OSS 控制台](https://oss.console.aliyun.com/)
2. 创建 Bucket：
   - **名称**：ai-invest-webapp（自定义）
   - **地域**：与 ECS 同区域
   - **存储类型**：标准存储
   - **读写权限**：公共读

#### 8.4.2 配置静态网站托管

1. 进入 Bucket → **基础设置** → **静态网站托管**
2. 开启静态网站托管：
   - **默认首页**：index.html
   - **默认 404 页**：（可留空）

3. 记录访问域名：
   ```
   http://ai-invest-webapp.oss-cn-hangzhou.aliyuncs.com
   ```

#### 8.4.3 初次上传 webapp

```bash
# 在 ECS 服务器上执行
ossutil cp -r /opt/ai-invest/webapp/ oss://ai-invest-webapp/ --update
```

#### 8.4.4 （可选）绑定自定义域名 + CDN

1. OSS 控制台 → **传输管理** → **域名管理**
2. 绑定已备案的域名（如 `invest.yourdomain.com`）
3. 开启 CDN 加速

---

### 8.5 Part 3: 本地开发环境部署脚本

#### 8.5.1 部署配置文件

`deploy/config.sh`：
```bash
#!/bin/bash
# 部署配置

# ECS 服务器配置
ECS_HOST="your_ecs_ip"
ECS_USER="root"
ECS_PROJECT_DIR="/opt/ai-invest"

# OSS 配置
OSS_BUCKET="ai-invest-webapp"
OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
```

#### 8.5.2 代码部署脚本

`deploy/deploy_main.sh`：
```bash
#!/bin/bash
# 部署 main 程序到 ECS

set -e

# 加载配置
source "$(dirname "$0")/config.sh"

echo "🚀 开始部署 main 到 ECS..."

# 同步代码（排除不需要的文件）
rsync -avz --progress \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='raw_data' \
    --exclude='output' \
    --exclude='tests' \
    --exclude='webapp/data/*.json' \
    ./ ${ECS_USER}@${ECS_HOST}:${ECS_PROJECT_DIR}/

# 在服务器上安装依赖
ssh ${ECS_USER}@${ECS_HOST} << 'ENDSSH'
cd /opt/ai-invest
source venv/bin/activate
pip install -r requirements.txt -q
echo "✅ 依赖安装完成"
ENDSSH

echo "✅ main 部署完成！"
```

#### 8.5.3 webapp 部署脚本

`deploy/deploy_webapp.sh`：
```bash
#!/bin/bash
# 部署 webapp 到 OSS

set -e

# 加载配置
source "$(dirname "$0")/config.sh"

echo "🚀 开始部署 webapp 到 OSS..."

# 使用 ossutil 同步（需要本地安装 ossutil）
ossutil cp -r webapp/ oss://${OSS_BUCKET}/ \
    --update \
    --exclude "*.json" \
    -e ${OSS_ENDPOINT}

echo "✅ webapp 静态文件部署完成！"
echo "📱 访问地址: http://${OSS_BUCKET}.${OSS_ENDPOINT}"
```

#### 8.5.4 一键部署脚本

`deploy/deploy_all.sh`：
```bash
#!/bin/bash
# 一键部署所有内容

set -e

SCRIPT_DIR="$(dirname "$0")"

echo "=========================================="
echo "       AI 投资新闻系统 - 一键部署"
echo "=========================================="

# 部署 main
echo ""
echo "[1/2] 部署 main 程序..."
bash "${SCRIPT_DIR}/deploy_main.sh"

# 部署 webapp
echo ""
echo "[2/2] 部署 webapp..."
bash "${SCRIPT_DIR}/deploy_webapp.sh"

echo ""
echo "=========================================="
echo "           ✅ 全部部署完成！"
echo "=========================================="
```

#### 8.5.5 设置脚本权限

```bash
chmod +x deploy/*.sh
```

---

### 8.6 快速开始步骤

#### 步骤 1：准备阿里云资源
```bash
# 1. 购买 ECS 服务器
# 2. 创建 OSS Bucket
# 3. 获取 AccessKey（RAM 子账户推荐）
# 4. 获取 DashScope API Key
```

#### 步骤 2：配置本地环境
```bash
# 安装 ossutil（Mac）
brew install aliyun-cli

# 配置 ossutil
ossutil config
```

#### 步骤 3：首次部署
```bash
# 在项目根目录执行
./deploy/deploy_all.sh
```

#### 步骤 4：验证部署
```bash
# 1. 登录 ECS 手动测试
ssh root@<ECS_IP>
cd /opt/ai-invest
source venv/bin/activate
python src/main.py

# 2. 访问 webapp
# http://ai-invest-webapp.oss-cn-hangzhou.aliyuncs.com
```

---

### 8.7 目录结构（最终）

```
ai-invest-news/
├── deploy/                    # 新增：部署脚本
│   ├── config.sh             # 部署配置
│   ├── deploy_main.sh        # 部署 main 到 ECS
│   ├── deploy_webapp.sh      # 部署 webapp 到 OSS
│   └── deploy_all.sh         # 一键部署
├── src/                      # 源代码
├── webapp/                   # H5 应用
├── tests/                    # 测试
├── requirements.txt          # Python 依赖
└── README.md
```

---

### 8.8 部署检查清单

- [ ] 阿里云账号已注册
- [ ] ECS 服务器已购买并配置
- [ ] OSS Bucket 已创建并开启静态网站托管
- [ ] AccessKey 已获取（推荐使用 RAM 子账户）
- [ ] DashScope API Key 已获取
- [ ] 本地 ossutil 已安装并配置
- [ ] 部署脚本已创建并设置权限
- [ ] Crontab 定时任务已配置
- [ ] （可选）自定义域名已备案并绑定

---

*部署方案版本：v1.0*