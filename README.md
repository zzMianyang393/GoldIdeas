# GoldIdeas Demand Pipeline V4.1

纯 Python 规则引擎驱动的 SaaS 创意验证管道，后端固定在 `server/`，网页检阅界面固定在 `web/`。

## 信息源

系统不只依赖 Reddit。当前默认来源包括：

- Reddit RSS: 12 个独立开发 / SaaS / 小企业相关 subreddit
- Hacker News RSS
- Hacker News Algolia 搜索
- Product Hunt RSS
- Indie Hackers RSS（若源不可解析，会记录异常并跳过）

单个来源失败不会中断整次扫描，异常会写入报告。

## 运行

Windows 当前环境里 `python` 指向 2.7，请使用 `py -3`。

```powershell
py -3 -m pip install -r server\requirements.txt
py -3 server\app.py
```

然后打开：

```text
http://127.0.0.1:8765
```

## CLI

```powershell
py -3 server\demand_pipeline.py
py -3 server\demand_pipeline.py --quick
py -3 server\demand_pipeline.py --rating green
py -3 server\demand_pipeline.py --subreddits indiehackers,microsaas
py -3 server\demand_pipeline.py --limit 50
```

输出文件：

- `server/data/raw_posts.json`
- `server/data/opportunities.json`
- `server/data/reports/YYYY-MM-DD.md`
- `server/data/goldideas.db`

## Server API

```text
GET  /api/status
GET  /api/report
GET  /api/runs
GET  /api/sources
GET  /api/sources/{id}
GET  /api/search-jobs
GET  /api/search-jobs/{id}
GET  /api/ai/report?opportunity_id=opp_xxx
POST /api/scan
POST /api/search-jobs
POST /api/sources
POST /api/sources/{id}
POST /api/ai/report
```

`POST /api/scan` 支持自定义搜索参数：

```json
{
  "limit": 10,
  "query": "shopify returns",
  "opportunity_type": "ecommerce_tools",
  "rating": "",
  "quick": true,
  "include_keywords": ["returns"],
  "exclude_keywords": ["jobs"],
  "ai_depth": "none"
}
```

当前支持的 `opportunity_type`：

- `micro_saas`
- `developer_tools`
- `ecommerce_tools`

`POST /api/ai/report` 会根据 `opportunity_id` 获取或生成可行性报告。当前实现是零 token 的本地占位报告，用于验证缓存、数据库和 API 流程；后续可以替换为真实 AI provider。

```json
{
  "opportunity_id": "opp_xxx",
  "report_type": "feasibility",
  "force": false
}
```

`POST /api/search-jobs` 会创建搜索任务、同步执行扫描、记录任务状态，并返回本次 run 与 opportunity 结果。

`POST /api/sources` 可创建或更新来源：

```json
{
  "id": "custom_feed",
  "name": "Custom Feed",
  "type": "rss",
  "url": "https://example.com/feed",
  "enabled": true,
  "source_pack": "custom"
}
```

`POST /api/sources/{id}` 支持更新来源；只传 `{ "enabled": false }` 时会切换启用状态。

## 测试

```powershell
py -3 server\test_pipeline.py
py -3 -m py_compile server\demand_pipeline.py server\app.py server\storage.py server\ai_reports.py
```
