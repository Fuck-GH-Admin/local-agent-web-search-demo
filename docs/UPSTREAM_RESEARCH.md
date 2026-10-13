# 上游技术预研与源码阅读记录（2026-10-13）

**历史预研记录**：本文件下方保留 B00 之前的获取状态。B00 已在新本地工作区完成六份 clone、依赖安装和基线测试，详见 [`B00_ACCEPTANCE.md`](./B00_ACCEPTANCE.md)；尚未验证真实搜索、正文提取或 Agent。基线需求：[`DEMO_REQUIREMENTS_DRAFT.md`](./DEMO_REQUIREMENTS_DRAFT.md)。

## 一、阅读范围与真实获取状态

- 官方文档、仓库 README、可定位的部分源码均已阅读，以下逐项目列出直接链接。
- 曾在临时工作区执行 `git ls-remote https://github.com/encode/httpx.git HEAD`，返回 `Could not resolve host: github.com`；因此**当前工作容器未克隆任何上游仓库、未安装这些依赖、未进行实测**。
- 不以网页搜索摘要冒充本地源码分析；写下的实现信息只来自所列文档/可在线查看的源码。
- 上游 `main/master` 和 `latest` 是移动目标。**B00 需要记录实际 clone 的 SHA、包版本与镜像 digest**，此文件不是依赖锁定清单。

## 二、逐项目研读记录

### 1. SearXNG — 搜索服务

**定位**：自托管元搜索服务，内部以不同引擎适配器向外部搜索源发起请求、汇总结果；不是自带全网网页索引。

**已核对的文档**
- [Search API](https://docs.searxng.org/dev/search_api.html)：`GET /search?q=...&format=json`（也支持 POST 表单）；`q` 必填；`language`、`pageno`、`time_range`、`categories` 等有条件适用。
- [架构](https://docs.searxng.org/admin/architecture.html)、[Engine Overview](https://docs.searxng.org/dev/engines/engine_overview.html)：搜索来源由适配器和设置配置，个别上游失效不等于本地服务宕机。
- [容器部署](https://docs.searxng.org/admin/installation-docker)：官方提供 Compose 和手动容器方案；Compose 可能包含 Valkey 等附属组件，Demo 要实测资源占用。
- [settings.yml](https://docs.searxng.org/admin/settings/settings.html)、[search 配置](https://docs.searxng.org/admin/settings/settings_search.html)、[server 配置](https://docs.searxng.org/admin/settings/settings_server.html)、[outgoing 配置](https://docs.searxng.org/admin/settings/settings_outgoing.html)。

**实现要点**：
- JSON 不一定默认开启：配置 `search.formats: [html, json]`；未授权格式会得到 **HTTP 403**，这不是搜索关键词的失败。
- 外部搜索源的禁用、429、CAPTCHA、超时会影响结果数量和延迟；要分别记录 HTTP/JSON 正常、有效结果数和上游错误。
- Demo 不修改 SearXNG 引擎代码，仅配置并访问它的 HTTP API；**SearXNG 启动成功 ≠ 真正搜到东西**。
- 偏向本机绑定，不要求公网暴露。

**源码核查目标**（后续 clone 后按 pinned SHA 复核）：`searx/engines/` 引擎实现，`searx/search/` 处理器与结果归并，`searx/webapp.py` HTTP 层；另已阅读官方 [JSON engine 源码页](https://docs.searxng.org/_modules/searx/engines/json_engine.html)。

### 2. HTTPX — 单一网页获取层

**定位**：同步/异步 HTTP 客户端、连接池、重定向、超时、流式传输，不负责识别网页正文。

**资料**：[Async Support](https://www.python-httpx.org/async/)、[Timeouts](https://www.python-httpx.org/advanced/timeouts/)、[Resource Limits](https://www.python-httpx.org/advanced/resource-limits/)、[Quickstart](https://www.python-httpx.org/quickstart/)，源码 [`httpx/_client.py`](https://github.com/encode/httpx/blob/master/httpx/_client.py)、[`httpx/_config.py`](https://github.com/encode/httpx/blob/master/httpx/_config.py)。

**实现要点**：
- 共用 `httpx.AsyncClient`；不要每打开一个 URL 就重新建立 Client，避免丧失连接池收益。
- 区分 connect/read/write/pool 超时；网络超时和外部错误按结构化状态返回。
- 若读取 HTML，保留原 URL、最终 URL、状态码、Content-Type、长度、耗时和原始 HTML；首轮限制大小防止测试误读大资源。
- **同一 URL 仅下载一次**；后续各解析器使用相同 HTML/编码结果进行对比。
- HTTPX 默认重定向行为必须在实现中显式设定；首轮推荐 `follow_redirects=True` 并记录历史。

### 3. Trafilatura — 主体文本及元数据抽取

**资料**：[Python API 使用](https://trafilatura.readthedocs.io/en/latest/usage-python.html)、[提取管线](https://trafilatura.readthedocs.io/en/stable/extraction-overview.html)，源码 [`trafilatura/core.py`](https://github.com/adbar/trafilatura/blob/master/trafilatura/core.py)。

**实现要点**：
- `extract(html, output_format="markdown", url=...)` 可输出正文；`bare_extraction` 返回结构化 Document；对元数据和正文独立记录。
- 官方文档说明 Trafilatura 在默认完整模式中可能使用 **readability + jusText** 等内部回退、baseline rescue 和 recall escalation。它和我们单独执行 `readability-lxml` 的结果**相关而不独立**，不能把两个成功视为完全独立成功证据。
- `fast=True` 会跳过部分内部回退；**对比测试固定配置**，必要时单列 fast 与 normal 实验，避免不公平。
- `html2txt` 属于低精度的全量文本兜底，不等于正确识别文章正文。禁止仅靠字符数定义成功。

### 4. readability-lxml — 文章正文识别

**资料**：[README/调用示例](https://github.com/buriy/python-readability/blob/master/README.md)、源码 [`readability/readability.py`](https://github.com/buriy/python-readability/blob/master/readability/readability.py)。

**实现要点**：
- `from readability import Document`；`Document(html).title()` 与 `summary()`。
- **`summary()` 返回 HTML 片段或完整 HTML，不是纯文本/Markdown**；应保存原输出和经过统一 DOM-to-text 后处理的文本。
- 源码说明 Document 不是 re-entrant，`summary()` 修改内部 DOM；每份输入创建新 Document；按需先读 title，再调用 summary。
- 独立与 Trafilatura 对比仍有意义，但算法家族重叠应在报告中注明。

### 5. Selectolax — DOM 与结构化补救

**资料**：[官方示例](https://selectolax.readthedocs.io/en/latest/examples.html)、[Lexbor API](https://selectolax.readthedocs.io/en/latest/lexbor.html)、[README](https://github.com/rushter/selectolax/blob/master/README.md)、[CHANGES](https://github.com/rushter/selectolax/blob/master/CHANGES.md)。

**实现要点**：
- 使用 `from selectolax.lexbor import LexborHTMLParser`，`css_first`、`css`、节点 `text()`、`decompose()`。
- 它主要提供高性能 HTML5 DOM 解析与 CSS 选择，并**不自带通用文章主内容选择算法**；需明确自定义优先级，例如 `article` → `main` → `[role=main]` → 其他候选。
- 最新变更文档有 Modest 后端移除的破坏性改动，**不能依赖 `selectolax.parser.HTMLParser` 的旧示例**；必须按 pinned 版本确认。
- 不执行 JavaScript；嵌入 JSON（如 JSON-LD）可作为观察项，但首轮不要求通用地恢复 SPA 动态内容。

### 6. openai-python — 模型及工具调用

**资料**：[官方 SDK README](https://github.com/openai/openai-python)、[官方 Function Calling 指南](https://developers.openai.com/api/docs/guides/function-calling)、[SDK 客户端源码](https://github.com/openai/openai-python/blob/main/src/openai/_client.py)。

**实现要点**：
- 官方 SDK 支持配置 `api_key`、`base_url`、`model`；**配置了兼容地址不代表该服务支持工具调用**。
- 明确 `search_web(query, limit?)` / `read_webpage(url)` 两个本地函数，使用 JSON Schema 定义；后端执行并把**真实结果**回传给模型；模型自带 Web Search 不能代替这两个函数。
- 需要支持多轮和一个模型回复多个 tool calls 的情形，并逐个对应 `tool_call_id`（Chat Completions 路径）或响应项关联标识（Responses 路径）。
- **模型/API 兼容性新发现**：官方文档注明部分新模型（如 GPT-6 Astra / GPT-6.1 Sol）工具调用要求 Responses API。不能承诺「Chat Completions 足以覆盖所有 OpenAI 兼容模型」。首轮模型配置必须声明 API 模式；若选用仅支持 Responses 的模型则该模式必须可用，或明确标记此模型未通过兼容性门槛。
- SDK 最近文档涉及 HTTPX2 默认传输，不能假定其内部依赖版本始终与我们直用的 HTTPX 相同；B00 要锁定包版本并做安装检查。

### 7. Demo 界面与测试工具（辅助）

- [FastAPI 静态文件](https://fastapi.tiangolo.com/tutorial/static-files/)：后端提供 API，原生 HTML/JS 前端读取同一结果模型，无需 Node/React。
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)：`TestClient` 可以对 HTTP 接口写 pytest，不必每次启动真实监听端口。
- [pytest tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)：固定 HTML 样本 + 临时文件可做完全离线回归。

## 三、最终设计约束（已纳入执行计划）

1. 网络层 / 解析层 / UI 层 / Agent 层必须分开；**CLI 与 WebUI 调用同一 Core**。
2. 使用同一原始 HTML、相同预处理和统一的结果 Schema 对比三个解析器；既保存原输出，也保存用于比较的规范化文本。
3. 将“HTTP 请求成功”、“正文提取非空”、“正文提取质量合格”视为三个不同判断。
4. 独立搜索、独立读 URL、AI Agent 三条路径都应可直接使用；Agent 调用日志必须能追溯到实际执行的本地函数。
5. 负例不一定要成功提取：能**识别无法读取并报告原因**即为正确行为。
6. 本期不引入 Chrome/Chromium/Playwright；不额外开发 PDF 读取。
7. 具体工具裁剪、算法质量阈值与跨端产品化留到实验结束后评估。
8. 不在本 Demo 中重写 SearXNG 或上游库代码；只适配其对外 API。

## 四、待本地补齐的准备资料

建议放在仓库外的 `.references/upstream/`，并设为 Git 忽略；不要把六份上游仓库内容混入本项目提交。正式 B00 逐一 clone：

```bash
mkdir -p .references/upstream
git clone https://github.com/searxng/searxng.git .references/upstream/searxng
git clone https://github.com/encode/httpx.git .references/upstream/httpx
git clone https://github.com/adbar/trafilatura.git .references/upstream/trafilatura
git clone --recursive https://github.com/rushter/selectolax.git .references/upstream/selectolax
git clone https://github.com/buriy/python-readability.git .references/upstream/python-readability
git clone https://github.com/openai/openai-python.git .references/upstream/openai-python
```

完成后记录各仓库 `git rev-parse HEAD`、许可证和实际安装包版本；只引用源码，不直接把 upstream 源码当我们的模块。依赖以锁定版本安装，尤其检查 Selectolax、OpenAI SDK 的版本/API 变化。

## 五、已知限制与需要观察的研究问题

- SearXNG 是本地**服务**，不等于轻量嵌入式 Python 库；Docker/附属服务的真实资源消耗要在测试报告中记录。
- 网页抽取的“成功”可能只是首页推荐/导航，三解析器重复采用同一算法家族也无法消除这一问题。
- SPA、登录墙、验证码等失败不构成本期必须突破的目标。
- SearXNG 为 AGPL 系列授权，其他上游许可分别核查；本轮只是本地验证，后续如打包、分发或深度改造，另做许可评估。本文件不提供法律结论。
- 未进行任何真实本机运行测试、无基准测试数据；所有具体性能数字须待实际测得。

下一步参见 [分批执行与验收计划](./DEMO_EXECUTION_PLAN.md)。
