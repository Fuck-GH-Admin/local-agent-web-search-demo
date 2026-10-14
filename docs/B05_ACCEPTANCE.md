# B05 — FastAPI + 原生 WebUI 与 G3 双入口验收

**阶段状态：自动化自检 PASS（133/133 + 5/5 CLI/API 回环对照 + JS 与 wheel 检查）；G3 本机 WebUI 人工验收 NOT_RUN。**

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

没有引入 React、Node.js、Playwright 或浏览器抓取。WebUI 浏览器仅用于**本地界面的展示**。

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

## G3：真实本机操作必须补做

自动接口测试**不能证明浏览器展示、布局或交互真实可用**。请在 Ubuntu 本机执行以下检查（[可填写的 G3 本机检查模板](../reports/B05/g3-local-review.template.md)），尤其使用 B01 已验证的真实 SearXNG：

- 使用浏览器打开本机 `http://127.0.0.1:8765`，切换三页签，页面无 JS 报错；桌面与窄视口能正常阅读。
- 搜索真实关键词（建议 `python asyncio` 与 `无人机 电磁干扰`），确认结果列表和来源引擎实际出现；对于上游空结果/超时，错误信息也可见。
- 在解析页读取普通文章及技术文档网址，确认 requested/final URL、下载耗时、三解析器输出、候选选择和理由都能显示；比较 CLI 相同 URL 的核心结果（动态网页可能变化，记录访问时刻）。
- SPA 空壳或其他无正文样本，界面不应编造正文；请求失败时 UI 必须可见且可再次提交。
- 截取页面交互结果的**真实浏览器截图**，存入 `reports/B05/screenshots/`（避免含隐私和敏感 URL），记录真实本机系统版本、服务运行命令、浏览器控制台错误、实测时间和结论到 `reports/B05/g3-local-review.md`。
- 由用户审核后将状态写为 `G3 PASS`，更新 `OPEN_VALIDATION_INDEX.md`、台账、验收文件；如暂未执行保持 `NOT_RUN`，不要用 CI 截图/虚构图片充数。

## B05 完成判定

代码和自动化自检可先达到 `SELF_CHECK_PASS`；**G3 只有本机真实 WebUI 人工验证通过后才能 PASS**。如果只跑 CI，应保留 Draft PR，不提前合并进 `main`。

跨阶段遗留继续保留：`B03-LIVE-02`、`B04-LIVE-01`、未来 `B06-URL-SEC-01`。详见 [跨批次索引](./OPEN_VALIDATION_INDEX.md)。
