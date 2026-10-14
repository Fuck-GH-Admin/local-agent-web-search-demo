# B06 — OpenAI SDK 工具循环（离线优先）

**当前阶段：B06 在开发分支，离线测试结果以 GitHub Actions 为准。真实模型 G4 仍属于 B07。**

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
3. **真实模式下所有模型控制的 `read_webpage` 一律返回 `URL_POLICY_NOT_READY`，不会执行联网读取**。

这是有意的 fail-closed 限制。理由：公网域名可能被 DNS 重绑定到内网，自动跳转也可能进入 `localhost`、`169.254.169.254`、私网与内部服务；单纯验证原始 URL 字符串不够。

`OPEN_VALIDATION_INDEX.md` 中 **`B06-URL-SEC-01` 仍未通过且阻断 B07 的真实读取**。在解除限制之前，需至少完成：DNS 解析的 IPv4/IPv6 非公网拒绝、重解析/连接目标一致性、各跳转目标逐跳验证、重定向上限、内网地址/IPv4 异形表示/DNS rebinding/用户信息/端口规避用例。此处没有声称这些检查已实现或通过。

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
