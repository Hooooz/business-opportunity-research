# 商业机会调研 Skill · v1.0.0

## 这份包解决什么问题

让其他 Agent 不依赖本次聊天，也能研究新的 APP 或经营品类，并回答：

> **这个经营机会值不值得出最小验证包？**

人读主干保持简单：一个决策、三个判断板块、六个维度。Agent 的复杂执行过程下沉到操作附录、证据台账和脚本。

本包是从已有轻断食 APP 报告及用户确认的分析框架整理出的**通用执行规范**，不是上次研究逐次工具调用的回放。当前记录不能核验“200 多个来源”的具体阅读数量，也不声称上一轮已使用本包所有脚本、台账和质量控制。

## 文件导航

- `SKILL.md`：Agent 的执行入口，含触发条件、固定框架、十步流程与禁止事项。
- `references/01-workflow.md`：每一步怎么做、做到什么程度、产出什么。
- `references/02-tools-and-search.md`：能力映射、查询配方、原文与 PDF 核验、访问失败处理。
- `references/03-evidence-and-confidence.md`：事实/假设/推断区分、数据口径、来源去重、置信度和 JSON 字段。
- `references/04-economics-and-validation.md`：单位经济、反算门槛、样本解释、最小验证包、非 APP 适配。
- `references/05-quality-and-handoff.md`：审计、红队检查、多 Agent 分工、断点续接与版本更新。
- `references/06-case-retrospective.md`：上次报告可确认的工作模块、不能确认的事项，以及本次新增控制。
- `assets/`：启动输入、研究计划、报告、验证包、交接、经营模型等模板。
- `scripts/`：初始化项目、计算经营账与比例区间、检查证据台账。
- `tests/`：本地脚本测试与供 Agent 试跑的验收场景。

## 如何交给其他 Agent

### 支持文件夹式 Skill 的环境

将整个 `business-opportunity-research/` 文件夹放入该宿主文档规定的技能目录，再让 Agent 使用 `business-opportunity-research`。具体安装目录、自动发现和工具授权由宿主决定，本包不假定所有宿主相同。

### 只支持对话和文件的环境

上传并解压整包，明确要求先读取 `SKILL.md`，随后按触发条件读取附录。若不能解压，可使用随包交付的完整说明 Markdown，或提供主文件与所需附录。只发送主文件会失去详细规则与脚本。

### 推荐调用提示词

```text
请使用 business-opportunity-research Skill，研究【品类】的经营机会。

研究范围：【地区/语言/平台；未知请明确标注】
研究截至：【本次运行日期】
公司情况：【人员、能力、资产、渠道、预算；未知不可猜测】
特别约束：【例如不做医疗建议、不采购付费数据、只研究订阅】

唯一决策：这个经营机会值不值得出最小验证包？
请先按三个判断板块、六个维度建立问题树，再获取证据、核验口径、
形成经营模型、寻找反证并设计最小验证包。

事实、来源方自述、估算、假设、推断和未知分开记录。
正文按金字塔结构呈现；附上证据台账、未解决问题和可继续执行的交接文件。
不以来源数量或报告长度作为完成标准；不要沿用其他品类的价格、阈值或结论。
未经授权不要采购、投放、联系访谈对象或执行实验。
```

## 本地脚本

Python 3.10+，仅标准库；不联网、不购买、不调用外部 API。

```bash
# 以下命令从技能文件夹根目录运行；将日期替换为实际研究日期。
python3 scripts/init_research.py --category "记账 APP" --markets "待确认" --as-of YYYY-MM-DD --out ./research-run

# 示例仅用于演示计算，不能当作任何品类的市场数据。
python3 scripts/calculate_economics.py model assets/unit_economics.example.json --output ./economics-example-result.json

# 比例区间示例：100 人里 3 人转化，不等于真实转化率精确为 3%。
python3 scripts/calculate_economics.py wilson --successes 3 --total 100

# 填完工作目录后运行；不会验证网页真实性，只检查结构与追溯。
python3 scripts/audit_research.py ./research-run --output ./research-run/audit.json

# 脚本测试。
python3 -m unittest discover -s tests -v
```

模板中的空值代表待补充，不能被 Agent 当成已经完成的研究。初始化目录立即审计出现缺项是预期行为。

## 使用边界

本包提供研究流程，不保证发现可盈利机会，不替代真实交易、留存试验、专业审核或法律意见。脚本只验证可机械验证的关系；不自动判断引用是否准确、评论是否代表总体、商业结论是否正确。

公开资料无法解决的缺口应保留。一个诚实的“现阶段不值得投入”或“只值得先补查特定问题”，比材料很多但逻辑不成立的正面结论更有用。

本次已做本地结构与脚本测试；没有在多个真实品类上完成端到端 Agent 回归测试，后续应使用 `tests/agent_eval_cases.md` 实跑并修订。

## 格式参考与来源

本包的文件夹、YAML 元信息及按需读取附录结构参考以下官方说明；商业研究方法是依据本次需求整理的工作规范，不将其称为上述标准的规定。

- [Agent Skills 规范](https://agentskills.io/specification)，访问日期：2026-09-21。
- [Agent Skills 编写实践](https://agentskills.io/skill-creation/best-practices)，访问日期：2026-09-21。

二者建议以 `SKILL.md` 为入口，将较长的参考材料和脚本分开，并通过实际任务和检查迭代。具体宿主是否支持此格式及如何授权工具，需要在部署环境中确认。
