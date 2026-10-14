# Local Agent Web Search Demo — 分批实施与验收计划 v1.0

**状态：B00–B04 已通过；B05 本机与实机核验完成，G3 待用户审核** · 2026-10-14
**任务范围**：本地 SearXNG + HTTPX + Trafilatura + readability-lxml + Selectolax + OpenAI SDK；CLI + 极简 WebUI 双入口；测试可行性，不做商业化产品。  
**依赖文档**：[需求草案](./DEMO_REQUIREMENTS_DRAFT.md) ｜ [六项上游预研](./UPSTREAM_RESEARCH.md)。

> **进度真实性**：B00–B02 的本机验收见 [`B00_ACCEPTANCE.md`](./B00_ACCEPTANCE.md)、[`B01_ACCEPTANCE.md`](./B01_ACCEPTANCE.md)、[`B02_ACCEPTANCE.md`](./B02_ACCEPTANCE.md) 和实施台账；当前 B05 已实现双入口并完成本机与真实浏览器核验，G3 仍待最终用户审核；B06–B08 未执行。原文中的命令草案仅在实际实现的批次内视为可用。每个批次结束才允许写入实际运行证据。

**每批开始与交接必须查阅 [跨批次待补验索引](./OPEN_VALIDATION_INDEX.md)**。未通过的人工关卡、非阻断联网测试和失败补验不能因为进入下一批就消失。

## 0. 范围冻结与成功定义

### 0.1 本轮确定
1. 本地运行，无付费**搜索** API；SearXNG 通过 HTTP JSON 提供搜索；网页获取走 HTTPX，不运行 Chromium/Chrome/Playwright。
2. 三个正文处理组件都纳入测试：Trafilatura、readability-lxml、Selectolax；**本轮不根据主观判断删库**。
3. 两个可进入 AI 之前独立测试的动作：`search_web`（关键词）和 `read_webpage`（URL）；另有 Agent 模式让模型自己调用工具。
4. **统一 Python Core**；CLI 以 `argparse` 直接调用 Core；WebUI 为 FastAPI + 原生 HTML/JS，访问同一个 Core。
5. 测试数据同时暴露在 CLI / WebUI 和 JSON 报告中；观测“实际发生什么”，失败也是有效实验结果。
6. 不把 PDF、OCR、SPA 浏览器渲染、登录与验证码、复杂代理、缓存体系、UI 美化、生产级防护纳入本期。
7. 以 Python 3.11+ 为首选基准；首轮 Linux，Windows 作为可选兼容性检查，非阻断主流程（正式客户端跨端待后续）。

### 0.2 成功分层（不互相冒充）
- **核心流程成功**：指定测试环境可运行，搜索与网页获取/解析本地函数能够正确处理成功和失败，CLI 与 WebUI 调用相同函数。
- **Agent 闭环成功**：真实模型通过 SDK 生成**我们定义的**工具调用，本地执行并回传结果，模型据此回答；全链路保留证据。
- **实际网站覆盖率**：记录成功/失败与网页类型；**不以 100% 网站覆盖率作为 Demo 通过条件**。
- **端侧集成可行性**：提供运行条件、启动复杂度、依赖尺寸与主要耗时的实测记录；不直接宣称可跨端打包。

### 0.3 计划目录（创建时可作小幅调整，必须记录）
```text
local-agent-web-search-demo/
├── README.md
├── pyproject.toml              # 可重现依赖及运行入口
├── .env.example                # 假值，不保存真实 API Key
├── deploy/searxng/             # compose 与最小 JSON 配置
├── src/local_search_demo/
│   ├── config.py
│   ├── schemas.py              # 各入口共享的数据契约
│   ├── search/searxng.py
│   ├── fetch/httpx_fetcher.py
│   ├── parsers/{trafilatura_adapter,readability_adapter,selectolax_adapter}.py
│   ├── pipeline/{reader,chooser}.py
│   ├── agent/{runner,tool_registry}.py
│   └── interfaces/{cli,api}.py
├── web/                        # 原生 HTML/CSS/JS
├── tests/
│   ├── fixtures/html/          # 固定 HTML 样本，离线
│   ├── fixtures/search/        # 固定 JSON 搜索响应，离线
│   ├── unit/
│   ├── integration/
│   └── live/                   # 手动/显式 opt-in 联网用例
├── reports/                    # 本地生成（示例/非敏感摘要可提交）
├── docs/
│   ├── DEMO_REQUIREMENTS_DRAFT.md
│   ├── UPSTREAM_RESEARCH.md
│   ├── DEMO_EXECUTION_PLAN.md
│   └── IMPLEMENTATION_LEDGER.md  # B00 建立进度与验收台账
└── .references/upstream/       # 工作区内的 git clone，加入 .gitignore
```

## 1. 全部批次和验收门

| 批次 | 主要工作 | 本批自检 | 阶段性人工验收 |
|---|---|---|---|
| **B00** | 环境、六份上游 clone/版本锁、项目骨架、Schema 与样本准备 | 依赖可导入、pytest 能跑 | **G0**：本机能重现环境 |
| **B01** | SearXNG 本地部署、JSON 检索、上游错误区分 | Mock + 真实查询 | **G1**：真实搜索烟测 |
| **B02** | HTTPX 下载器、重定向/编码/超时/内容类型与耗时 | 离线 HTTP 服务 | 自检后继续 |
| **B03** | 三解析器适配器、原样本横向比较、错误标记 | 离线 fixture 逐一对比 | **G2**：人工复核正文 |
| **B04** | 统一读取管线、暂定兜底规则、CLI 三命令、JSON 记录 | CLI 回归 | 自检后继续 |
| **B05** | FastAPI API + 原生 WebUI：搜索、读取、结果并排与日志 | API 与 CLI 一致性 | **G3**：双入口人工验收 |
| **B06** | OpenAI SDK 客户端/工具声明/循环；Mock 模型测试 | 0/1/多工具和异常用例 | 自检后继续 |
| **B07** | 接入真实兼容模型，Agent 搜索→读取→回答 | 真实工具链与调用轨迹 | **G4**：Agent 实机验收 |
| **B08** | 端到端回归、故障场景、耗时和资源采样、实验报告 | 可复现测试总表 | **G5**：最终 Demo 验收 |

**节奏**：每批提交代码+本批证据；仅 G0/G1/G2/G3/G4/G5 需要明确阶段验收。人工在本地才能验证的内容不要用 CI/Mock 替代。只有当前关卡通过或带原因批准豁免才进入下一阶段；如果特定外部网络失败，可推进**离线子任务**，但不能把该门标成 PASS。

## 2. 每批执行卡（照此实施）

### B00 — 基线与可复现环境

**任务步骤**
1. 从 `main` 建工作分支；核对已有 README/需求/预研/本计划，创建 `IMPLEMENTATION_LEDGER.md`，登记批次状态初始为 `TODO`。
2. 建立 `.gitignore`，忽略 `.references/upstream/`、`.env`、`__pycache__`、虚拟环境、大体积临时结果/真实凭据。
3. 按预研文档将 6 份上游源码 clone 到本地参考目录（Selectolax 使用 `--recursive`）；为每份记录 `git rev-parse HEAD`。失败则记录原因，不伪造 SHA。
4. 创建 `pyproject.toml`、Python 虚拟环境、依赖锁定文件、`.env.example`、可用的空启动入口；锁定实际 Python 与包版本，并记录目标平台。
5. 建最小统一数据模型：`SearchResult`、`FetchResult`、`ParserResult`、`ReadResult`、`AgentTrace`、`ExperimentRecord`。创建至少 6 类固定 HTML/JSON fixture。
6. 写环境检查命令与最小测试，跑 `pytest`，保留环境信息（不包含令牌）。

**G0 验收**：
- 安装与导入均成功；`pytest` 可发现并运行测试；基本入口提供帮助；源码 clone SHA/依赖锁信息可追溯。
- 完整一套本地重建步骤可由另一终端执行；不要求此时搜索可用。
- **证据**：`reports/B00/environment.json`、`reports/B00/test-summary.txt`、台账更新。
- **若当前环境无法连接 GitHub**：本关卡标记 `BLOCKED_LOCAL`；可在其他可联网本地环境补做，不可标记 PASS。

### B01 — SearXNG 搜索层

**任务步骤**
1. 按官方容器文档准备本机部署（本地端口、settings 覆盖、启用 `html/json`）；避免把上游仓库内容复制进我方项目。
2. 创建 `SearXNGClient.search(query, limit, language?, time_range?)`，请求 `/search?format=json`，把不同引擎结果归一化为标题、URL、摘要、引擎、排序与失败信息。
3. 固定 JSON fixture 做无网解析测试，包括空结果、字段缺失、重复 URL、接口 403 和超时。
4. 用中英文各一条非敏感关键词进行真实搜索；记录来源引擎、结果个数、HTTP 状态、耗时、上游错误。不要把正常 HTTP 200 + 0 results 当成成功检索。

**G1 验收**：
- 真实请求可返回正确 JSON；至少一次从可用上游得到可点击结果，才记 `LIVE_PASS`。
- 模拟 403/429/超时/空结果时错误分类正确；真实上游失效单独标 `UPSTREAM_BLOCKED`，不谎称本地检索成功。
- **证据**：`reports/B01/search-smoke.json` + Docker Compose 状态与非敏感日志。

### B02 — HTTPX 获取层

**任务步骤**
1. 构建共享 `AsyncClient` 与统一下载 API；集中配置 timeout、连接限制、重定向。
2. 记录原 URL/最终 URL、状态、Content-Type、响应大小/编码、每阶段耗时、错误类型，输出原始 HTML。
3. 使用本地 HTTP fixture 服务模拟 HTML/redirect/404/429/慢响应/非 HTML/异常编码；另对 1–2 个真实网站尝试下载（非阻断）。
4. 使下载结果能直接交给解析器，不在此批尝试识别正文。

**本批通过条件**：固定测试全部通过，同一 HTML bytes 被保留，错误不被转换为假正文，下载与解析计时严格分开。  
**证据**：`reports/B02/fetch-tests.json`、pytest 输出。

### B03 — 三解析器并行评估

**任务步骤**
1. 分别做独立 adapter。Trafilatura 提供正文/元数据；Readability 保存 `summary()` 原 HTML 与规范化文本；Selectolax 通过固定 CSS/标签优先级获取文本和候选结构。
2. 各 adapter **只接收同一份已经下载的 HTML**，不在 adapter 内联网；读取过程中分别计时。
3. 用至少六类 fixture：文章、新闻/多导航、技术文档、短正文/中文、空或 SPA 壳、格式异常 HTML。
4. 记录 raw、normalized、title、字符数、是否有正文候选、异常、耗时；补充人工判定 `correct / partial / noise / no_content` 与理由。
5. 专门用同一份 HTML 横向比较，确认三工具输出确实各自可见。记录 Trafilatura 内部已含 readability 类型回退的重合性。

**G2 验收**：
- 三 adapter 可逐一单独运行，缺一个也不导致其他两个结果丢失；对至少六类 fixture 均有结果记录（包括负例）。
- 至少一类可读文章提取出预设的正文锚点；SPA 空壳/空页面不伪造正文；人为核对重复导航和乱码问题。
- **此时不要求选出最优解析器、不设置虚假的成功率 KPI。**
- **证据**：`reports/B03/parser-comparison.json` + 人工标注表。

### B04 — 统一 Core、回退和 CLI

**任务步骤**
1. 实现 `read_webpage(url)`：一次抓取 → 三 adapter 尝试/可单独复现 → 选择当前最佳候选 → 返回结构化证据。
2. 第一版选择策略只求**可解释**：空值/失败跳过、明显噪声降级、正文锚点与结构优先；每次记录选择哪个、为什么、拒绝了哪些。不要依靠“字数最多”单一指标。
3. 提供 `python -m local_search_demo search "<query>"`、`read "<url>"`、`agent "<question>"` 命令架构；Agent 未实现时返回明确 `NOT_IMPLEMENTED`。
4. CLI 支持 `--json` / `--output`；保存单次实验记录，不混入密钥/敏感请求头。
5. 从固定 fixture 到 Core 的完整离线链路做回归。

**本批通过条件**：搜索与读取可以**不依赖模型**独立使用；每次结果可复现地写 JSON；故障与兜底选择均可查。  
**证据**：`reports/B04/cli-smoke.json`、CLI 日志。

### B05 — 轻量 WebUI 与 CLI 一致性

**任务步骤**
1. FastAPI 暴露最小 API：`GET /health`、`POST /api/search`、`POST /api/read`、后续 `POST /api/agent`。
2. 原生 HTML/JS 三个页签：关键词搜索 / URL 网页解析 / Agent；第三页签暂展示“未实现”，B07 激活。
3. 列出搜索结果；网页对比展示三个解析器输出、原始和最终 URL、耗时、失败原因及选用结果；无需 CSS 精修。
4. API 直接调用 B04 Core，不允许复制一套搜索或解析算法。用 FastAPI `TestClient` 测接口。
5. 同样的 fixture 输入，在 CLI 与 API 中得到一致的**核心字段**（排除 run_id、时间戳、UI 排版）。

**G3 验收**：
- 一次本机启动后，网页能够执行搜索与 URL 解析并呈现三个 adapter 的不同结果；错误能显示。
- CLI / API 的选择结果与正文一致；切换 UI 不影响底层测试结果。
- **证据**：`reports/B05/api-tests.json`、对照 JSON、WebUI 实机截图（人工提供/生成，不用截图替代自动测试）。

### B06 — OpenAI SDK 工具循环（先离线）

**任务步骤**
1. 定义 `search_web` / `read_webpage` JSON Schema 和执行映射，严格复用 B04 Core。新增 `AgentRunner` 和 `ModelProvider`。
2. 模型设置 `base_url/api_key/model/api_mode(chat_completions|responses)`；至少实现一个与指定测试模型兼容的实际 API 路径，并显式探测或记录不兼容。不能默默回落到服务商的内建联网。
3. Mock 模型输出四组轨迹：无工具、一次搜索、搜索后读 URL、多工具与异常 JSON 参数；确保结果被回传正确的调用关联 ID，错误不会无限循环。
4. 设置最大工具调用轮数、运行超时与响应日志；`tool_choice=required` 类策略只用于**验证函数调用通路**，自主判断测试必须使用自动策略。

**本批通过条件**：Mock 下真实本地 `search_web`、`read_webpage`（可喂 fixtures）被执行并产生结构化轨迹；错误/零工具/多工具正常终止。  
**证据**：`reports/B06/tool-loop-tests.json`、pytest 输出。

### B07 — 真实模型 Agent 闭环

**任务步骤**
1. 接入用户提供/本地运行的 OpenAI 兼容模型，记录真实支持的 API 模式；API Key 仅来自环境变量、永不写入报告。
2. 用明确需要联网的提问与一个无须联网的控制问题分别测试；同时测试强制工具通路和自动选择通路，**不能拿强制搜索证明 AI 自主判断**。
3. 实际运行「模型请求搜索 → 本地 SearXNG 返回 URL → 模型请求读取 → 本地解析返回正文 → 模型引用来源回答」。
4. 对失败细分为：模型接口不兼容 / 模型不调用工具 / 搜索上游无结果 / 页面无法读取 / 提取噪声 / 回答未引用证据。
5. 收集模型调用轮数、工具参数、真实结果、每步时长、最终引用的 URL；不得由测试脚本事后编造模型未调用的工具。

**G4 验收**：
- 至少有 **1 个真实模型 + 1 个真实联网问题** 完成完整 search → read → answer 闭环，且轨迹可确认是本地函数实际执行。
- 模型回答的引用 URL 必须出现于本次成功搜索/读取记录；不对证据不足内容强行下结论。
- 无工具控制问答不强制要求每次零调用，但必须如实记录自动决策表现。
- 若没有兼容模型或外部服务不可达，只能标 `BLOCKED`，不以 Mock 当作真实 Agent 通过。
- **证据**：`reports/B07/agent-live.json`、无密钥日志及人工复核记录。

### B08 — 整体验收、瓶颈分析和后续清单

**任务步骤**
1. 执行完整离线 pytest、CLI/API 同值对比、SearXNG 真实烟测、真实 Agent 闭环复验。
2. 对网页类型分别记录覆盖：正常文章、噪声新闻、技术文档、短中文、SPA 壳、429/超时/拒绝；失败也须留下结果。
3. 至少记录 **5 个真实网页** 的每种解析器结果与人工评语；记录对应的访问日期、网站类别、成功/失败，不把 5 个固定站点推广为全网成功率。
4. 采样搜索/下载/解析/模型/总耗时及本机内存与进程占用（尤其 SearXNG Docker）。
5. 生成 `DEMO_TEST_REPORT.md`：测试环境、包版本、上游 SHA、复现命令、通过项、失败项、限制、后续优化候选；**不在本轮删库**。

**G5 最终验收**：
- G0–G4 不存在未解释的 `FAIL`；若存在 `BLOCKED`，报告应明确“部分完成”而非“全部通过”。
- CLI 独立搜索和读取正常；WebUI 与 Core 一致；真实 Agent 闭环有可核验证据。
- 六类 fixture + 至少五个真实网页有测试记录，失败分类、各阶段耗时和解析器比较报告完整。
- 复现指令可在同类 Linux 本机环境执行；没有 Chromium 路径、没有把模型自带搜索冒充本地搜索。
- **证据**：`docs/DEMO_TEST_REPORT.md`、`reports/B08/`、最终验收表和待办列表。

## 3. 数据协议和评价表：开工即固定字段

建议结果结构如下，细节允许补充但主字段不可无声变动：

```json
{
  "run_id": "example",
  "mode": "search|read|agent",
  "timestamp": "ISO-8601",
  "query": null,
  "url": null,
  "search": {"status": null, "items": [], "elapsed_ms": null, "errors": []},
  "fetch": {"status": null, "url_requested": null, "url_final": null,
            "http_status": null, "content_type": null,
            "bytes": null, "elapsed_ms": null, "error": null},
  "parsers": [
    {"name": "trafilatura|readability|selectolax", "status": null,
     "raw_output": null, "text": null, "title": null,
     "chars": null, "elapsed_ms": null, "error": null}
  ],
  "selected_parser": null,
  "selection_reason": null,
  "agent": {"provider": null, "model": null, "api_mode": null,
            "tool_calls": [], "answer": null, "cited_urls": []},
  "total_elapsed_ms": null
}
```

注：缺失字段保持 `null`，不要造空白的成功结果；大型 HTML 原文放单独文件并在 JSON 引用路径，不在每条记录重复存储。自动测试中的期望锚点和人工评价需单独保留。

**人工质量标记**：`correct`（标题/主旨/指定正文锚点可读）、`partial`（缺失重要段落）、`noise`（大量导航/推荐/混入）、`no_content`（没有正文）、`blocked`（网络/站点/资源限制）。比较表务必列实际页面 URL/fixture ID 与主观判断理由。

**计时与性能**：统一采用毫秒，并分别记录搜索 / 下载 / 三解析器 / 模型 / 总耗时。若并发，分阶段耗时之和不等于端到端耗时，不强制相加。目标是测量真实行为，**不预设“全链路 < 5 秒”之类虚假硬性通过标准**。

## 4. 测试环境、命令与证据约定

以下命令是**目标命令草案，尚未实现**；实际创建后须与 README 对齐，不得把本段当作已验证使用说明：

```bash
# B00: 环境
python --version
python -m pip install -e ".[dev]"
pytest -q

# B01: 本地 SearXNG（实际目录与 compose 文件在 B01 产生）
docker compose -f deploy/searxng/compose.yml up -d
curl -sS -G http://127.0.0.1:8080/search \
  --data-urlencode 'q=python asyncio' --data-urlencode 'format=json'

# B04: CLI
python -m local_search_demo search "python asyncio" --json
python -m local_search_demo read "https://example.org/" --json

# B05: UI（实际导入路径以实现为准）
uvicorn local_search_demo.interfaces.api:app --host 127.0.0.1 --port 8765

# B07: 模型（本地环境变量配置，永远不要把令牌提交到仓库）
python -m local_search_demo agent "搜索并阅读最近的 Python 文档更新" --json
```

**每批交付五件**：
1. 对应的变更清单、commit SHA；
2. 本批测试命令与结果摘要（PASS / FAIL / BLOCKED / NOT_RUN）；
3. 自动化输出与需人工执行的本机任务列表；
4. 未解决问题与是否阻断下一批的判断；
5. `docs/IMPLEMENTATION_LEDGER.md` 里更新本批状态、证据路径与验收结论。

**验收必须区别**：
- `PASS`：有实际运行证据且达标；
- `FAIL`：已执行但违反标准；
- `BLOCKED`：环境、外部网络、模型或凭据阻断；
- `NOT_RUN`：尚未执行；
- `WAIVED`：经明确批准跳过的可选项，须注明后果。
- 任何未发生的联网/实机测试都不得被离线 Mock 或 CI 虚构为 PASS。

## 5. 优先级、风险与回滚

**P0 必做**：B00–B08 的核心交付；SearXNG JSON、下载器、三解析器结果、CLI/WebUI 一致、实际 Agent 工具回环、客观报告。  
**P1 可选**：语言和时间筛选、吞吐实验、多模型比较、JSON-LD 额外提取、Windows 运行、Responses 与 Chat Completions 双协议同时支持（**若测试模型仅支持其中一种，该模式升为 P0**）。  
**P2 后续**：PDF/OCR、浏览器动态渲染、反爬登录、客户端嵌入、跨平台打包、持久缓存、向量检索、生产级网络安全与授权策略。

**主要风险**：
- 本机无法下载源码/容器镜像：B00/G0 `BLOCKED`；
- SearXNG 服务启动但上游封禁：B01/G1 `UPSTREAM_BLOCKED`，可先继续离线 fixture，不算在线通过；
- read-only SPA 页面无正文：B03/B08 记真实边界，不强行用字符串长度伪造正确结果；
- 被选模型不支持当前 API 模式：B06/B07 记录 provider 能力并切换已实现模式，仍失败则 BLOCKED；
- 提取结果偏差明显：保留三个 adapter 输出、人工理由和失败样本，不在 Demo 临时删库；
- SearXNG 太重不便端侧嵌入：B08 记录真实资源开销，后续产品阶段才裁决保留/替换。

**变更规则**：当某批发现必须变更 Schema/验收标准，先把“旧标准、变更原因、影响批次”追加到台账，再调整实现；不得事后修改标准来包装失败结果。当前计划只作为 Demo 开发和验收的单一执行依据，不自动代表已完成工作。

## 6. 当前执行状态

| 批次 | 状态 | 说明 |
|---|---|---|
| B00 | PASS | 本机技术检查、六份上游 clone、32 项测试及独立环境重建通过；人工阶段签认尚未发生，见验收报告 |
| B01 | PASS / LIVE_PASS | 本机 55 项离线回归、Docker 状态、镜像锁、原始 JSON、CLI 和中英文真实搜索通过；上游错误与首轮网络失败均保留 |
| B02 | PASS / LIVE_PASS | 本机 91/91 回归通过（含 36 项获取层测试）；两个真实 HTML 下载与保存 bytes 的 SHA-256 比对通过 |
| B03 | PASS / G2 PASS | 本机 109/109（18 项 B03）通过；18 组内容复核与理由完整，用户已明确签认，工作表检查退出 0 |
| B04 | PASS / LIVE_PASS | 已接受 B04 CI 124/124；2026-10-14 两个目标机真实 CLI read 通过，与 WebUI 核心字段相同 |
| B05 | SELF_CHECK_PASS / HOST_BROWSER_PASS / G3 USER_REVIEW_PENDING | 本机 133/133、CLI/API 5/5、真实浏览器 17/17，16 张截图已复核；最终用户审核待办 |
| B06 | NOT_RUN | 等待 B04 |
| B07 | NOT_RUN | 等待 B05/B06 及模型配置 |
| B08 | NOT_RUN | 等待完整联调 |

**当前交付：B05/G3 实机证据。** B04 公网 read 待办已补验；B05 完成本机回归、真实浏览器操作与截图复核，等待用户审核具体证据后签认 G3。B06–B08 未执行。
