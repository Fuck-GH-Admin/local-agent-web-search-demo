# E00｜基准接入顺序与逐题筛选合同 v1.0

**当前状态：SCREENING_PROTOCOL_READY / QUESTIONS_SELECTED=0 / DATA_IMPORT_NOT_RUN**  
**先决文件：** [可用性审计](./00_BENCHMARK_AVAILABILITY_AUDIT_20261014.md) ｜ [机器可读来源登记](./BENCHMARK_SOURCE_REGISTRY.json)。本文件是下一阶段的**工作合同**，不包含任何已入选测试题目。

## 1. 新阶段必须回答的独立问题

A. **数据可用性**：官方是否公开文件、是否可在 Ubuntu 完整获取、真实格式和字段为何、许可证是否允许此用途？  
B. **项目适配性**：它测搜索召回、网页抽取、回答正确率，还是复杂 Agent？当前 SearXNG/三解析器/Agent 哪层能直接接？  
C. **题目质量**：证据是否仍然有效、答案是否唯一/集合完整、是否适合中文、本地网络是否可达、是否会泄漏 Gold？  
D. **结果可复现性**：同一输入、模型、工具预算、内容快照和评分器能否重算？动态事实是否有时间金标？

**每个问题有独立状态，不得用 A=PASS 推导 B/C/D=PASS。**

## 2. 分批卡（本轮只完成 E00-R：官方来源核验）

| 批次 | 实际任务 | 完成判据 | 当前状态 |
|---|---|---|---|
| **E00-R**：上游基准研究 | 官方仓库/数据卡/许可/格式/费用/限制 + 推荐优先级，资料可追溯 | 本轮文档与 JSON 登记提交 GitHub，不声称已下载 | **RESEARCH_COMPLETE** |
| **E00-A1**：本机来源探测 | 各候选只读 clone/headers/manifest/1 行或样本文件/合法下载，锁 SHA256、split、字段、许可；记录可复现命令、非敏感失败 | 每项 `LOCAL_SMOKE_PASS/BLOCKED/DEFERRED`，有文件哈希与环境信息 | **NOT_RUN** |
| **E00-A2**：适配器与评分器预检 | EXA `Searcher`、Seal/CRAG 题目加载器的离线固定样本 schema；无 Agent/模型 API；静态评分器最小 golden fixture | 不同来源能映射到统一问题类型，失败类型不被吞 | **NOT_RUN** |
| **E00-S**：逐测试筛题（你与我再共同确定） | 每个测试先列候选与排除原因、来源快照；Gold 保密；人工认可最终所选的 question IDs | 筛选台账独立签认；**当前没有题目入选** | **NOT_RUN** |
| **E01**：搜索/解析单独评分 | 固定搜索和正文输入、R@K/证据段落/漏文/噪声与下载成功率 | 可复现的 Search-only、Fetch/Parse-only 结果 | **FUTURE** |
| **E02**：固定模型端到端 | No-search / Search snippets / Search + full read 同题同预算；引用逐断言复核 | 准确率、弃答、引用支持率、时间与费用 | **FUTURE** |
| **E03**：扩大标准集、供应商对照 | 先核对预算/公平性与成本，再接 DeepSearchQA、FRAMES、BrowseComp 等 | 同题不同搜索工具效果与置信区间 | **FUTURE** |

验收和原项目一样保留 `PASS/FAIL/BLOCKED/NOT_RUN`，失败及禁用项不能在跨批次索引中消失。E00-A1 尚未完成时，禁止宣称各基准已在目标主机“可用”。

## 3. 下一批先测哪些官方数据入口（**不选择题目**）

### 路线 A：检索层（先行）

**EXA Publication**：测试是否能读取评测查询/标准论文标识；结构映射 `query → SearXNG.SearchResult.items[]`、`target DOI/title/canonical URL`，不能使用纯字符串 URL 包含关系冒充文献匹配。记录作者/出版时间辅助消歧的规则。

**EXA WebCode Contents**：核查 250 URLs 与 golden markdown 实际文件是否公开、是否需要内容授权、评分器对代码块/表格的输入要求；我们的 `read_webpage` 的三个 parser 使用同一份冻结 HTML 以消除页面时间差。若 golden 内容实际不可复现，只建自有小型手工证据标签，不冒充 WebCode 官方评分。

### 路线 B：回答层（同时做可用性试探）

**SealQA**：只检查 Seal-0 与 Seal-Hard 的 parquet schema、列类型、答案/gold 与题目是否混在同一字段及裁判模板；LongSeal 单列 `DEFERRED_CONTEXT`。必须记录 HF revision。后续选题时先确认“没有证据仍需拒答”的条件适配性。

**CRAG**：只检查 Task1 包与数据 schema，保留 `query_time` / `static_or_dynamic` / `false_premise`；许可 CC BY-NC 4.0，先确保我们研究性非商业用途匹配。Task2/3 另做需求评估。

### 路线 C：时效性（数据需冻结）

**FreshQA**：从带日期的原始 Google Sheet 导出只读 CSV，并留源文档 URL 与 SHA。不能因为页面声称按周更新就将旧题打上“2026 年 10 月最新”标签。

**LiveNewsBench**：逐一确认官方 `human_verified_test.jsonl` 的真实 release、题量、时间、可用字段和许可证；在严格遵循禁源域名与 Archive 过滤时，如现有 SearXNG 不能支持可靠的屏蔽，标 `ADAPTER_BLOCKED`，不能擅自删除反泄漏限制。

### 延后条件

FRAMES、DeepSearchQA、BrowseComp 在 A1 可只验证 metadata 与下载成本，不抢先投入长 Agent 运行；BrowseComp-Plus 明确暂不下载 2.78GB 查询数据或构建十万文档索引，需先审批磁盘预算与新增检索模式。Artificial Analysis / OpenBenchmarks 私有集合无法用公共样例推出官方榜分。

## 4. 正式筛题的统一规则（下阶段再执行）

每条候选的审查字段（**只定义 schema，不填真实题**）：

```yaml
benchmark_id: EXA | SEALQA | ... | CHINESE_GOLD
upstream_revision: <commit SHA 或日期版本>
dataset_split: <官方 split>
sample_uid: <稳定的原始题 ID 或文件+行号>
topic: <检索/技术文档/政策/学术/时效/冲突/...>
language: <zh/en/...>
problem_type: <single_answer|set_answer|unanswerable|extract_only|retrieval_only>
source_policy: <需要屏蔽的域名，含 archive/benchmark hosts>
evidence_source_ids: <独立 evidence/gold 文档标识，只放私有 Gold>
answer_as_of_utc: <如涉及动态事实则必须有时间点>
licensing_review: <OK|UNCERTAIN|RESTRICTED>
technical_feasibility: <DIRECT|ADAPTER_NEEDED|DEFERRED|BLOCKED>
exclude_reason: <不存在时置 null>
reviewer_decision: <CANDIDATE|SELECTED|REJECTED|HOLD>
reviewer_evidence: <审查说明路径>
```

入选规则：
1. **事实可核验**：单答案唯一或明确列允许别名；集合题应确认漏项和边界；技术文档题要有真实片段/代码/表格证据；禁止只有某一供应商的模型回答作为“真值”。
2. **可测且可接**：现有工具能访问合法来源，或明确列扩展任务；不能将失败的公网 URL 直接算“模型不会回答”；要分开 Fetch/Parse/Reason 错误。
3. **独立性**：用于开发的样本与正式盲测样本分开；正式 Gold 不进入模型 Prompt、搜索查询、工具结果或公开仓库，不使用同一 Agent 先偷看标准答案再测自己。
4. **污染控制**：优先不让被测 Agent 搜到 benchmark 问题/答案托管页；原始 BrowseComp/BC+ 的解密明文不上传；LiveNewsBench 强制禁新闻源域名及 archive。
5. **版本与时间**：动态题注明 as-of；页面可变时必须冻结 HTML、证据片段和 SHA，报告中区分 `LIVE_CURRENT` 和 `FROZEN_CORPUS`。
6. **代表性**：领域与困难度不是按榜单配比直接照搬。若做中文 200 题，初步意向是 40 普通事实、40 高校/政府政策、40 论文溯源、40 新近事件、30 跨来源/矛盾、10 无答案/错误前提，**现在只是计划配额，不是已选样本**。先试 60 题的开发流程，可按数据质量调整比例。
7. **评分可解释**：题目入选后再分别定义证据召回、答案正确/集合 P-R-F1、引用断言支持、拒答正确、重复运行方差；要记录 `answer_present_but_unretrieved`、`retrieved_but_not_extracted`、`extracted_but_wrong_answer` 等可归因类别。
8. **答题模型对照**：不搜索 / 只摘要 / 抓全文，控制相同模型、Prompt 和工具预算，API 型号/版本留档；不得将不同联网工具底层的隐藏能力当作同一操作。

筛题仓库交付建议：`docs/evals/screening/<benchmark_id>_candidate_review.md` 放**公开且不包含 Gold 的筛题理由**；私有 `evals/private_gold/<benchmark_id>/` 保存答案、原始来源与人工证据；`reports/evals/runs/` 放真实结果快照与非敏感哈希。严禁对整个数据集进行无许可二次分发。

## 5. 防止 E00 阶段越权执行的硬边界

- 这轮只批准 GitHub 文档、来源目录登记、待补验索引维护；**不批准实际付费模型/第三方搜索 API 调用、自动批量抓取全部真实题目或发布解密 Gold**。
- A1 的网络探测在用户 Ubuntu 明确授权且执行后才能标 `LOCAL_SMOKE_PASS`；本轮来源已公开也不代表已实机成功。
- 若真实许可证不清楚/非商业限制不匹配/源数据需登录或许可审批，**记录 BLOCKED，并优先推进别的基准**，不能改变数据许可说明或换镜像掩盖。
- 数据集一旦固定，保存上游 commit、zip/CSV/parquet 的 SHA256、脚本、评分器 SHA 和选择清单 hash，后续不可悄悄换题造成成绩不可比较。
- 计划以文档先行、固定 evidence、细分自动/人工两级验收为原则。上一阶段 B00–B08 G5 已通过，保留 GNU 连接例外；新的 E00 不修改 B 阶段既有结论。

## 6. E00 下一轮交接 Prompt（用于逐源小批量可用性验证）

> 阅读 `docs/evals/00_BENCHMARK_AVAILABILITY_AUDIT_20261014.md`、`docs/evals/BENCHMARK_SOURCE_REGISTRY.json`、`docs/evals/01_EVAL_ADOPTION_AND_SCREENING_PROTOCOL.md` 和 `docs/OPEN_VALIDATION_INDEX.md`。从 E00-A1 开始，只按候选来源验证真实可下载文件与 schema（先 EXA/SEALQA），记录真实 upstream revision/文件 SHA256/许可证/必要账号与运行命令。不要筛选具体题目、不要运行真实模型、不要将原始 Gold 推送到 GitHub。每一项探测通过/失败/未运行都更新 registry 和实施台账。A1 完成后再逐基准讨论选题。

