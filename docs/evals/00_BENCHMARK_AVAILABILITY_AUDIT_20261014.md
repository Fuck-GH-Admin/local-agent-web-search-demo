# E00｜联网搜索评测基准可用性审计 v1.0

**核查日期：2026-10-14**  
**状态：UPSTREAM_RESEARCH_COMPLETED / LOCAL_DATA_DOWNLOAD_NOT_RUN / QUESTION_SELECTION_NOT_RUN**  
**目标仓库：** `Fuck-GH-Admin/local-agent-web-search-demo`，继承 B00–B08 的已签收工程基线，**不改变 G5 PASS（含 GNU 例外）**。

> 本文是“选什么测评有意义、数据从哪来、是否能合法而可重复地测试”的可行性调研，**不是测评成绩**。本轮核查了项目官方 GitHub/Hugging Face、README、数据卡和方法论页面；没有在目标 Ubuntu 下载完整数据、打开付费裁判 API、运行任何 benchmark、评判或筛选具体题目。不要把 `公开可见` 写成 `本机可执行 PASS`。结构化来源见 [BENCHMARK_SOURCE_REGISTRY.json](./BENCHMARK_SOURCE_REGISTRY.json)。

## 0. 本项目真实被测能力和边界

现有链路是 `本地 SearXNG(JSON) → HTTPX 单次下载 → Trafilatura / readability-lxml / Selectolax 三份文本 → 候选选择 → AgentRunner + OpenAI 兼容模型`，同时有 CLI、FastAPI/WebUI 和 `ExperimentRecord` / `AgentTrace` JSON。现有 `SearchItem` 记录 url/title/snippet/engines/rank，`ParserResult` 记录原始输出/正文/耗时，`ToolCall` 记录参数、调用 ID 和结果。

**已发现而评测需要解释的缺口：** B08 真实页面中存在 Selectolax 导航噪声、Readability 部分正文缺失、SPA 空壳、GNU 中文站点访问 BLOCKED；模型成功读取的文本可能被截取前 6,000 字符；当前 `cited_urls` 只能判断引用是否来自成功读取的 URL，**不能证明每项断言受到该正文支持**。B08 工程成功率和 347/347 回归**绝非**统一的检索或答案准确率。

因此后续一定分别衡量：SearXNG 搜索结果是否包含必要证据、下载是否成功、三解析器是否保留证据、候选正文是否正确、模型能否基于证据答对与正确引用。还要分开记录线上动态搜索（索引随时间变化）与固定文本/固定 corpus（可复现检索），不得混成同一分数。

### 状态语义（此文及 registry 通用）

- `UPSTREAM_METADATA_VERIFIED`：官方仓库/数据卡与数据结构存在；**不代表已能下载、加载或在目标机运行**。
- `PUBLIC_SAMPLE_PRIVATE_OFFICIAL`：公开样本与正式私有评分集不同；仅能做程序适配，不能复刻排行榜。
- `METHOD_PUBLIC_PARTIAL_DATA`：公开方法论，但全部评测题、闭源裁判或运行器不完全可得。
- `DOCUMENTATION_VERIFIED`：工具文档公开，不代表已验证当前项目兼容。
- `PLANNED_ONLY`：仅提出自建数据集；尚无题目/金标。
- 所有适用的 `local_probe` **NOT_RUN**；下一批在 Ubuntu 以锁版本/最小下载测试后才能升级。

## 1. 结论一览：数据许可、接入难度和取舍

| ID / 基准 | 实际可用性与许可 | 我们要测的层 | 接入/评分风险 | 决策 |
|---|---|---|---|---|
| EXA：Exa Search Benchmarks | 四类 benchmark 源码与基准入口公开；仓库 **MIT** | 搜索 Recall/MRR、论文溯源、技术文档抽取 | 自定义 `Searcher` 易接；部分子项目运行命令依赖 Exa/OpenAI 等 Key；各子集 gold 文件仍须实机核验 | **P0，先做适配可行性验证** |
| SEALQA：SealQA | HF 三个测试配置 `seal_0` / `seal_hard` / `longseal`、Apache-2.0 | 搜索噪声/冲突、证据不足、最终事实判断 | 独立评分模板、LLM Judge 版本与 LongSeal 上下文预算；HF 内容会更新，必须 pin revision | **P0，先试前两个配置** |
| CHINESE_GOLD：项目中文金标 | **未建题、未选题、未授权复制第三方数据** | 中文官方政策/论文/时效/引文 | 人工查证成本最高；需要私有 Gold 与盲测隔离 | **P0，先定义 schema，选题留下一批** |
| FRESHQA：FreshQA | 仓库 Apache-2.0；数据主要经**具日期的 Google Sheets** 公布，带 FreshEval notebook | 时效性、错误前提、不该答的题 | 公开入口可见不等于 CSV 已下载；仓库当前首页显示 2026-04-21 表，更新提示可能过时；需要按日期复核 | P1 |
| LIVENEWS：LiveNewsBench | 仓库 MIT；公开 JSONL train/val/test/human_verified_test；README 目前列出 **2025-09、2026-01 两个正式 release** | 新近事件、搜索行为、答案时效 | 不能宣传为 2026-10 当周数据；官方要求屏蔽出题源新闻域名及 archive；默认 **5 searches + 5 visits**，须与现有 8 工具总上限对齐或申明偏离 | P1，有条件精选 |
| CRAG：Comprehensive RAG Benchmark | 官方 `facebookresearch/CRAG`，数据说明与下载入口公开；**CC BY-NC 4.0** | 证据噪声、回答与弃答、动态答案 | Task1/2/3 配不同 mock web/KG；Task3 较大；非商业许可要遵守；不等于真实 SearXNG | P1，固定上下文子集 |
| OPENBENCH：OpenBenchmarks | 公开 runner；正式多轮企业搜索 **45 私有题**，另有 **10 公开样例**；网站公开成绩数据按 CC BY 4.0 | 固定 Agent / 更换搜索供应商 / 集合 F1 / 成本 | 不能拿 10 道样例复现私有排行榜；以方法与协议为主；代码/data 许可分开审阅 | P1 方法参考 |
| FRAMES | 824 条公开 HF test，Apache-2.0；有 Wikipedia gold links | 多页证据组合与推理 | Wikipedia 页面动态变化，URL≠冻结正文；至少 2–15 页，需额外工具预算 | P2 |
| DEEPSEARCHQA | 900 条公开 HF `eval`，Apache-2.0；约 65% 是答案集合题 | 深度研究集合 P/R/F1 | 官方指定 Gemini 2.5 Flash + judge prompt，替换裁判不可与官方分数混比；预算较高 | P2 小规模 |
| BROWSECOMP | OpenAI 官方 1,266 道**加密**题，simple-evals 体系 | 极难多跳、搜索策略 | 官方防泄漏提示明确**不要把解密题/答案以明文发布**；数据具体许可条款继续复核；当前 Agent 限 6 回合/8 工具难以公平跑 | P2，暂不全量 |
| BROWSECOMP_PLUS | HF 830 题，100,195 篇固定 corpus 文档；数据卡 MIT；**查询数据集页面显示总文件 2.78 GB**，另有 corpus | 真正隔离固定检索器与 LLM | obfuscated 字段与较大语料；须新增离线索引/BM25/向量检索；**不能用实时 SearXNG 的联网结果冒充固定 corpus 结果** | P2 依赖新架构 |
| AA_SEARCH：Artificial Analysis Search Index | 公开方法论 + 排行榜；其组合用 900 DeepSearchQA / 200 BrowseComp / **600 私有 AA-Omniscience** | 统一模型仅替换搜索 API、model-only uplift/成本/延迟 | 私有部分不可复刻，公开排行榜数字不是我们本机成绩 | **仅方法参考** |

### 实际抽样前的明确建议

1. **最先验证可运行的候选**：EXA Publication Retrieval、EXA WebCode Contents、SEALQA Seal-Hard/Seal-0、中文自建金标方案。
2. **第二批才下载并选题**：FreshQA（明确日期的 CSV）、LiveNewsBench（先区分版本与是否真正“新”）、CRAG Task1 固定证据。
3. **后续扩展**：FRAMES、DeepSearchQA、BrowseComp 子集；BrowseComp-Plus 需要先决定是否建离线索引。
4. **当前不单独当作题库**：Artificial Analysis、OpenBenchmarks 45 私有题官方榜、Promptfoo、Ragas。OpenBenchmarks 的 10 公开样例只用于接口契约适配，不能用于官方复现。

## 2. 分源可用性细节与初步接入路线

### EXA｜优先测试搜索与抓取，不照搬供应商成绩

源：[官方 benchmarks GitHub](https://github.com/exa-labs/benchmarks)。项目公开 `shared.Searcher` 的 `search(query,num_results)` 与 `extract(url,query?)`，包括 WebCode（~840，Contents/Highlights/RAG/E2E）、People（1,400）、Company（~800）、Publication（1,866）。其中 WebCode Contents 是 250 个 URL 的正文抽取，对我们 B08 的表格、代码、导航噪声更有诊断价值；Publication 适合金标题录、DOI、作者/出版信息。

**接法**：写 `SearXNGSearcher.search → search_web`、`extract → read_webpage` 的薄适配器，保持标题/URL/摘要/排名/错误映射。单测先对固定 SearXNG JSON；真正计算论文 Recall@K 前必须核对“唯一正确目标”/DOI/跨镜像 URL canonicalization。对 WebCode Contents，三个解析器应都使用**相同下载 HTML**，分开评分；不能给各解析器不同时间重新抓网页。

**阻断**：官方快速运行示例展示 `EXA_API_KEY`/`OPENAI_API_KEY`；非 Exa 的本地检索试验可不需要 Exa Key，但**官方 LLM 裁判**需要相容模型 API 及配额。README 出现公开基准并不证明本机拿到了 gold markdown、每题评分材料。后续必须逐子集记录数据文件/下载方式/许可/哈希。

### SEALQA｜难题与冲突信息，不等于已经有引用标注

源：[HF 数据卡](https://huggingface.co/datasets/vtllms/sealqa)，Apache-2.0；`seal_0`、`seal_hard`、`longseal`（其中 LongSeal parquet 明显更大）。官方注明题目旨在测试**冲突、噪声或无帮助的搜索结果**，并提供裁判模板及历史版本。**不要**直接推断每题都有标准化的证据 URL / 引用跨度标注；须实际检查字段后决定是否可用于 Citation Support 评分。

**接法**：先在固定模型和固定预算下测试 `model-only`、`search-only snippets`、`search+read`；Gold 与已知正确答案严格隔离。对采集的网页正文另外按每条断言手工核对“支持/反驳/证据不足”。SealQA 成绩可衡量解题，不自动等于我们检索 Recall@K。

**阻断**：数据在更新；下一批需 pin Hugging Face commit SHA，检查 config/split/schema 和 judge prompt；LongSeal 还须考虑本地 Agent 文本截断与上下文容量。

### FRESHQA / LIVENEWS｜版本冻结是第一步

FreshQA 源：[官方仓库](https://github.com/freshllms/freshqa)。GitHub 主页提供 **2026-04-21** 的 FreshQA 数据表入口，也显示“每周/按需更新”的说明，但不能据此断言最新已更新至 2026-10。数据以 Sheets 为主，第一步应进行只读 CSV 导出、固化 SHA、记录表格版本及问答的 as-of date；不要直接调用最新 Sheets 覆盖已冻结历史 Gold。FreshEval 推荐使用较旧 GPT-4 裁判配置，这种原版配置不可无说明地与新版评分器混用。

LiveNewsBench 源：[官方仓库](https://github.com/YunfanZhang42/LiveNewsBench)。README 明确包含 `event_date`、`question`、`answer`、`link` 和四种 JSONL split；公开仓库当前只保证前两次 release，**不保证最新新闻**。正式测试要封锁出题新闻 `link` 对应域名和 Internet archives，避免搜到题库或原新闻直接泄漏答案；这一点会引出我们 SearXNG 搜索结果和 read 工具的**查询源过滤适配需求**。不可只靠 Agent Prompt 声明不去该域名。

### CRAG｜从固定证据和弃答开始

源：[官方仓库](https://github.com/facebookresearch/CRAG) / [数据结构](https://github.com/facebookresearch/CRAG/blob/main/docs/dataset.md)。包含 `query_time`、`static_or_dynamic`、`false_premise`、网页 `search_results`（含 HTML），适合重演相同证据下，模型是否错误推断/无证据乱答。Task1/2 可取 5 页面上下文，Task3 的最多 50 页配 mock KG，明显超出首批目标。**遵守 CC BY-NC 4.0**，特别注意将来若有商业用途需另行评估数据许可，不可把 CRAG 数据直接混入可商用产品/训练集。

### OPENBENCH / AA_SEARCH｜学习比较设计，不追官方榜名次

[OpenBenchmarks runner](https://github.com/openbenchmarks-labs/multi-turn-company-search) 的官方主榜用 **45 道私有多约束企业检索题**，公开仅 10 条样例供运行器/适配器试验。无法通过这 10 道复刻主榜；我们应该借鉴同题同模型同工具预算、多次独立重复、搜索源交换和精确集合 P/R/F1。其网站条款将**网站发布的成绩/JSON 数据**设为 CC BY 4.0，不代表任意代码或私有 Gold 自动同许可。

[Artificial Analysis 方法](https://artificialanalysis.ai/methodology/search-api) 的指数合并 DeepSearchQA / AA-Omniscience / BrowseComp，并记录模型不开搜索的基线、搜索费用和延迟。它会用统一模型切换搜索提供者，同时做防污染筛选；当前我们没有它的私有 AA-Omniscience 600 题与完整运行环境，故**不宣称可复刻其公开名次**。

### FRAMES / DSQA / BrowseComp / BC+｜第二阶段的依赖边界

- [FRAMES HF](https://huggingface.co/datasets/google/frames-benchmark)：824 条 test、有参考 Wikipedia links。适合把“检索证据充分性”和“跨页面推理”分开，但需要冻结 Wikipedia 页面版本，避免网页变更与知识答案混淆。
- [DeepSearchQA HF](https://huggingface.co/datasets/google/deepsearchqa)：900 条 eval + 官方 gold，65% 为答案集合。官方指定 `gemini-2.5-flash` + 指定判题模板；若换为其它裁判，只能标为**自定义成绩**，不可与官方排名直接比较。
- [OpenAI BrowseComp](https://openai.com/index/browsecomp/) / [simple-evals](https://github.com/openai/simple-evals)：1,266 道加密高难题。须保留加密来源、严格本机解密、禁止发布明文 Gold，防泄漏。我们目前默认 Agent 最多 6 回合/8 工具次数（实际配置请使用运行元数据），与深度研究 Agent 的搜索深度差异很大。
- [BrowseComp-Plus HF](https://huggingface.co/datasets/Tevatron/browsecomp-plus) / [固定语料](https://huggingface.co/datasets/Tevatron/browsecomp-plus-corpus)：830 题、100,195 篇固定文档、Gold/Evidence/Negatives 标注；query 数据卡显示总文件 **2.78 GB**，还要另建本地检索索引。该固定语料与公网实时搜索不等价；部署前估算 corpus + 索引 + 缓存磁盘与内存需求，并禁止往仓库上传解密明文。

## 3. 评分工具的实际用途，不给工具名冒充题库

| 工具 | 适配价值 | 现在是否安装 |
|---|---|---|
| [Promptfoo](https://www.promptfoo.dev/docs/guides/llm-as-a-judge/) | 用配置运行 prompt/model A/B 和 judge 结果；先人工校准样本 | **不安装**，先用现有 pytest/JSON/uv |
| [EvalScope BrowseComp 文档](https://github.com/modelscope/evalscope/blob/main/docs/en/benchmarks/browsecomp.md) | 已公开 BrowseComp 数据集映射和 Agent 模式说明 | **暂不安装**；进入 P2 再 pin 版本与依赖 |
| [Ragas](https://docs.ragas.io/) | Faithfulness、Context Recall 等现成概念 | **不安装**；Faithfulness 只代表“忠实于给定上下文”，不保证原始网页事实正确 |
| [OpenAI Eval best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices?api-mode=responses) | 任务专属数据集、独立评分器、人工校准、可复现轨迹 | **方法约束**，不是搜索 API 数据集 |

本期不修改 `pyproject.toml` / `uv.lock`，不引入 Node/LLM judge 等新的运行依赖；正式新增依赖需要单独批次评测锁文件与 CI。

## 4. 版本、许可证和 API 费用的审计准则

1. **数据许可证与代码许可证分开**：优先读取官网 `LICENSE` 和具体数据卡；未知项标 `UNVERIFIED`，不得假定可商用或允许重新分发原始题目。
2. **公开网页≠实际文件可取**：本轮仅做网页/仓库页面核实，HF 大文件、Google Sheets CSV、私有 45 题、完整数据 hash/加载状况均未经 Ubuntu 验证。下一批必须在本机小规模只读探测；不得在当前调研结果写出“已下载可用 PASS”。
3. **评分器版本必须固定**：官方裁判、提示词、规范化逻辑、时间版本不可在批次中悄悄更换；不同 judge 的自定义分数必须独立报告。
4. **防泄漏**：测试 Agent 看不到 gold/source labels；Search/Read 封锁 benchmark 托管链接、Canary 与明确要求屏蔽的新闻来源域名；公开仓库不推解密 BrowseComp/BC+ Gold、受版权保护的整网页内容和含密钥 Trace。
5. **实际费用未实测**：如需 LLM grading / 实际 model runs，先估算采样问题数 × 模型回合/输出 tokens × 价格，不得写虚构费用。模型与 SearXNG 无法保证 provider 自带搜索行为一致；任何对比都需声明工具预算、指数样本、日期与代理。
6. **评分公平性**：同一网页只下载一次分别交给三解析器；同模型更换搜索提供者时同时固定 prompt、top-K、fetch 策略、工具总次数、输入长度与评分器。实时多供应商对照尽量在相同时间交错执行并报告方差。
7. **数据版本快照**：记录 `source_url`、upstream commit SHA/revision、数据文件 SHA256、许可、抓取/答案时间、split、schema、排除域名及人工复核时间。不能拿“latest”替代版本号。

## 5. 具体下一步（只验证数据可用性，不筛题）

按 [E00 接入与筛题协议](./01_EVAL_ADOPTION_AND_SCREENING_PROTOCOL.md)：

- `E00-A1`：在 Ubuntu 测试候选目录、最小数据或 manifest 的下载/读取、split/schema/license 和哈希，**绝不传入真正 Agent**。优先 EXA/SEALQA，再 FreshQA/LiveNews/CRAG；将状态从 metadata verified 升至 `LOCAL_SMOKE_PASS` 或 `BLOCKED`。
- `E00-A2`：针对每套测试明确我们实际能实现的评分层及需要的额外工具；可用性与有价值性分离。
- `E00-A3`：确认独立金标存储、防泄漏与评分规范后，**再与你逐测试筛选具体题目**。本轮没有抽选任何题（`questions_selected=0`）。
- 本轮先写调研和筛选合同，**不声称 E00-A1 下载/运行已完成**。

## 6. 原始来源索引（优先官方）

[EXA](https://github.com/exa-labs/benchmarks) · [SealQA](https://huggingface.co/datasets/vtllms/sealqa) · [FreshQA](https://github.com/freshllms/freshqa) · [LiveNewsBench](https://github.com/YunfanZhang42/LiveNewsBench) · [CRAG](https://github.com/facebookresearch/CRAG) · [OpenBenchmarks](https://github.com/openbenchmarks-labs/multi-turn-company-search) · [FRAMES](https://huggingface.co/datasets/google/frames-benchmark) · [DeepSearchQA](https://huggingface.co/datasets/google/deepsearchqa) · [BrowseComp](https://openai.com/index/browsecomp/) · [BrowseComp-Plus](https://huggingface.co/datasets/Tevatron/browsecomp-plus) · [Artificial Analysis](https://artificialanalysis.ai/methodology/search-api)。

特别提醒：官方链接证明该仓库/数据卡存在；**链接不构成特定版本数据可下载、完整运行器可复现和许可证适用于所有附属素材的保证**。这些未完成状态已经列入项目跨批次待办索引。
