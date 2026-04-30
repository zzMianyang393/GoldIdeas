# GoldIdeas AI 接入与商业模式设计说明

> 目标读者：产品设计 / 后端实现 / AI 功能实现代理  
> 范围：AI 接入策略、缓存策略、数据库设计方向、自定义搜索、多内容方向、收费模型  
> 不包含：前端视觉风格

---

## 1. 核心判断

GoldIdeas 后续可以使用 AI，但 AI 不应该替代整个系统。

推荐定位：

**规则引擎负责发现与初筛，AI 负责解释、归纳与报告增强。**

这样可以同时获得：

- 可控成本
- 可解释评分
- 自动化效率
- 更高质量的决策报告

---

## 2. AI 在系统中的角色

### 2.1 规则引擎负责

规则引擎适合处理稳定、可重复、低成本的任务：

- 信息源采集
- 去重
- 初步分类
- 红线判断
- 五维评分
- GREEN / YELLOW / RED 评级
- 结构化 JSON 输出
- 扫描历史记录

### 2.2 AI 负责

AI 适合处理需要理解、归纳和表达的任务：

- 多来源摘要
- 痛点归纳
- ICP 推断
- 竞品假设
- 市场信号总结
- 风险解释
- 可行性报告草稿
- 下一步验证计划
- 用户访谈问题
- 落地页文案草稿

### 2.3 不建议让 AI 负责

不建议第一版让 AI 直接负责：

- 最终评分
- 是否一票否决
- 数据去重唯一判断
- 计费额度判断
- 用户权限判断

AI 可以给建议，但最终结构化评分应由规则引擎或明确版本化的 scoring profile 决定。

---

## 3. AI 调用原则

AI 调用必须遵循：

**同一个 opportunity 的同一类 AI 分析，不重复调用。**

原因：

- 避免浪费 token
- 降低成本
- 保持结果稳定
- 支持报告复用
- 支持未来收费

推荐流程：

1. 规则引擎完成扫描。
2. 系统生成或匹配 `opportunity_id`。
3. 查询数据库是否已有 AI 报告。
4. 如果已有并且未过期，直接复用。
5. 如果没有，则创建 AI 分析任务。
6. AI 任务异步执行。
7. 结果写入数据库。
8. 前端显示 AI 报告状态与结果。

---

## 4. Opportunity 去重与缓存

### 4.1 不要只用标题作为唯一标识

标题容易变化，也容易重复。

推荐组合：

- source
- source_group
- canonical_url
- normalized_title
- content_hash

### 4.2 推荐 ID 生成逻辑

可以生成：

```text
opportunity_fingerprint = hash(
  source_group + canonical_url
)
```

如果没有稳定 URL：

```text
opportunity_fingerprint = hash(
  normalized_title + source_group + content_hash_prefix
)
```

### 4.3 后续更高级的合并

未来可以把多个 signal 合并为同一个 opportunity。

例如：

- Reddit 上有人抱怨 Shopify return 工具
- HN 上有人讨论电商退货自动化
- Product Hunt 出现相关新产品

这些可能属于同一个 opportunity cluster。

第一版可以先基于 URL / 标题 hash 去重。

---

## 5. AI 报告缓存策略

### 5.1 默认复用

同一个 opportunity 如果已经有 AI 报告，默认不重新生成。

### 5.2 允许重新生成的条件

建议满足以下条件之一才重新调用 AI：

- 用户手动点击 Regenerate
- 新增多个高质量来源证据
- opportunity 内容 hash 明显变化
- AI 报告超过一定时间，例如 30 天
- prompt version 升级
- report template version 升级
- scoring profile version 升级
- 用户选择更高分析深度

### 5.3 需要记录版本

每份 AI 报告建议记录：

- model
- provider
- prompt_version
- report_template_version
- scoring_profile_version
- generated_at
- input_hash
- token_usage
- cost_estimate
- status

这样以后可以解释“为什么这份报告是这样生成的”。

---

## 6. 推荐数据库概念模型

第一阶段可以继续用 JSON，但后续建议迁移到 SQLite / Postgres。

推荐核心表 / 集合：

### 6.1 `signals`

原始采集信号。

字段示例：

- id
- source_id
- source_group
- title
- content
- url
- comments_url
- published_at
- fetched_at
- raw_payload
- content_hash

### 6.2 `opportunities`

去重后的机会资产。

字段示例：

- id
- fingerprint
- title
- canonical_summary
- primary_source_id
- rating
- total_score
- category
- first_seen_at
- last_seen_at
- seen_count
- status

### 6.3 `opportunity_signals`

机会与原始信号的关联。

字段示例：

- opportunity_id
- signal_id
- relation_type
- confidence

### 6.4 `scores`

规则评分结果。

字段示例：

- opportunity_id
- scoring_profile
- scores_json
- reasons_json
- redlines_json
- rating
- generated_at

### 6.5 `ai_reports`

AI 生成报告。

字段示例：

- id
- opportunity_id
- report_type
- report_json
- report_markdown
- status
- model
- provider
- prompt_version
- input_hash
- token_usage
- cost_estimate
- generated_at

### 6.6 `runs`

扫描运行记录。

字段示例：

- id
- started_at
- finished_at
- parameters_json
- source_count
- raw_count
- opportunity_count
- green_count
- yellow_count
- red_count
- errors_json

### 6.7 `sources`

信息源配置。

字段示例：

- id
- name
- type
- url
- enabled
- source_pack
- last_status
- last_error
- last_fetched_at

### 6.8 `search_jobs`

用户自定义搜索任务。

字段示例：

- id
- user_id
- query
- mode
- source_pack
- scoring_profile
- ai_depth
- status
- created_at
- completed_at

### 6.9 `users`

用户账户。

字段示例：

- id
- email
- plan
- created_at

### 6.10 `usage_credits`

用量与额度。

字段示例：

- user_id
- period
- scan_count
- ai_report_count
- ai_credit_used
- reset_at

---

## 7. 自定义搜索

如果允许用户自定义搜索，系统必须兼容多个内容方向。

不要把自定义搜索做成简单关键词搜索。

推荐结构：

```text
Custom Search = Query + Opportunity Type + Source Pack + Scoring Profile + AI Depth
```

字段示例：

- query
- opportunity_type
- target_audience
- include_keywords
- exclude_keywords
- source_pack
- scoring_profile
- ai_depth
- date_range

---

## 8. 多内容方向兼容

系统底层应该支持多个 `Opportunity Type`。

每个方向应该拥有自己的：

- 信息源
- 关键词策略
- 红线规则
- 评分维度
- AI 报告模板
- 变现判断逻辑

### 8.1 第一批推荐方向

第一版建议先支持 3 个方向：

1. Micro SaaS
2. Developer Tools
3. E-commerce Tools

这三个方向差异明显，且都有较强付费可能。

### 8.2 后续可扩展方向

后续可以加入：

- Creator Tools
- Local Business Tools
- AI Workflow Tools
- Niche B2B Tools
- Info Product / Newsletter

---

## 9. Opportunity Type 说明

### 9.1 Micro SaaS

重点判断：

- 是否有明确痛点
- 是否适合订阅
- 是否个人可开发
- 是否有长期留存
- 是否有低成本获客渠道

适合来源：

- Reddit indie / SaaS 社区
- Indie Hackers
- Product Hunt
- Hacker News

### 9.2 Developer Tools

重点判断：

- 是否有开发者真实痛点
- 是否有开源替代
- 是否能通过 GitHub / HN 获客
- 是否容易被平台功能吞掉
- 是否存在长期维护压力
- 是否有团队付费可能

适合来源：

- Hacker News
- GitHub Issues
- Reddit webdev / programming
- Stack Overflow / dev forums
- Product Hunt

### 9.3 E-commerce Tools

重点判断：

- 是否直接影响收入
- 是否能证明 ROI
- 是否依赖 Shopify / Amazon / TikTok 等平台
- 是否有支付、合规、物流风险
- 是否适合按订单量 / GMV / 店铺规模收费

适合来源：

- Shopify forums
- Reddit ecommerce / shopify
- Product Hunt
- Amazon seller 社区
- DTC / growth 社区

### 9.4 Creator Tools

重点判断：

- 创作者是否愿意付费
- 是否节省时间或提高收入
- 是否依赖平台政策
- 是否容易被平台内置
- 是否可通过模板、素材、自动化变现

### 9.5 Local Business Tools

重点判断：

- 小商家是否愿意付费
- 是否解决具体运营问题
- 是否需要销售或人工交付
- 是否能标准化
- 是否有低成本获客渠道

### 9.6 AI Workflow Tools

重点判断：

- AI 是否是核心能力还是辅助能力
- 是否存在强自动化价值
- 是否容易被大模型平台原生功能替代
- 是否有企业工作流嵌入价值
- 是否存在数据隐私风险

---

## 10. Scoring Profile

当前 V4.1 的评分适合 Micro SaaS。

后续不同方向应该拥有不同评分 profile。

### 10.1 通用基础维度

可以保留：

- 痛点强度
- 开发性价比
- 生存稳定性
- 获客阻力
- 变现确定性

### 10.2 不同方向的扩展维度

Developer Tools 可增加：

- 开源竞争风险
- 开发者采用阻力
- 维护成本

E-commerce Tools 可增加：

- ROI 可证明性
- 平台依赖风险
- 商家支付能力

Creator Tools 可增加：

- 平台内置风险
- 内容生产频率
- 创作者付费能力

AI Workflow Tools 可增加：

- AI 替代风险
- 数据隐私风险
- 自动化深度

---

## 11. 商业模式选择

### 11.1 路线 A：用户自定义搜索

用户输入需求，系统帮他搜索、评分、生成报告。

优点：

- 更像 SaaS 工具
- 个性化强
- 适合订阅
- 可绑定 AI credit

缺点：

- 成本更高
- 用户可能不知道搜什么
- 搜索质量参差不齐

适合收费：

- 免费额度
- 月订阅
- AI report credit
- 超额付费

### 11.2 路线 B：固定提供创意库

平台定期提供精选机会，用户付费查看。

优点：

- 产品简单
- 成本可控
- 内容资产可沉淀
- 适合 newsletter / research database

缺点：

- 容易被认为只是 idea list
- 创意容易被复制
- 长期 SaaS 价值较弱

适合收费：

- 会员订阅
- 单份报告解锁
- 每周精选报告

### 11.3 路线 C：混合模式

推荐选择。

模式：

- 平台提供公开精选机会库
- 用户可以自定义搜索
- 用户可以生成私有 AI 深度报告
- 用户可以收藏、跟踪、验证机会

优点：

- 公开机会库负责获客
- 私有搜索和 AI 报告负责收费
- 同时具备内容资产与 SaaS 工具属性
- 更容易扩展到团队和专业用户

---

## 12. 推荐收费结构

### 12.1 Free

适合获客。

可包含：

- 查看部分公开机会
- 每日 / 每月有限扫描
- 少量 AI report credit
- 基础报告查看

### 12.2 Pro

核心付费层。

可包含：

- 查看完整机会库
- 自定义搜索
- AI 可行性报告额度
- 收藏机会
- 跟踪机会
- 导出报告

### 12.3 Studio / Advanced

高级层。

可包含：

- 更高 AI credit
- 竞品调研
- 趋势监控
- 多来源深度搜索
- 自定义信息源
- 团队协作
- API / webhook

---

## 13. Credit 设计

建议把 AI 成本绑定到 credit。

低成本功能：

- 扫描
- 规则评分
- 基础过滤
- 查看公开机会摘要

消耗 credit 的功能：

- AI 可行性报告
- AI 竞品分析
- AI ICP 分析
- AI 验证计划
- AI 多来源总结
- 重新生成报告

示例：

- Standard AI Report: 1 credit
- Deep AI Report: 3 credits
- Competitor Research: 5 credits
- Regenerate Report: 1 credit

---

## 14. 推荐产品定位

不要把 GoldIdeas 定位成单纯“卖创意”。

创意本身不是最终价值。

真正价值是：

- 帮用户发现机会
- 帮用户判断值不值得做
- 帮用户快速验证
- 帮用户持续跟踪市场信号
- 帮用户把零散讨论转成可执行项目判断

推荐定位：

**SaaS Opportunity Research & Validation Workspace**

一句话商业逻辑：

**公开机会库负责获客，私有搜索和 AI 深度报告负责收费。**

---

## 15. 第一阶段落地建议

第一阶段不需要一次性实现全部内容。

建议顺序：

1. 保留现有规则引擎。
2. 增加 opportunity fingerprint。
3. 增加持久化数据库。
4. 增加 AI report 状态字段。
5. 增加 AI 报告生成任务。
6. 实现 AI 报告缓存。
7. 前端展示 AI report 状态。
8. 增加自定义搜索参数。
9. 增加 Opportunity Type。
10. 最后再做计费和 credit。

这样可以避免一开始系统复杂度过高。

