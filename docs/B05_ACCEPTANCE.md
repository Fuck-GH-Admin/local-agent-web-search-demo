# B05 — FastAPI + 原生 WebUI 与 G3 双入口验收

**阶段状态：本机自动化 PASS（133/133 + 5/5 CLI/API 对照 + JS 与 wheel）；真实浏览器 17/17、16 张截图复核完成；正式 G3 最终用户审核 PENDING。**

本批按 `DEMO_EXECUTION_PLAN.md` 只做第二种交互入口：搜索、网页读取与解析器比较全部直接调用 B01–B04 Python Core，**不复制新的业务算法**。Agent 页签只显示规划中状态，`POST /api/agent` 返回 HTTP 501。

## 交付结构

| 文件 | 用途 |
|---|---|
| `src/local_search_demo/web/api.py` | FastAPI `GET /`、`GET /health`、`POST /api/search`、`POST /api/read`、`POST /api/agent` 和静态文件 |
| `src/local_search_demo/web/static/index.html` | 关键词搜索 / URL 解析 / Agent 三页签和可访问的表单 |
| `src/local_search_demo/web/static/app.js` | 原生 `fetch`、结果展示、错误显示，三个解析器并列显示 |
| `src/local_search_demo/web/static/app.css` | 响应式轻量暗色 WebUI，不依赖前端打包工具 |
| `tests/unit/test_web_api.py` | FastAPI TestClient 离线 API、错误、静态资源与安全展示回归 |
| `scripts/b05-api-parity.py` | CLI/API 经同一个本地 HTTP 站点执行，比较动态字段之外的相同 Core JSON，并留存报告 |

应用没有引入 React、前端打包或浏览器抓取依赖。WebUI 浏览器用于本地展示；本次验收另用主机已有的 Node/Playwright 驱动真实 Chrome，不改变应用的 Python 依赖锁或 HTTPX 网页获取方式。

## 本机启动与使用

在 `feat/b05-fastapi-webui` 分支，确保 Python 3.12.13 与既有锁文件的环境可用：

```bash
git fetch origin
git switch feat/b05-fastapi-webui
uv sync --locked --all-extras

# 若需要真实搜索，保留 B01 的 SearXNG 容器与既有网络代理配置
docker compose -f deploy/searxng/compose.yml ps

# 仅监听本机，勿用 --host 0.0.0.0 对外开放未鉴权开发服务
uv run --locked uvicorn local_search_demo.web.api:app --host 127.0.0.1 --port 8765
```

访问 <http://127.0.0.1:8765/>。三个页签依次为：

1. 搜索：输入关键词，展示 SearXNG 返回的标题、URL、摘要、引擎、排名和状态/错误；
2. 解析：输入 HTTP(S) URL，展示 requested/final URL、状态、编码、字节/耗时、自动候选选择、全部三个解析器的文本/原始输出与原因；
3. Agent：占位，不会构造虚假的模型回答，`POST /api/agent` 明确 HTTP 501。

可以使用 `SEARXNG_BASE_URL=http://127.0.0.1:8080` 更改搜索服务地址。SearXNG 的 Docker 代理与 Ubuntu 主机 HTTPX 使用的 `HTTP_PROXY/HTTPS_PROXY/NO_PROXY` 不是同一个环境，必须分别检验。

**安全边界**：开发 API 已加入 Host 白名单（127.0.0.1 / localhost / TestClient 测试专用 testserver）、CSP、no-store 和 nosniff 响应头；未启用跨源访问 CORS；网页正文及搜索内容只以 `textContent` 写入 DOM，不调用 `innerHTML` 执行第三方内容；服务只建议 loopback 监听。当前是本机未鉴权实验站，能提交任意 URL，因此**不要暴露公网/LAN**。未来 B06/07 模型自主读取 URL 前必须执行索引中的 `B06-URL-SEC-01` 安全检查。

## 已完成的真实 CI 自动化证据

- [GitHub Actions #38492812276](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38492812276)：Python 3.12.13，**133 passed in 8.33s**，0 failed；覆盖 WebUI 静态资源、FastAPI 路由、Host/CSP 安全约束以及 B00–B04 完整回归。
- `scripts/b05-api-parity.py` 在同一 CI 中 **PASS / 5 场景**：文章、SPA、404、搜索四组 CLI/API 核心字段严格一致，加 health、Agent 501 和主页。实际来源 HTTP 请求计数：文章 2、SPA 2、404 2、搜索 2（两个入口各一次）。
- JS 语法检查：`node --check` **PASS**（CI 内使用 Node，仅检查 JS，不增加应用前端运行依赖）。`uv build --wheel` **PASS**，检查 `index.html`、`app.css`、`app.js` 均随安装包打包。
- 已下载 GitHub artifact #11861829788 并读取原始 `B05/api-tests.json`：上述 5 项全部 `pass=true`，排除的只有运行标识与计时，不排除正文、解析器、候选选择、错误状态。
- 固化证据：[B05 自动验收摘要](../reports/B05/ci-offline.json) ｜ [API 对照完整 JSON](../reports/B05/api-tests.json)。
- **这些证据不能代替 G3 本机浏览器人工测试，也不能证明 SearXNG 在你当前网络上的真实搜索。**

## 自动化测试（G3 技术部分）

```bash
uv run --locked pytest -q
uv run --locked python scripts/b05-api-parity.py
```

`reports/B05/api-tests.json` 应记录：4 项 CLI/API 核心字段对比（文章、SPA、404、搜索），以及 health / Agent 501 / 静态主页；须有 `matching_core_fields=true` 和全部场景 PASS。比较时排除 `run_id`、时间戳和耗时（天然不相等），**不能排除正文、选择算法、错误、元数据**。只访问本地临时 HTTP 服务器，无真实联网；CI 会保存 JSON 工件。

`uv build --wheel` 额外检查 `index.html`、`app.js`、`app.css` 被包含于分发 wheel，避免打包遗漏。

## G3：真实本机操作清单（本次已执行，最终用户审核待办）

自动接口测试**不能证明浏览器展示、布局或交互真实可用**。请在 Ubuntu 本机执行以下检查（[可填写的 G3 本机检查模板](../reports/B05/g3-local-review.template.md)），尤其使用 B01 已验证的真实 SearXNG：

- 使用浏览器打开本机 `http://127.0.0.1:8765`，切换三页签，页面无 JS 报错；桌面与窄视口能正常阅读。
- 搜索真实关键词（建议 `python asyncio` 与 `无人机 电磁干扰`），确认结果列表和来源引擎实际出现；对于上游空结果/超时，错误信息也可见。
- 在解析页读取普通文章及技术文档网址，确认 requested/final URL、下载耗时、三解析器输出、候选选择和理由都能显示；比较 CLI 相同 URL 的核心结果（动态网页可能变化，记录访问时刻）。
- SPA 空壳或其他无正文样本，界面不应编造正文；请求失败时 UI 必须可见且可再次提交。
- 截取页面交互结果的**真实浏览器截图**，存入 `reports/B05/screenshots/`（避免含隐私和敏感 URL），记录真实本机系统版本、服务运行命令、浏览器控制台错误、实测时间和结论到 `reports/B05/g3-local-review.md`。
- 由用户审核后将状态写为 `G3 PASS`，更新 `OPEN_VALIDATION_INDEX.md`、台账、验收文件；如暂未执行保持 `NOT_RUN`，不要用 CI 截图/虚构图片充数。

## B05 完成判定

代码和自动化自检可先达到 `SELF_CHECK_PASS`；**G3 只有本机真实 WebUI 人工验证通过后才能 PASS**。如果只跑 CI，应保留 Draft PR，不提前合并进 `main`。

跨阶段索引保留：`B04-LIVE-01` 已用本次两个真实 CLI read 关闭；`B03-LIVE-02` 和未来 `B06-URL-SEC-01` 继续待办。详见 [跨批次索引](./OPEN_VALIDATION_INDEX.md)。

## 2026-10-14 目标主机 B05/G3 完整补验

基于最新 B05 分支 `4e5f56331f02dfd04864782f12198c9fd6c41f2c`，已经包含 main `3bec4da` 的已接受 B04。完整阅读当前 README、执行计划、索引、台账、B04/B05 验收和模板，检查 API/静态页面/测试与两个 Core 读取入口；不重复实现业务算法。

- Ubuntu 26.04.1 LTS / x86_64 / CPython 3.12.13 / uv 0.12.5。原有 133 项测试在本机实际全部通过（8.42s），0 失败/跳过，详见 pytest-summary.txt、pytest.xml、pytest-cases.json。
- 固定输入 CLI/API 实际 loopback 对照 5/5 PASS，正文/原始结果/决策/错误未被排除；当前 `api-tests.json` 为本机记录，原 CI 版本原样保存为 `ci-api-tests.json`。JS 语法、wheel 三静态文件检查通过。
- 本机真实 Google Chrome 153.0.8010.52，有界面模式、Xvfb 虚拟显示。独立 Playwright 1.62.1 只做 QA；浏览器仅打开本地 WebUI，实际文章和文档仍由 HTTPX 获取。内置浏览器首轮因缺显示服务失败，使用 Xvfb 后完成全部检查。
- 17 项浏览器检查 PASS，三页签/键盘、中英文真实搜索（各 5 条）、两页真实读取、三原始输出展开、SPA、404、断网/恢复、302、查询错误、Agent 501 与 390px 窄视口均实际执行。
- 16 张原始 Chrome PNG 已由 Codex 使用 view_image 逐张复核，中文字体、桌面三列和窄屏单列、正文、状态、错误与恢复均可读；文件 SHA-256 和尺寸保存在 browser-observations.json。
- 两页公网的 CLI/WebUI 核心字段严格相同；真实搜索两次请求间排序和上游错误提示变化如实保存，不伪造相等结论。固定输入 5/5 严格对照另有实际证据。
- 未捕获 JS 异常 0。控制台真实有 favicon 404、主动断网 ERR_INTERNET_DISCONNECTED、Agent 501 三条网络提示，未过滤或宣称 console 完全无错误。

完整逐项记录、源数据摘要与截图链接见 [`reports/B05/g3-local-review.md`](../reports/B05/g3-local-review.md)。原始网页/响应全文留在被忽略的 raw/；公开提交元数据、正文哈希、对照结论与非敏感真实截图。

当前 `B05-G3-01` 只剩“由用户审核后将状态写为 G3 PASS”的最终审核；`browser-observations.json` 的技术 PASS 不代替用户签认。正式 G3 保持 AWAITING_USER_REVIEW，不合入 main 或提前进入 B06。

### 本次新提交 CI 阻断（不冒充测试失败/通过）

G3 实机证据提交 `d059b8028a2661703cc27bbc62c1c8dbd4cc6f02` 已推送，但新的 Actions #38497254054 / #38497249637 都在分配 runner 前失败，steps 和日志为空。GitHub 的 failure annotation 明确提示账户付款失败或 spending limit 需调整。原始诊断见 `reports/B05/ci-startup-blocked.json`；新增索引 `B05-CI-01` 为 BLOCKED，待账户负责人解除限制后再复跑。没有调整付费或 workflow 设定，也没有声称当前提交 CI 通过；上面 133 项 CI 是原实现的历史成功记录，本次目标机 133 项回归另有实际证据。
