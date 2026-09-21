# 03｜证据、口径、置信度与台账

## 1. 最小证据链

```text
S：来源 → C：原子判断 → D：维度结论 → A/B/C：板块判断 → 最终投入决策
```

原始事实必须能回到来源，推断必须能回到前提，估算必须能回到公式和输入。一个句子里含多个可分离断言时，拆成多个判断。

证据不是链接收藏夹。一个链接可能支持多个判断，也可能完全不能支持报告里引用它的那句话。

## 2. 六类判断，必须分开

| `kind` | 中文 | 例子与写法 |
|---|---|---|
| `observed_fact` | 已观察事实 | “在指定地区商店页，观察到某 SKU 标价为 X，周期为一年。”限定时间和观察范围 |
| `attributed_fact` | 来源方自述 | “公司在某日披露其 ARR 为 X；本轮未获得独立审计证据。” |
| `estimate` | 估算 | “根据 C01、C02，在 A01 假设下，按公式推得区间 X—Y。” |
| `assumption` | 待验证假设 | “为测试经营敏感性，暂设付费转化为 3%。”不称为行业均值 |
| `inference` | 分析推断 | “结合价格、免费替代和访谈线索，基础功能的额外付费理由可能偏弱。” |
| `unknown` | 未知 | “未找到该地区、该品类的可核验 MAU。”不写成零，也不推定市场小 |

这六类标签是写作纪律，不是绝对真实性分级。来源方自述可以真实地记录“他说了什么”，仍然不足以证明其声称的商业表现。

假设不能因为被多个模型使用而升级成事实。多个 Agent 重复同一推断也不会产生新证据。

## 3. 数据的九项口径检查

对会参与比较、加总或计算的每个数字，至少核对：

| 字段 | 要问的问题 |
|---|---|
| 时间 | 统计期、截止日、事件日期和发布日期是否不同？ |
| 地域 | 全球、国家、城市或某语言市场？ |
| 人群 | 全部人口、成年人、智能手机用户、注册用户还是付费用户？ |
| 平台 | iOS、Android、Web，还是跨平台去重？ |
| 指标定义 | 下载、活跃、支付人数、收入等的定义是什么？ |
| 期间与存量 | 累计值、单月流量、某日存量还是年度化运行值？ |
| 分母 | 下载、注册、试用、付费或满足条件的客户？ |
| 单位 | 币种、含税/不含税、总额/净额、每月/每年？ |
| 方法与范围 | 抽样、面板估计、全量记录、预测、公司自述？有什么排除项？ |

指标存在并不说明适合问题。用全国调查推断某付费渠道用户时，必须说明两个人群不一致。

### 不允许的替换

- 累计下载 ≠ 当前活跃用户；多个 APP 下载之和 ≠ 不重复用户总数。
- 评分人数 ≠ 下载人数；评论主题频次 ≠ 总体问题发生率。
- 使用过 ≠ 仍在使用；付费意愿 ≠ 实际付款；实际付款 ≠ 续费。
- 目标人群 ≠ 可服务人群 ≠ 可触达人群 ≠ 可盈利用户。
- ARR ≠ 当年确认营收 ≠ 净利润；融资 ≠ 收入。
- 行业基准 ≠ 本品类基准；本品类基准 ≠ 我们的产品实测。
- 当前价 ≠ 平均成交价；广告素材存在 ≠ 投放盈利。
- 访问日期是今天 ≠ 数据是今天产生的。

## 4. 来源质量不是“官方优先”四个字

分别评估：**直接性、方法透明度、适用性、时效、独立性、利益关系和可核验性。**

某来源可对一个问题质量高，对另一个问题质量低。例如官方定价页适合核验公开标价，不适合证明所有客户支付相同价格；公司博客适合证明公司发布了某功能，不足以证明用户使用效果。

免费与付费是访问属性。付费估算也需要核验抽样、覆盖范围和模型；免费原始统计可能更适合某个问题。

涉及专业效果时，区分产品营销、观察性资料、对照研究和证据综合；检查研究对象、干预、结局、样本与局限。不能把某种方法的平均效果当成一个特定 APP 的效果。

## 5. 置信度标准

这里的置信度是**对具体判断的证据质量评价**，不是“该产品成功的概率”，也不是统计学置信区间。

| 等级 | 操作标准 | 常见限制 |
|---|---|---|
| 高 | 证据直接匹配问题，方法与口径清楚、时间适用、无关键未解决冲突；不一定需要多个来源 | 只在该证据实际覆盖的范围内高 |
| 中 | 有直接支持，但存在单一利益相关来源、代理指标、较旧数据、样本或覆盖限制 | 保留限定，不扩大外推 |
| 低 | 高度依赖外推、片面样本、缺失方法、范围错配或重大未解决冲突 | 不能独立承担强决策结论 |
| 未评估 | 尚未阅读/核验，或对象本身仍未知 | 不填一个中间分伪装完成 |

`confidence_reason` 必填。不要只写“来源权威”，应写“原始调查覆盖目标年龄及地区，但不是持续使用率，因此只支持采用行为”。

### 从证据到结论如何传递

一个关键前提很弱时，综合结论应受其限制，不能把大量高质量背景资料平均进去提升把握。对“市场存在”高置信，不意味着对“我们获客能盈利”高置信。

机会吸引力与证据置信度分别呈现。高吸引力、低把握可能值得小额验证，也可能因验证风险或成本过高而不值得；不能用“吸引力分数 × 置信度系数”替代判断。

## 6. 冲突与负面证据

每条冲突记录：争议判断、两个来源 ID、各自口径、冲突类型、处理结果、决策影响。

处理顺序：先核对定义 → 再核对地区与期间 → 再核对源头与方法 → 最后判断是否仍真正冲突。

无法解决时保留冲突，不取算术平均，也不只挑符合初始观点的一边。高风险或决定性冲突要么补查，要么限制最终结论。

没有检索到某功能，只能写“在本次所查页面未确认”；不能直接写“竞品都没有”。没有找到商业数据，也不能推断没有商业需求。

## 7. 来源去重与工作量统计

至少区分以下计数：

| 指标 | 定义 |
|---|---|
| `logged_tool_calls` | 动作日志中实际执行的工具调用条数；不是宿主全量遥测 |
| `search_hits` | 检索命中数量；工具未完整返回时为 `null`，不是 0 |
| `registered_source_records` | 来源台账登记条数，包括尚未阅读或失败记录 |
| `reviewed_source_records` | 标记为已读文本/图像的来源记录条数 |
| `unique_reviewed_locators` | 按已审阅原始定位字符串精确去重的数量 |
| `reviewed_origin_groups` | 归并到共同原始发布/数据来源后的组数 |
| `cited_source_records` | 报告实际采用的来源记录数，包括支持/反证/背景 |
| `failed_source_records` | 未成功阅读的来源数 |

`reviewed_origin_groups` 不是自动证明的“独立权威来源数”。两个不同原始调查也可能使用同一个样本；同一机构的不同报告既可能独立，也可能复用数据，需要人工判断。

同源组示例：公司新闻稿、转载新闻稿、媒体引用同一新闻稿应归为同一原始披露组；媒体若另有独立核验，独立证据部分应单独记录并解释。

对 URL 只做保守规范化。可去除明确跟踪参数，但不得删除地区、语言、平台、页码或 SKU 参数。镜像和转载需要人工建立同源组，不能只靠域名去重。

**绝不能把“界面显示 200 个相关页面”改写成“深入阅读了 200 个独立来源”。**历史日志缺失时，说清无法核验；不得补造过去的动作记录。

## 8. 台账文件与数据约定

所有 `.jsonl` 文件一行一个 JSON 对象。时间使用 ISO 日期/日期时间。未知值用 `null` 或明确枚举，不用空白数字、`NaN`、`Infinity`。记录 ID 在一次研究内唯一。

### `sources.jsonl`

必填字段：

```json
{
  "source_id": "S001",
  "title": "来源标题",
  "locator": "真实 URL 或已授权内部文件标识",
  "accessed_at": "YYYY-MM-DD",
  "origin_group": "O001",
  "source_kind": "official_record",
  "review_status": "reviewed_text",
  "access_status": "full",
  "quality_note": "适合回答什么；利益关系和方法限制是什么"
}
```

`source_kind` 可用：`official_record`、`company_statement`、`original_research`、`third_party_estimate`、`firsthand_review`、`internal_data`、`secondary_report`、`other`。

`review_status`：`lead_only`、`metadata_only`、`reviewed_text`、`reviewed_visual`、`failed`。

`access_status`：`full`、`partial`、`paywalled`、`blocked`、`missing`、`error`。

建议补充：`publisher`、`published_at`、`data_period`、`geography`、`platform`、`access_basis`、`retrieval_ref`、`limitations`、`independence_note`。部分正文可用时可以 `partial + reviewed_text`，但判断只能使用实际可见部分。

### `claims.jsonl`

必填字段及条件字段：

```json
{
  "claim_id": "C001",
  "dimension": "D1",
  "statement": "一条完整、范围明确的判断",
  "kind": "observed_fact",
  "confidence": "medium",
  "confidence_reason": "为何有该把握，以及限制",
  "decision_role": "decisive",
  "included_in_report": true,
  "evidence": [
    {"source_id": "S001", "role": "supports", "precise_locator": "第 X 页/表 Y/段落首句"}
  ],
  "depends_on": [],
  "formula": null,
  "metric": null
}
```

`dimension` 可为 D1—D6 或 `CROSS`。`decision_role` 为 `decisive`、`supporting`、`background`。证据角色为 `supports`、`contradicts`、`context`。

事实和来源方自述必须有实际阅读的支持来源。估算必须有 `depends_on` 与 `formula`；推断必须有前提判断 ID。假设和未知可以没有外部证据，但必须被明确标识。

若 `metric` 非空，记录：`name`、`value`、`unit`、`geography`、`population`、`period`、`platform`、`definition`。字段未知可为 `null` 并解释，不能因为数字看起来精确而略去口径。

### `dimension_assessments.json`

JSON 数组，恰好覆盖 D1—D6。每项：

```json
{
  "dimension": "D1",
  "status": "provisional",
  "conclusion": "一句话结论",
  "claim_ids": ["C001"],
  "confidence": "medium",
  "confidence_reason": "限制在哪里",
  "decision_impact": "对最终投入建议的影响",
  "limitation": "仍未知的问题"
}
```

`status` 为 `complete`、`provisional`、`unknown`、`not_applicable`。非适用必须说明原因；不得为节省研究直接跳过某个维度。

### `actions.jsonl`

仅记录实际发生的动作，不写预想动作。必填：`action_id`、`timestamp`、`phase`、`tool`、`operation`、`target`、`result_status`、`executed`。建议补充 `question_id`、`source_ids`、`notes`。

日志记录可观察动作和结果，不要求暴露私有逐字思维过程。计划写入研究计划，不能伪装成执行日志。

### `competitors.jsonl`

建议字段：`competitor_id`、`name`、`stable_id`、`market`、`platform`、`positioning`、`selection_reason`、`observed_at`、`source_ids`、`limitations`。未知留空并标记，不捏造商店 ID。

## 9. 引用输出

在报告的关键事实或数字旁引用，包含地域和时间限定；不要在段末附一个只能支持半句话的链接。

聊天里使用宿主的原生引用。导出文件保留来源 ID 和 URL/文件标识以及页码/段落，不能只保存离开会话就无法使用的引用 token。

对推断写“据此推断”，对计算写“按以下假设推算”，对公司披露写“公司自述”。引用表示证据关系，不等于替来源背书。
