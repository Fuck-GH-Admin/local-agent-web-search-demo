# B07-INTERFACES-01 — 启用普通 CLI / API / WebUI Agent 入口

**状态：SELF_CHECK_PASS / LOCAL_UI_NOT_RUN（G4 原签认仍 PASS）。** G4 独立模型启动器的实机验收已获得用户签认；本子批只负责将已验证的 Agent Core 安全接到普通入口。离线接口测试、CI 和目标机浏览器检查必须单独记录，**不能直接继承 G4 PASS**。

## 数据流

- 普通 CLI：`python -m local_search_demo agent` → `agent/service.py` → `AgentRunner` → `AgentToolDispatcher` → 本地 SearXNG / B04 安全网页读取。
- FastAPI：`POST /api/agent` → 同一个 `execute_agent` 函数；测试可注入 `ScriptedModelProvider + httpx.MockTransport`，生产只从服务器进程的环境变量获取真实模型配置。
- WebUI：Agent 页签现在提供问题、`auto/required/none` 和单次公网读取选择。全部回答、引用、错误及调用轨迹使用 DOM `textContent`，不渲染上游 HTML。
- 每次执行创建新的 Dispatcher，搜索来源集合不会跨会话串用。调用预算：回合 1–10、超时至多 120 秒、单次模型响应至多 4096 tokens；沿用 Runner 最大工具 8 次及 URL 审核策略。

## 安全边界

1. API Key 仅从本地环境变量 `OPENAI_API_KEY` 获取，**不会从请求 JSON 接收任何 key**；没有模型配置时 API 返回 HTTP 503 `BLOCKED`，CLI 返回退出码 2。
2. API 继续使用 B05 的可信 Host 白名单、CSP/no-store。Agent 的浏览器跨源请求额外验证 `Origin`，拒绝通过恶意网页向本机接口发起付费调用。
3. Agent 真实网页读取默认关闭：CLI 必须显式 `--allow-live-read`；WebUI 必须在表单勾选且**服务器端**设置 `LOCAL_AGENT_ALLOW_LIVE_READ=1`；两条路径均须通过 B06 已签收的 `B06-URL-SEC-01`/HTTPS 证据检查。HTTPX 实际访问仍经 DNS 固定公网 IP、逐跳重定向和 TLS 验证。
4. 当前 FastAPI 是**无身份认证的 loopback Demo**，不允许监听 `0.0.0.0`；严禁把 HTTP API 代理公开到公网或其它机器。请用 `uvicorn ... --host 127.0.0.1`。
5. `required` 只强制第一轮工具调用，后续切回 auto；**不能用 required 结果作为模型自主判断的证据**。普通 CLI/API WebUI 的新增入口不自动发起真实模型调用，用户操作才会运行。

## 离线回归

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked pytest -q tests/integration/test_agent_interfaces.py
node --check src/local_search_demo/web/static/app.js
```

用固定 HTML、SearXNG MockTransport 和 ScriptedModelProvider 核对：真实共享 Core 的 search→read→answer、调用 ID、模型缺失/预算非法错误、跨域付费调用拒绝、WebUI 原生文本渲染和安全开关。CI 结果及失败须回填本文件。

## 本机真实入口检查（尚未签收）

在你的 Ubuntu 上导出模型配置（不要将 Key 复制到聊天或 GitHub），确认本地 SearXNG 仍运行：

```bash
git fetch origin
git switch feat/b07-agent-interfaces
uv sync --locked --all-extras

uv run --locked python -m local_search_demo agent \
  "搜索 Python asyncio 官方文档并引用来源回答" \
  --tool-choice auto --thinking disabled --allow-live-read \
  --json --output reports/B07/interface-cli-live.json

# 新终端启动本地 WebUI；服务器明确允许你在表单上选择一次真实网页读取
LOCAL_AGENT_ALLOW_LIVE_READ=1 uv run --locked uvicorn \
  local_search_demo.web.api:app --host 127.0.0.1 --port 8765
```

浏览器访问 `http://127.0.0.1:8765/`，切换 Agent 页签；先试一次无工具控制题（不勾选公网读取），再用同类型 asyncio 官方文档题（勾选公网读取）。复核：
- [ ] 普通 CLI `agent` 不再 NOT_IMPLEMENTED；模型无配置时明确 BLOCKED；真实运行记录 status、工具 ID、已核 URL。
- [ ] WebUI 真正显示模型回答、搜索/读取轨迹和引用；网页无 JS 控制台错误，窄视口可操作。
- [ ] URL 安全入口仍只允许本次搜索来源、HTTPS TLS，私网读取明确拒绝。
- [ ] API 没有 API Key 字段、跨源 POST 拒绝、无 server 环境开关时读取 403、模型错误不泄露凭据。
- [ ] CLI/API 与已有 B07 独立启动器的**业务**契约一致（不同时间模型生成结果不要求逐字相同）。
- [ ] 真实截图与输出需先脱敏，再写 `reports/B07/interfaces/...`；原始模型答案、含访问地址的正文保留本机忽略目录。

实机签认后更新 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md) 的 `B07-INTERFACES-01`、实施台账和本文件。不满足条件不得标成 PASS 或把 Demo 对外发布。

## 原有验收保持不变

`B07-G4-01` 已由原实机运行及人工复核签认；本子批不会重新编造 G4。B08/G5 整体验收仍未开始。真实 G4 结果见 [B07_LIVE_VALIDATION.md](./B07_LIVE_VALIDATION.md)。

## CI 自动化证据（已核验）

- [Actions #38551213517](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38551213517)：全量 `323 passed in 10.53s`、B07 启动检查 7/7、普通接口 9/9，B04 3/3、B05 5/5、B06 4/4 均 PASS；`scripts/b07-interfaces-smoke.py` 的真实 SDK loopback 模拟模型服务回环成功。
- SDK 回环测试实际运行普通 CLI 和 FastAPI Agent，生成四次固定模型响应，两次本地搜索；无真实模型 API、无付费、无凭据写入报告。
- 曾有 [失败 CI #38550515144](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38550515144)：323 项 pytest 通过，但旧 B05 parity 仍要求 HTTP 501。修复为只校验路由存在且不意外发起模型调用后恢复成功；失败历史保留。
- 固定证据 `reports/B07/interfaces/ci-acceptance.json`。这些证明技术入口已接入，**不替代浏览器/本机真实模型接口人工验收**。
