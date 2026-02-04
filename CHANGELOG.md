# Changelog - AI Investment News Analysis System

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2026-02-04 - Phase 1: Investment Intelligence Upgrade

### Added

#### Investment Thesis Extraction
- Added `InvestmentThesis` dataclass with 5 structured fields:
  - `bull_case`: List of 3 bullish reasons (specific, verifiable)
  - `bear_case`: List of 3 bearish reasons (specific, verifiable)
  - `key_question`: Critical question determining investment outcome
  - `time_horizon`: Impact timeframe (即时/1-3个月/6-12个月/长期)
  - `comparable_events`: Up to 2 historical analogues
- Enhanced LLM prompt in `investment_extractor.py` to extract investment thesis
- Added validation logic for investment thesis structure

#### 7-Dimensional Investment Scorecard
- Created new module `src/selector/investment_scorer.py`
- Implemented `InvestmentScorecard` dataclass with 7 dimensions:
  1. Materiality (重要性): 0-10, financial impact magnitude
  2. Urgency (紧迫性): 0-10, time sensitivity
  3. Conviction (确信度): 0-10, evidence quality
  4. Competitive (竞争影响): 0-10, competitive dynamics
  5. Risk (风险): 0-10, uncertainty level
  6. Innovation (创新度): 0-10, tech/product innovation
  7. Execution (执行力): 0-10, execution feasibility
- Composite score calculation (0-100, weighted average)
- Investment rating system: "Strong Buy Signal" | "Monitor" | "Risk Alert" | "Pass"
- Rule-based scoring (no LLM, zero additional cost)

#### 3-Tier Event Structure
- Refactored event filtering in `article_builder.py` to support 3 tiers:
  - **Tier 1** (High Priority): composite_score >= 70, max 3 events
  - **Tier 2** (Medium Priority): 50 <= composite_score < 70, max 5 events
  - **Tier 3** (Low Priority): composite_score < 50, max 3 events
- Added `_calculate_avg_composite_score()` for event-level scoring
- Added `tier` field to `ArticleEvent` dataclass
- Tier 1 events get detailed rendering (thesis + risk-reward)
- Tier 2 events get condensed rendering
- Tier 3 events get title-only rendering

#### Executive Alert Section
- Added `_render_executive_alerts()` function in `article_renderer.py`
- Generates Top 3 actionable alerts sorted by urgency * materiality
- Displays for each alert:
  - Action category (立即关注/信息监控/常规跟踪)
  - Investment rating (⭐ or ⚠️)
  - Action recommendation (specific guidance)
  - Time window (from investment thesis)
  - Risk level (高/中等/较低)
  - Conviction level (高/中/低)

#### Risk-Reward Assessment
- Added `_render_risk_reward()` function in `article_renderer.py`
- Calculates upside potential (0-5, based on bull_case)
- Calculates downside risk (0-5, based on bear_case + uncertainties)
- Visual bars: 🟢 for upside, 🔴 for downside
- Risk-adjusted assessment: 有利/中性/不利
- Shows top bull/bear reason for context

#### Pipeline Integration
- Added Step 7.5 to main pipeline: Investment scorecard calculation
- Created `_calculate_investment_scorecards()` function in `main.py`
- Scorecard calculated for all news items after investment extraction
- Updated pipeline docstring (11 → 12 steps)

#### Testing & Documentation
- Created `tests/test_phase1_integration.py` with comprehensive integration tests
- Created `docs/PHASE1_IMPLEMENTATION.md` with full implementation details
- Created `docs/PHASE1_QUICK_REFERENCE.md` with user/developer guides

### Changed

#### Report Structure
- **Before**: Flat list of 8 events with equal priority
- **After**: Hierarchical 3-tier structure with prioritized rendering
- Added "🚨 今日重点关注" section at top of report
- Reordered sections:
  1. 标题 + 一句话总览
  2. 🚨 今日重点关注（新增）
  3. 一、核心事件（高优先级）（新增层级）
  4. 二、值得关注（中等优先级）（新增层级）
  5. 三、参考信息（低优先级）（新增层级）
  6. 四、市场信号汇总
  7. 五、今日值得持续关注的方向

#### Event Rendering
- Tier 1 events now include:
  - 📊 投资评分卡 (7 dimensions + composite score)
  - 💰 投资论点 (bull/bear case, key question, time horizon)
  - ⚖️ 风险-收益评估 (visual bars + assessment)
- Tier 2 events: Condensed format (no thesis/scorecard)
- Tier 3 events: Title-only format

#### Data Flow
- News objects now include `investment_scorecard` field after Step 7.5
- Events now include `tier` field during article building
- Scorecard data flows through: news → events → rendering

### Performance

#### Cost Impact
- **Before**: ~$0.50/report (Qwen Plus, 6 dimensions)
- **After**: ~$0.80/report (+60%, not 3x as estimated)
- Reason: Thesis extraction added to existing LLM call, not separate call
- Scorecard calculation: $0 (rule-based, no LLM)

#### Latency Impact
- **Before**: ~10 minutes end-to-end
- **After**: ~11 minutes (+10%)
- Breakdown: +1 min (LLM with larger prompts), +10s (scorecard calculation)
- Still under 15-minute target ✅

### Technical Details

#### Files Modified
- `src/fetch/investment_extractor.py`: +90 lines
- `src/content/article_builder.py`: +40 lines
- `src/content/article_schema.py`: +1 line
- `src/content/article_renderer.py`: +180 lines
- `src/main.py`: +30 lines

#### Files Added
- `src/selector/investment_scorer.py`: +410 lines
- `tests/test_phase1_integration.py`: +280 lines
- `docs/PHASE1_IMPLEMENTATION.md`
- `docs/PHASE1_QUICK_REFERENCE.md`

#### Dependencies
- No new dependencies added
- All features use existing libraries

---

## [1.0.0] - 2026-01-XX - Initial Release

### Features
- 11-step pipeline for AI investment news analysis
- RSS feed aggregation (86 sources)
- News deduplication and merging
- 6-dimensional investment extraction (LLM-based)
- Event clustering and summarization
- Event decision pipeline
- Markdown report generation
- H5 application data export

### Pipeline Steps
1. Search recent news (SearchPipeline)
2. Normalize news data
3. Article fetching
4. Deduplication and merging
5. Light features extraction
6. News selection (top-k)
7. Investment info extraction (LLM)
8. Event analysis (embedding + clustering)
9. Event decision (importance + signal + action)
10. Article generation
11. H5 data export

### Supported Sources
- 86 RSS feeds across AI/tech news sources
- Concurrent fetching support (configurable)
- Source classification (valid/expired/invalid)

### Investment Dimensions (6D)
1. Facts (明确事实)
2. Numbers (数字/量化信息)
3. Business (商业化信息)
4. Industry Impact (行业影响)
5. Management Claims (管理层表态)
6. Uncertainties (不确定性/风险)

---

## Upcoming Releases

### [1.2.0] - Phase 2: Core Enhancements (Week 3-4)
- [ ] Competitive Intelligence Section
- [ ] Value Chain Impact Analysis
- [ ] Sentiment Momentum Tracker (7-day rolling)

### [1.3.0] - Phase 3: Advanced Intelligence (Month 2)
- [ ] Forward Catalyst Calendar (30-day extraction)
- [ ] Historical Context Database (SQLite)
- [ ] Sentiment inflection detection

### [2.0.0] - Phase 4: System Intelligence (Month 3-6)
- [ ] Thesis Tracking & Validation
- [ ] Alternative Data Integration (GitHub API)
- [ ] Personalization Layer
- [ ] Prediction Accuracy Scorecard

---

## Version History

- **v1.1.0** (2026-02-04): Phase 1 - Investment Intelligence Upgrade
- **v1.0.0** (2026-01-XX): Initial Release - Basic Pipeline

---

## Changelog Guidelines

Types of changes:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features to be removed in future
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

**Maintained by**: AI Investment Analysis Team
**Last Updated**: 2026-02-04
