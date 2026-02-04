# RSS并发抓取优化 - 迁移指南

## 📊 性能提升

- **预期性能提升**: 60-80%
- **串行耗时**: ~86秒（86个源 × 1秒/源）
- **并发耗时**: ~15秒（86个源 / 10并发 × 1.5秒/批次）
- **加速比**: 约5-6倍

## 🚀 快速开始

### 1. 安装新依赖

```bash
pip install aiohttp>=3.8.0
# 或
pip install -r requirements.txt
```

### 2. 使用并发版本（推荐）

#### 方式A: 使用新的SearchPipelineV2（推荐）

```python
from search.search_pipeline_v2 import SearchPipelineV2

# 创建管道（默认使用并发模式）
pipeline = SearchPipelineV2(
    hours=24,
    max_items_per_source=20,
    use_concurrent=True,  # 使用并发（默认）
    max_concurrent=10     # 最大并发数
)

# 运行完整管道
news, stats = pipeline.run_pipeline()

# 或仅运行搜索
news, stats = pipeline.search_recent_ai_news()
```

#### 方式B: 直接使用ConcurrentRSSFetcher

```python
from search.concurrent_rss_fetcher import ConcurrentRSSFetcher

# 创建并发抓取器
fetcher = ConcurrentRSSFetcher(
    hours=24,
    max_items_per_source=20,
    max_concurrent=10,  # 并发数
    timeout=15,         # 超时（秒）
    max_retries=2       # 重试次数
)

# 同步调用
news, stats = fetcher.fetch_rss_sync()

# 异步调用
import asyncio
news, stats = await fetcher.fetch_all_rss_concurrent()
```

### 3. 向后兼容：保持串行模式

```python
from search.search_pipeline_v2 import SearchPipelineV2

# 使用串行模式
pipeline = SearchPipelineV2(
    hours=24,
    use_concurrent=False  # 关闭并发
)

news, stats = pipeline.run_pipeline()
```

## 📝 修改现有代码

### 修改main.py

**原代码**:
```python
from search import SearchPipeline

pipeline = SearchPipeline(hours=hours)
raw_news, search_stats = pipeline.search_recent_ai_news()
```

**新代码**（推荐）:
```python
from search.search_pipeline_v2 import SearchPipelineV2

# 使用并发模式
pipeline = SearchPipelineV2(
    hours=hours,
    use_concurrent=True,
    max_concurrent=10
)
raw_news, search_stats = pipeline.search_recent_ai_news()
```

**或保持原代码不变**（SearchPipeline仍可用）:
```python
from search import SearchPipeline  # 原有代码无需修改

pipeline = SearchPipeline(hours=hours)
raw_news, search_stats = pipeline.search_recent_ai_news()
```

## 🔧 配置参数

### ConcurrentRSSFetcher参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| hours | int | 24 | 搜索时间范围（小时） |
| max_items_per_source | int | 20 | 每个源最大条数 |
| max_concurrent | int | 10 | 最大并发数 |
| timeout | int | 15 | 单个请求超时（秒） |
| max_retries | int | 2 | 最大重试次数 |

### 并发数调优建议

- **低配置机器**: max_concurrent=5
- **标准配置**: max_concurrent=10（推荐）
- **高配置机器**: max_concurrent=15-20
- **注意**: 并发数过高可能触发某些RSS源的限流

## 📈 性能统计

并发版本会在stats中返回额外的性能统计信息：

```python
news, stats = fetcher.fetch_rss_sync()

# 性能统计
perf = stats['performance']
print(f"总耗时: {perf['total_time']:.2f}s")
print(f"平均每源: {perf['avg_time_per_source']:.2f}s")
print(f"成功/失败: {perf['successful_fetches']}/{perf['failed_fetches']}")
```

## 🧪 测试

### 运行性能对比测试

```bash
# 方式1: 直接运行并发抓取器
cd src/search
python concurrent_rss_fetcher.py

# 方式2: 运行SearchPipelineV2测试
python search_pipeline_v2.py
```

### 预期输出

```
性能对比结果
======================================================================
串行模式耗时: 86.34s
并发模式耗时: 15.67s
性能提升: 81.8%
加速比: 5.51x
节省时间: 70.67s
```

## ⚠️ 注意事项

### 1. 网络环境

- **需要稳定的网络连接**
- 某些RSS源可能有访问限制或限流
- 国内访问某些国外源可能较慢

### 2. 错误处理

- 并发版本会自动处理单个源的失败，不影响其他源
- 失败的源会在stats中标记为"error_sources"
- 超时的请求会自动重试（根据max_retries配置）

### 3. 内存使用

- 并发抓取会同时处理多个请求，内存占用略高
- 对于86个源，max_concurrent=10时，额外内存占用约20-50MB

### 4. 兼容性

- **Python版本**: >=3.7（需要asyncio支持）
- **依赖包**: 需要安装aiohttp>=3.8.0
- **向后兼容**: 原有SearchPipeline仍可正常使用

## 🎯 最佳实践

### 1. 生产环境配置

```python
# 生产环境推荐配置
pipeline = SearchPipelineV2(
    hours=24,
    max_items_per_source=20,
    use_concurrent=True,
    max_concurrent=10  # 根据服务器性能调整
)
```

### 2. 监控和日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 运行管道
pipeline = SearchPipelineV2(use_concurrent=True)
news, stats = pipeline.run_pipeline()

# 检查性能统计
if 'performance' in stats['search']:
    perf = stats['search']['performance']
    if perf['total_time'] > 30:
        logger.warning(f"RSS抓取耗时过长: {perf['total_time']:.2f}s")
```

### 3. 错误处理

```python
try:
    pipeline = SearchPipelineV2(use_concurrent=True)
    news, stats = pipeline.run_pipeline()

    # 检查失败的源
    failed = stats['search']['source_classification']['error_sources']
    if failed:
        logger.warning(f"以下源抓取失败: {failed}")

except Exception as e:
    logger.error(f"RSS抓取失败: {e}")
    # 降级到串行模式
    pipeline = SearchPipelineV2(use_concurrent=False)
    news, stats = pipeline.run_pipeline()
```

## 🔄 回滚方案

如果遇到问题，可以快速回滚到串行模式：

### 方法1: 修改配置
```python
pipeline = SearchPipelineV2(use_concurrent=False)
```

### 方法2: 使用原始SearchPipeline
```python
from search import SearchPipeline
pipeline = SearchPipeline(hours=24)
```

## 📞 问题反馈

如遇到问题，请提供以下信息：

1. Python版本
2. 错误日志
3. 网络环境（是否使用代理）
4. stats统计信息

---

**最后更新**: 2026-01-22
**版本**: v1.0
