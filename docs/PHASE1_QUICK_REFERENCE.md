# Phase 1 Quick Reference Guide

## For Developers

### New Data Structures

#### InvestmentThesis
```python
from fetch.investment_extractor import InvestmentThesis

thesis = InvestmentThesis(
    bull_case=["reason1", "reason2", "reason3"],
    bear_case=["risk1", "risk2", "risk3"],
    key_question="What's the key question?",
    time_horizon="6-12个月",  # 即时 | 1-3个月 | 6-12个月 | 长期
    comparable_events=["Historical event 1", "Historical event 2"]
)
```

#### InvestmentScorecard
```python
from selector.investment_scorer import calculate_investment_scorecard

news = {
    "title": "...",
    "source": "...",
    "companies": [...],
    "signals": [...],
    "investment_info": {...},
    "light_features": {...}
}

scorecard = calculate_investment_scorecard(news)
# Returns:
# {
#     "materiality_score": 8.5,
#     "urgency_score": 7.0,
#     "conviction_score": 9.0,
#     "competitive_score": 6.5,
#     "risk_score": 5.0,
#     "innovation_score": 4.0,
#     "execution_score": 5.0,
#     "composite_score": 72.5,
#     "investment_rating": "Monitor",
#     "reasoning": {...}
# }
```

### Pipeline Integration

The investment scorer is automatically called in Step 7.5 of the pipeline:

```python
# In main.py
def generate_ai_news(hours: int = 24):
    # ...
    # Step 7: Investment info extraction (LLM)
    final_news = _extract_investment_info(final_news, stats)

    # Step 7.5: Investment scorecard (rule-based, NEW!)
    final_news = _calculate_investment_scorecards(final_news, stats)

    # Step 8: Event analysis
    events = _analyze_events(final_news, stats)
    # ...
```

### Event Tiering

Events are automatically sorted into 3 tiers based on average composite score:

```python
# Tier 1: composite_score >= 70 (max 3 events)
# Tier 2: 50 <= composite_score < 70 (max 5 events)
# Tier 3: composite_score < 50 (max 3 events)

for event in article.events:
    if event.tier == "tier1":
        # Detailed rendering with investment thesis & risk-reward
    elif event.tier == "tier2":
        # Condensed rendering
    else:
        # Title only
```

---

## For Investment Analysts

### How to Read the New Report

#### 1. Executive Alerts (Top of Report)
```
🚨 今日重点关注（Top 3行动项）

## 1. 【立即关注】OpenAI获66亿美元融资
- 投资评级: ⭐⭐⭐⭐⭐ Strong Buy Signal (87/100)
- 建议行动: 监控Q3财报的毛利率指引
- 时间窗口: 3个月内
- 风险等级: 中等 | 确信度: 高
```

**What to do**: Start here. If you have 2 minutes, read only this section.

#### 2. Investment Scorecard (Tier 1 Events)
```
📊 投资评分卡
  - 综合评级: ⭐⭐⭐⭐⭐ Strong Buy Signal (87/100)
  - 📈 重要性: 9/10 | ⏰ 紧迫性: 8/10 | 🎯 确信度: 9/10
  - 💼 竞争影响: 7/10 | ⚠️ 风险: 6/10 | 🚀 创新度: 8/10
```

**How to interpret**:
- **Composite Score**:
  - 80-100 = Strong Buy Signal (high conviction + high materiality)
  - 65-79 = Monitor (worth tracking)
  - 45-64 = Risk Alert (proceed with caution)
  - 0-44 = Pass (ignore or wait for more info)

- **7 Dimensions**:
  - **Materiality (重要性)**: Financial impact size
  - **Urgency (紧迫性)**: Time sensitivity
  - **Conviction (确信度)**: Evidence quality
  - **Competitive (竞争影响)**: Competitive dynamics
  - **Risk (风险)**: Uncertainty level
  - **Innovation (创新度)**: Tech/product innovation
  - **Execution (执行力)**: Execution feasibility

#### 3. Investment Thesis (Tier 1 Events)
```
💰 投资论点
  - 看涨理由:
    ✅ 企业客户收入可能达50亿美元ARR（当前16亿）
    ✅ 基础设施成本下降，利润率可从30%提升至45%
    ✅ 微软战略支持，技术领先优势明显
  - 看跌理由:
    ❌ 竞争对手降价压力（Anthropic便宜20%）
    ❌ 客户集中度风险，前10名占60%收入
    ❌ 估值过高，市盈率不合理
  - 关键问题: OpenAI能否在模型商品化时保持定价权？
  - 时间周期: 6-12个月
```

**How to use**:
- **Bull Case**: Why this could be a good investment
- **Bear Case**: What could go wrong
- **Key Question**: The critical uncertainty that determines outcome
- **Time Horizon**: When impact will materialize

#### 4. Risk-Reward Assessment (Tier 1 Events)
```
⚖️ 风险-收益评估
  - 上行潜力: 🟢🟢🟢🟢⚪ 4.5/5
    → 企业客户收入可能达50亿美元ARR
  - 下行风险: 🔴🔴🔴🔴🔴 5.0/5
    → 竞争对手降价压力
  - 风险调整收益: 不利（风险大于收益）
```

**How to interpret**:
- **Upside Potential**: Based on bull case strength (0-5 scale)
- **Downside Risk**: Based on bear case + uncertainties (0-5 scale)
- **Risk-Adjusted Return**:
  - **有利（非对称上行空间）**: Upside significantly outweighs risk
  - **中性（风险收益平衡）**: Balanced risk-reward
  - **不利（风险大于收益）**: Risk outweighs potential return

#### 5. Event Tiers

**Tier 1 (核心事件 - 高优先级)**:
- Composite score >= 70
- Max 3 events
- **Full detail**: Investment thesis + risk-reward + scorecard

**Tier 2 (值得关注 - 中等优先级)**:
- Composite score 50-69
- Max 5 events
- **Condensed format**: Overview + key info only

**Tier 3 (参考信息 - 低优先级)**:
- Composite score < 50
- Max 3 events
- **Title only**: Quick reference

---

## Investment Ratings Guide

### ⭐⭐⭐⭐⭐ Strong Buy Signal (80-100)
- **Action**: Deep dive research, consider position sizing
- **Characteristics**: High materiality + high conviction + reasonable risk
- **Example**: Major funding round by tier-1 company with clear revenue path

### ⭐⭐⭐ Monitor (65-79)
- **Action**: Track closely, watch for catalysts
- **Characteristics**: Interesting but need more information or time
- **Example**: New product launch with uncertain market reception

### ⚠️⚠️⚠️ Risk Alert (45-64)
- **Action**: Be cautious, understand risks before acting
- **Characteristics**: Significant uncertainties or red flags
- **Example**: Regulatory investigation, management turnover

### 📊 Pass (0-44)
- **Action**: Ignore or wait for more clarity
- **Characteristics**: Low materiality or conviction, or too risky
- **Example**: Small startup funding, unverified rumors

---

## Common Workflows

### Workflow 1: Morning Briefing (5 minutes)
1. Read **Executive Alerts** (Top 3)
2. Scan **Tier 1 Event Titles**
3. Done

### Workflow 2: Deep Dive (30 minutes)
1. Read **Executive Alerts**
2. Read **Full Tier 1 Events** (投资论点 + 风险收益)
3. Click through to **重要文章** for more context
4. Review **Tier 2 Events** for additional signals

### Workflow 3: Portfolio Review (60 minutes)
1. Complete Workflow 2
2. Check **市场信号汇总** for sector trends
3. Review **值得持续关注的方向**
4. Cross-reference with existing portfolio holdings
5. Identify action items (buy/sell/monitor)

---

## FAQ

### Q: Why is the composite score different from my intuition?
A: The scorecard uses a weighted formula:
- Materiality: 25%
- Urgency: 20%
- Conviction: 20%
- Competitive: 15%
- Risk (inverse): 10%
- Innovation: 10%

High materiality (财务影响) matters most. If an event has low materiality, it can't score high overall.

### Q: How is "time horizon" determined?
A: Extracted from investment thesis via LLM. Look for:
- "即时": Immediate impact (earnings reports, regulatory decisions)
- "1-3个月": Short-term catalysts (product launches, quarterly results)
- "6-12个月": Medium-term trends (business model shifts, market share changes)
- "长期": Long-term themes (technology paradigm shifts)

### Q: Can I customize the scoring weights?
A: Yes! Edit `src/selector/investment_scorer.py`:
```python
self.weights = {
    "materiality": 0.25,   # Change this
    "urgency": 0.20,
    "conviction": 0.20,
    "competitive": 0.15,
    "risk": 0.10,
    "innovation": 0.10,
}
```

### Q: What if I want more/fewer tier 1 events?
A: Edit `src/content/article_builder.py`:
```python
return {
    "tier1": tier1_events[:3],   # Change from 3 to N
    "tier2": tier2_events[:5],
    "tier3": tier3_events[:3]
}
```

### Q: How much does this cost?
A: Phase 1 adds ~$0.30 per report (+60% from $0.50 to $0.80).
- Investment thesis extraction: Included in Step 7 LLM call
- Scorecard calculation: Free (rule-based, no LLM)

---

## Tips & Best Practices

### For Analysts
1. **Start with Executive Alerts**: Don't read sequentially. Jump to high-priority items first.
2. **Focus on Key Question**: The "key question" often reveals the real risk.
3. **Use Comparable Events**: Historical parallels help calibrate expectations.
4. **Check Time Horizon**: Align with your investment timeframe (short-term trader vs long-term holder).
5. **Risk-Reward Matters More Than Score**: A 65-score event with asymmetric upside beats an 80-score with balanced risk-reward.

### For Developers
1. **Scorecard is Extensible**: Add more dimensions in `investment_scorer.py` if needed.
2. **Thesis Validation**: Consider adding `thesis.validate()` to check for logical consistency.
3. **Historical Tracking**: Store scorecards over time to build performance metrics (Phase 4).
4. **User Feedback Loop**: Track which alerts users act on to improve scoring.

---

## Troubleshooting

### Issue: Investment thesis is empty
**Cause**: LLM failed to extract or returned invalid JSON
**Solution**: Check `news["investment_info"]["investment_thesis"]` in logs. May need prompt tuning.

### Issue: All events are Tier 3
**Cause**: Composite scores are all low (< 50)
**Solution**: Check scorecard calculation. May indicate:
- Low-quality news sources
- Missing investment_info fields
- Need to adjust scoring thresholds

### Issue: Executive alerts show low-score events
**Cause**: Urgency * materiality sorting may surface important but risky events
**Solution**: This is by design. Alerts prioritize time-sensitive items even if overall score is moderate.

---

## Resources

- **Implementation Doc**: `docs/PHASE1_IMPLEMENTATION.md`
- **Original Plan**: See optimization plan in conversation history
- **Test File**: `tests/test_phase1_integration.py`
- **Example Report**: `/tmp/test_phase1_report.md`

---

**Last Updated**: 2026-02-04
