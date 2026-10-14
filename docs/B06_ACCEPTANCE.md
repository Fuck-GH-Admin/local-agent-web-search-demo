# B06 — OpenAI SDK 工具循环（离线优先）

**当前阶段：离线工具循环及 DNS pinning 安全单测已通过（179/179，另新增默认关闭测试待复验）；目标机真实 HTTPS 验收尚未执行。真实模型 G4 属于 B07。**

## 实现内容与边界

- `agent/toolspec.py`：仅定义 `search_web` 和 `read_webpage` 的 OpenAI Chat Completions 兼容 JSON Schema，拒绝额外字段。
- `agent/provider.py`：`ModelProvider` 协议、`ScriptedModelProvider` 固定输出、`OpenAIChatProvider` SDK 适配。当前仅实现 `api_mode=chat_completions`；`responses` 模式明确拒绝，不能静默回退到内建搜索。
- `agent/dispatcher.py`：解析工具参数并调用 B01 `search_web` / B04 `read_webpage`，真实接口不另写第二套搜索或提取逻辑。只允许读取**本次搜索获得的** HTTP(S) 公网样式 URL。
- `agent/runner.py`：模型回合、工具结果回填关联 ID、每回合耗时、最大回合/工具调用数与超时；所有错误以结构化 trace 记录，不无限调用。
- `scripts/b06-offline-tool-smoke.py`：四种预设轨迹，脚本化模型 + HTTPX MockTransport；Core 仍真的执行搜索归一化及 HTML 三解析器提取。

真实模型调用与真实公网搜索—读取—引用回答属于 B07 G4，**离线模拟不代表实机 Agent 成功**。B06 本轮不打开 WebUI Agent 页签、CLI `agent` 仍返回 NOT_IMPLEMENTED。

## 不能跳过的安全边界

目前 B04 `read_webpage(url)` 针对用户明确输入的网址，HTTPX 会自动跟随跳转，不能未经检查就暴露给模型。B06 的 Dispatcher：

1. 要求模型仅能读取该次 `search_web` 返回的 URL，拒绝 localhost、内网 IP、凭据内嵌 URL、非 HTTP(S) 和非常规端口。
2. 固定样本模式要求 `httpx.MockTransport`，与公网真正隔离；用于 CI 演练。
3. 已新增 `agent/safe_http.py`：使用专门的 HTTPX `SafePublicTransport`，先校验 URL 和所有 DNS A/AAAA 返回值，禁止非公网 IP，再将实际连接目标 URL 锁定为已审核的公网 IP，通过 `Host` 和 `sni_hostname` 保持原域名的 HTTPS 证书校验（HTTPX 官方扩展）；重定向由外层 HTTPX 逐跳重新进入该传输层，默认最多五次；严格关闭环境代理。
4. 真实模式的 `read_webpage` 与可访问本机 SearXNG 的搜索 HTTP 客户端完全分离。新增 `enable_live_reads=False` 默认关卡；**即使传输层存在，未经 G6 正式验收和主动显式启用，也只返回 `URL_POLICY_NOT_READY`**。公网 HTTPS 直连的目标机冒烟需单独检查。

原先的 deny-all 是有意的 fail-closed 限制；现已升级为连接目标 IP 固定与逐跳拒绝，但在测试验收前不能放松安全关卡。理由：公网域名可能被 DNS 重绑定到内网，自动跳转也可能进入 `localhost`、`169.254.169.254`、私网与内部服务；单纯验证原始 URL 字符串不够。

`OPEN_VALIDATION_INDEX.md` 中 **`B06-URL-SEC-01` 仍未通过且阻断 B07 的真实读取**。新增 `tests/unit/test_agent_safe_http.py` 覆盖：IPv4/IPv6 非公网拒绝、混合 DNS 结果拒绝、实际连接 IP 固定、SNI/Host 保留、逐跳重定向校验、重定向上限、DNS 重绑定、代理禁止、异形 URL 与 Agent live 分离路径。安全单测在 [Actions #38522909188](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38522909188) 已通过（179 tests），新增显式启用开关后需要最终 CI 复核；还需 Ubuntu 目标机直连 smoke，才能依照验收准则关闭 `B06-URL-SEC-01`。

## 真实公网 HTTPS 安全冒烟（目标机待补）

执行 `uv run --locked python scripts/b06-safe-http-live.py`，固定检查 `https://example.org/` 与 Python 官方文档，使用真实 DNS 和原生 TLS 证书验证，**禁止代理**。输出 `reports/B06/safe-http-live.json`，当前状态 `NOT_RUN`，在 Ubuntu 实机检验后才可更新。不能用 MockTransport 测试取代真实 DNS/TLS 环境确认；如果网络只允许代理，应标记 BLOCKED，不回退到不安全的普通 HTTPX。

## B06 自动化验收

```bash
uv sync --locked --all-extras
uv run --locked pytest -q tests/unit/test_agent_loop.py
uv run --locked pytest -q
uv run --locked python scripts/b06-offline-tool-smoke.py
```

期望 `reports/B06/tool-loop-tests.json` 记录四种模型轨迹及工具调用：零工具、搜索、搜索后读正文、多工具+错误 JSON。**必须看到本次实际 search/read 工具结果、call_id 和最后状态**。

补充单测检查：
- 参数格式/错误 JSON/未知工具/拒绝私网 URL；一项失败不阻止其它操作，call_id 与回复消息关联。
- 模型超时及调用数量上限，禁止无穷循环。
- 回答引用 URL 必须来自本次成功读取；不属于本轮读取的引用标为 unverified。
- 真实模式模型 URL 读取 fail-closed；未实现的 Responses API 模式不能被误标支持。

注意 MockTransport 自动化可以检验逻辑，但不检验真实搜索引擎、公网 URL 代理链路、模型是否主动选择调用；B07 仍需另做。

## 本机必要准备

B06 离线测试不需要提供真正 API 密钥，也不增加安装到项目 Python 环境之外的服务。若 B07 使用真实兼容模型，才需要在本机环境变量中配置 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`；**千万不要提交真实 Key 到 GitHub**。

如需要自托管 runner，CI 继续使用已有 `[self-hosted, linux, x64]` 配置和显式 Node.js 初始化。B06 的所有 mock 测试只读取固定 fixture。

## 交接与索引

自动化 PASS 后可以签收 B06 工具模拟部分，但 **`B06-URL-SEC-01` 是未关闭的安全阻断项，真实 Agent 前绝不能绕过**；`B03-LIVE-02` 的真实网站解析泛化也仍需另行评估。每次推进、发现缺口和测试证据都需更新 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md) 和 [IMPLEMENTATION_LEDGER.md](./IMPLEMENTATION_LEDGER.md)。

## 第一轮真实 CI 与加固后的状态

- [B06 第一轮 CI #38511422094](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38511422094)：`155 passed in 9.02s`，固定四场景 `PASS`，B04 三场景及 B05 五场景回归也通过，artifact #11869184533 已生成。
- 新增针对模型控制 URL 的真正公网 DNS 解析/安全 IP pinning、SNI、重定向与代理等测试；**新测试还未从最新提交取得最终 PASS**，不可混同于第一轮 155 项。
- 已核查官方文档采用的请求扩展：[HTTPX sni_hostname](https://www.python-httpx.org/advanced/extensions/)；不得删除证书校验或用关闭 TLS 验证绕过。

### 已发现并保留的第一轮加固失败

- CI #38522756363：`178 passed / 1 failed`，错在测试将 `http://0x7f000001/` 当成允许，而安全 URL 校验正确地拒绝了它；改正测试预期后 CI #38522909188 `179 passed in 8.94s`，所有安全用例通过。
- 之后额外加入更严格的 `enable_live_reads=False` 默认关闭开关和对应测试。最终测试数量和结果需以此后的 GitHub Actions 为准，不沿用此前数字冒充。
