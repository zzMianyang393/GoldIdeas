# GoldIdeas 前端基座需求说明

> 目标读者：Antigravity / 前端实现代理  
> 范围：只描述产品结构、模块化基座、页面能力与数据对接  
> 不包含：视觉风格、配色、品牌语言、具体 UI 美术方向

---

## 1. 产品定位

GoldIdeas 是一个用于发现、分析、验证 SaaS / Micro SaaS 创意的工作台。

当前后端已经实现 V4.1 规则引擎，可以完成：

- 多来源信号采集
- 机会分类
- 5 条红线判断
- 五维评分
- GREEN / YELLOW / RED 评级
- Markdown 报告与 JSON 数据落盘

前端不应该只是一个 MVP 数据展示页，而应该作为长期可扩展的 Web 工作台基座。

更准确的产品形态是：

**IDE-like Web Workspace**

这里的 IDE-like 不是指桌面端应用，也不是必须做成 VS Code，而是指一种工作台式信息架构：

- 固定模块导航
- 中央工作区
- 右侧 Inspector / Detail 面板
- 顶部任务、搜索、状态、命令区域
- 支持后续持续增加、删除、替换模块

第一版仍然是 Web 应用，不需要 Electron / Tauri。

---

## 2. 核心设计目标

### 2.1 作为长期基座

前端需要支持未来扩展，不要写成单一页面 demo。

后续可能新增：

- AI 可行性报告生成
- 竞品调研
- 信息源管理
- 扫描历史
- 评分规则编辑
- 验证任务管理
- 手动录入 idea
- 多报告对比

因此需要从一开始建立清晰的模块边界。

### 2.2 支持模块增删

推荐把页面抽象为：

- `Module`
- `Workspace`
- `Inspector`
- `Run`
- `Source`
- `Opportunity`
- `Report`
- `Artifact`

每个模块可以有自己的主视图，但共享同一个应用外壳。

### 2.3 支持 AI 能力接入

系统允许使用 AI 完成部分功能。

建议边界：

规则引擎负责：

- 抓取
- 去重
- 红线初筛
- 基础评分
- 结构化输出
- 可解释的规则证据

AI 负责：

- 多来源摘要
- 痛点归纳
- ICP 推断
- 竞品假设
- 可行性报告草稿
- 下一步验证计划
- 把零散信号整理成人能决策的分析材料

前端需要为 AI 任务预留入口与状态展示，但第一版可以先用占位或静态状态。

---

## 3. 推荐应用结构

### 3.1 顶部区域

顶部区域用于全局任务和状态。

建议包含：

- Run Scan
- Generate Report
- Search
- 当前扫描状态
- 最近一次运行时间
- 报告入口
- 全局设置入口

顶部区域不负责展示大量业务内容，只作为全局操作区。

### 3.2 左侧模块导航

左侧是固定模块入口。

第一版建议保留这些模块：

- `Signals`
- `Opportunities`
- `Reports`
- `Sources`
- `Runs`
- `Settings`

可以暂时不实现所有模块的完整功能，但导航结构应该保留，方便后续扩展。

### 3.3 中央工作区

中央区域根据当前模块切换。

例如：

- Opportunities：机会列表、过滤、排序
- Reports：报告列表、报告查看
- Sources：信息源列表、启用状态、异常状态
- Runs：扫描历史、参数、耗时、产出数量
- Settings：规则、AI 配置、导出路径等

### 3.4 右侧 Inspector

右侧 Inspector 展示当前选中对象的上下文。

选中 Opportunity 时显示：

- 标题
- 来源
- 原文链接
- 评分
- 红线结果
- 五维评分
- 内容摘要
- 关键证据
- 操作按钮

选中 Report 时显示：

- 报告状态
- 关联 opportunity
- 生成时间
- 使用的数据源
- 导出操作

选中 Source 时显示：

- 来源类型
- URL / 查询参数
- 最近状态
- 最近错误
- 最近产出数量

---

## 4. 第一版模块说明

### 4.1 Signals

用于展示原始采集信号。

第一版可展示：

- 标题
- 来源
- 发布时间
- 链接
- 摘要
- 是否已转为 opportunity

后续可扩展：

- 手动标记
- 忽略
- 合并重复信号
- AI 摘要

### 4.2 Opportunities

核心模块。

第一版需要支持：

- 机会列表
- 按评级过滤：GREEN / YELLOW / RED
- 按来源过滤
- 按总分排序
- 选中后在 Inspector 查看详情
- 打开原始链接
- 打开或生成可行性报告

主要字段：

- title
- source
- source_group
- url
- content_summary
- category
- rating
- total_score
- scores
- score_reasons
- redlines
- redline_checks
- key_insight
- action_items

### 4.3 Reports

用于管理可行性报告。

第一版可先展示 Markdown 报告。

后续需要支持：

- 单个 opportunity 的深度报告
- 多 opportunity 对比报告
- AI 生成草稿
- 人工编辑
- 导出 Markdown / JSON

### 4.4 Sources

用于管理信息源。

当前后端默认来源包括：

- Reddit RSS
- Hacker News RSS
- Hacker News Algolia Search
- Product Hunt RSS
- Indie Hackers RSS

第一版可展示只读状态：

- 来源名称
- 来源类型
- 最近是否成功
- 最近错误
- 最近产出数量

后续可扩展：

- 新增来源
- 禁用来源
- 修改抓取参数
- 测试连接

### 4.5 Runs

用于查看每次扫描运行。

第一版可展示：

- generated_at
- limit
- source_count
- raw_count
- green / yellow / red 数量
- errors
- report_path

后续可扩展：

- 运行耗时
- 任务状态
- AI 子任务状态
- 重跑
- 对比两次运行差异

### 4.6 Settings

用于保留配置入口。

第一版可以只做基础占位：

- 默认 limit
- 是否 quick scan
- 默认 rating filter
- AI provider 配置占位
- 数据路径说明

---

## 5. 可行性报告结构

每个 opportunity 后续应该能生成一份独立的可行性报告。

报告建议包含以下部分。

### 5.1 Executive Summary

用于快速决策。

包含：

- 一句话结论
- 当前评级
- 总分
- 推荐动作
- 是否值得进入验证

### 5.2 Problem Evidence

用户痛点证据。

包含：

- 原始信号摘要
- 痛点关键词
- 痛点强度评分
- 多来源证据
- 是否出现重复需求

### 5.3 Audience & ICP

目标用户画像。

包含：

- 可能用户群体
- 使用场景
- 预算能力
- 触发购买的事件
- 早期用户在哪里出现

### 5.4 Market Signal

市场信号。

包含：

- 讨论热度
- 来源分布
- 是否跨社区出现
- 是否是短期热点
- 是否有长期稳定需求

### 5.5 Competition

竞争与替代方案。

包含：

- 直接竞品
- 间接替代
- 巨头风险
- 开源 / 免费替代
- 用户对现有方案的不满

### 5.6 Build Feasibility

开发可行性。

包含：

- MVP 范围
- 技术复杂度
- 是否适合个人开发者
- 依赖哪些平台 / API
- 预计开发阶段

### 5.7 Distribution

获客路径。

包含：

- 可用渠道
- 冷启动方式
- SEO 可能性
- 社区传播可能性
- 是否需要销售团队

### 5.8 Monetization

变现路径。

包含：

- 订阅
- 一次性付费
- usage-based
- 模板 / 插件 / 服务化
- 价格测试建议

### 5.9 Risk Assessment

风险评估。

包含：

- 平台风险
- 合规风险
- 技术风险
- 获客风险
- 护城河风险
- 需求伪信号风险

### 5.10 Validation Plan

下一步验证计划。

包含：

- 需要验证的核心假设
- 用户访谈问题
- 落地页测试
- 价格测试
- MVP 最小功能
- 停止条件

### 5.11 AI Notes

AI 辅助分析内容。

包含：

- AI 摘要
- AI 归纳的用户痛点
- AI 推断的 ICP
- AI 给出的竞品方向
- AI 生成的验证建议

需要明确标记 AI 生成内容，避免与规则引擎结果混淆。

---

## 6. 当前后端 API

当前本地服务默认运行在：

```text
http://127.0.0.1:8765
```

### 6.1 获取当前状态

```http
GET /api/status
```

返回：

- ready
- metadata
- counts
- opportunities

### 6.2 触发扫描

```http
POST /api/scan
Content-Type: application/json
```

请求体示例：

```json
{
  "limit": 10,
  "rating": "",
  "quick": true
}
```

返回：

- metadata
- counts
- redline_stats
- opportunities
- report_path

### 6.3 获取 Markdown 报告

```http
GET /api/report
```

返回最新 Markdown 报告。

---

## 7. 当前数据结构参考

### 7.1 Opportunity

```json
{
  "title": "Example title",
  "content": "Raw content",
  "url": "https://example.com",
  "comments_url": "https://example.com/comments",
  "comments": 12,
  "source": "r/indiehackers",
  "source_group": "reddit",
  "published": "2026-04-30T00:00:00+00:00",
  "category": {
    "name": "pain_point",
    "description": "用户明确表达痛点",
    "hits": 2
  },
  "redlines": [],
  "redline_checks": {
    "1": "pass",
    "2": "pass",
    "3": "pass",
    "4": "pass",
    "5": "pass"
  },
  "scores": {
    "痛点强度": 6.2,
    "开发性价比": 7.0,
    "生存稳定性": 7.0,
    "获客阻力": 5.8,
    "变现确定性": 6.0
  },
  "score_reasons": {
    "痛点强度": "弱痛点: need",
    "开发性价比": "个人可做: saas",
    "生存稳定性": "无明显政策或平台风险",
    "获客阻力": "低成本获客: reddit",
    "变现确定性": "明确变现: pricing"
  },
  "total_score": 6.4,
  "rating": "🟢 GREEN",
  "content_summary": "Short summary",
  "key_insight": "用户明确表达痛点；当前最强维度是开发性价比。",
  "action_items": "整理 5 个同类讨论，做一个落地页验证。"
}
```

### 7.2 Metadata

```json
{
  "generated_at": "2026-04-30T00:00:00+00:00",
  "limit": 10,
  "source_count": 16,
  "subreddits": ["indiehackers", "microsaas"],
  "raw_count": 53,
  "errors": [
    {
      "source": "r/SaaS",
      "error": "RSS Timeout"
    }
  ],
  "quick": true,
  "rating_filter": null
}
```

---

## 8. 第一版交付建议

第一版前端建议完成：

- IDE-like Web Workspace 外壳
- 左侧模块导航
- 顶部全局操作栏
- Opportunities 主工作区
- Opportunity Inspector
- Reports 查看入口
- Sources / Runs / Settings 占位模块
- 接入 `/api/status`
- 接入 `/api/scan`
- 接入 `/api/report`

暂不要求：

- 完整 AI 生成流程
- 完整信息源编辑
- 完整报告编辑器
- 用户系统
- 权限系统
- 桌面端打包

---

## 9. 给实现代理的关键要求

- 不要做成单页 demo。
- 不要把所有业务逻辑塞在一个页面里。
- 不要把 Opportunities、Reports、Sources、Runs 混成一张大表。
- 要保留模块边界。
- 要让后续新增模块时成本很低。
- 要让 Inspector 成为统一详情展示区域。
- 要为 AI 分析任务预留状态位和入口。
- 视觉风格由另行指定，不在本文档中定义。

