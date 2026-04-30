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
GET  /api/runs/{id}
GET  /api/signals
GET  /api/signals/{id}
GET  /api/opportunities
GET  /api/opportunities/{id}
GET  /api/opportunities/{id}/signals
GET  /api/sources
GET  /api/sources/{id}
GET  /api/search-jobs
GET  /api/search-jobs/{id}
GET  /api/ai/report?opportunity_id=opp_xxx
GET  /api/ai/reports
GET  /api/ai/reports/{id}
GET  /api/ai/jobs
GET  /api/ai/jobs/{id}
POST /api/scan
POST /api/search-jobs
POST /api/sources
POST /api/sources/{id}
POST /api/ai/report
POST /api/ai/jobs
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

`GET /api/opportunities` 支持列表查询：

```text
GET /api/opportunities?limit=50&offset=0&rating=green&q=dashboard&source_group=reddit
```

`GET /api/signals` 支持原始信号查询：

```text
GET /api/signals?limit=50&offset=0&q=invoice&source=sample&source_group=sample
```

`GET /api/opportunities/{id}/signals` 可用于回溯一个机会关联的原始信号。

`GET /api/ai/reports` 支持按 opportunity 和 report type 过滤：

```text
GET /api/ai/reports?opportunity_id=opp_xxx&report_type=feasibility
```

`POST /api/ai/report` 会根据 `opportunity_id` 获取或生成可行性报告。当前实现是零 token 的本地占位报告，用于验证缓存、数据库和 API 流程；后续可以替换为真实 AI provider。

```json
{
  "opportunity_id": "opp_xxx",
  "report_type": "feasibility",
  "force": false
}
```

`POST /api/ai/jobs` 会创建异步 AI 报告任务，返回 `pending` 状态的 job；服务会在后台线程中生成或复用缓存报告。前端可轮询 `GET /api/ai/jobs/{id}` 查看状态。

```json
{
  "opportunity_id": "opp_xxx",
  "report_type": "feasibility",
  "force": false
}
```

AI provider 默认是零成本本地占位：

```powershell
$env:GOLDIDEAS_AI_PROVIDER='local'
```

如需接入 OpenAI-compatible Chat Completions 接口：

```powershell
$env:GOLDIDEAS_AI_PROVIDER='openai'
$env:OPENAI_API_KEY='...'
$env:OPENAI_MODEL='gpt-4o-mini'
# 可选：兼容服务地址
$env:OPENAI_BASE_URL='https://api.openai.com/v1'
```

真实 provider 会写入 `provider`、`model`、`token_usage` 字段；当前没有内置价格表，`cost_estimate` 暂为 0。

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
py -3 -m py_compile server\demand_pipeline.py server\app.py server\storage.py server\ai_reports.py server\ai_jobs.py server\ai_providers.py
```
