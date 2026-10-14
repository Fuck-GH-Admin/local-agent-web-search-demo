# B07 — 真实模型 Agent 闭环（运行入口与验收）

**当前状态：PREPARED / REAL_MODEL_NOT_RUN / G4 NOT_RUN**。本分支建立在尚未合入 main 的 B06 基线上，是依赖 B06 的堆叠开发分支。不能把启动器存在视为真实模型可用。

## 核心原则

- 真正使用 `openai.AsyncOpenAI` Chat Completions 的 `tools`/函数调用；不调用服务商内建联网、内建浏览器或者 Responses API 作为隐式替代。
- 工具仍复用 B06 `AgentRunner` 和 `AgentToolDispatcher`，因此 `search_web` 走本地 SearXNG、`read_webpage` 走 B04 三解析器。
- API Key 只从 `OPENAI_API_KEY` 环境变量读取，不写入报告。模型和 API 端点可由 `OPENAI_MODEL`、`OPENAI_BASE_URL` 提供。不要把真实 Key、私人浏览页面或含凭据的终端截图推送仓库。
- 默认 `--tool-choice auto`，用以验证模型是否主动选择工具；可用 `--tool-choice required` 单独确认函数调用通路。强制工具结果**不能**作为自主调用能力的证据。
- 未要求启动时脚本不调用模型；`--allow-live-read` 默认关闭。启用时必须同时满足 `docs/OPEN_VALIDATION_INDEX.md` 内 `B06-URL-SEC-01` 已明确标注 PASS，以及本机 `reports/B06/safe-http-live.json` 两个目标都 PASS。除此之外实际下载还有 SafePublicTransport 逐跳 DNS/IP 校验，不会退回普通 HTTPX。

## 前置工作

1. 先核实 B06 最新 CI PASS，再安全合入 `main`。本 B07 分支要追随合入后的基线。
2. 在 Ubuntu 主机真实运行 `uv run --locked python scripts/b06-safe-http-live.py`。若当前网络必须走代理，脚本会标 BLOCKED，**不能因此取消公共 IP 固定、TLS 验证或改回对内网可访问的 HTTPX**。
3. 结合安全单测和实际 TLS 下载确认 `B06-URL-SEC-01` 满足标准后，由使用者在索引正式签收。签收前只能运行 Search-only Agent，不能测试完整 search→read。
4. 从自己的终端/私有配置注入 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY`，不要将值写入 GitHub。

## 实际命令

```bash
git fetch origin
git switch feat/b07-real-model-prep
uv sync --locked --all-extras

# 无须公网读取的真实模型控制题，测试是否按 auto 决策
uv run --locked python scripts/b07-agent-live.py \
  --question "3+4 等于几？" --tool-choice auto \
  --output reports/B07/no-tool-control.json

# 需要搜索的真实题目；仍然只能搜索，不会放开网页读取
uv run --locked python scripts/b07-agent-live.py \
  --question "查找 Python asyncio 官方文档的链接" --tool-choice auto \
  --output reports/B07/search-only.json

# 只有在 G6 安全关卡正式通过后，才可运行完整工具闭环
uv run --locked python scripts/b07-agent-live.py \
  --question "搜索 Python asyncio 官方文档，打开网页读取内容，并引用确切链接回答。" \
  --tool-choice auto --allow-live-read \
  --output reports/B07/agent-live.json
```

以上只是可供目标主机执行的命令，**本会话没有实际执行模型 API、也没有收到模型选择与工具调用的真实证据**。如果服务商只提供 Responses API，本脚本会显式拒绝并记录不兼容，不伪造支持。

## G4 必须核验

- 至少一次真实兼容模型通过 `search_web → read_webpage → answer`，读取到的确实是本地函数的实时结果；保存轮次、call_id、参数、下载成功、正文和每段耗时。
- 最终回答的引用 URL 应与本次成功读取 URL 匹配；非本次读取来源标成 `UNVERIFIED_CITATION`，不当作有效引用。
- 对 `auto` 的外网题与本来无需联网的控制题分别测试；`required` 强制测试只证明 SDK 工具链能够调用。
- 记录真实模型返回的 API 兼容/不兼容状态，超时、拒绝工具、上游不可用、页面抽取无正文等失败类别。
- 人工检查全部 Trace，签收前状态只能是 `G4 NOT_RUN/BLOCKED/FAIL`，不可由离线 ScriptedModelProvider 的 PASS 自动变更。

## 机器依赖与安全约束

现有 Python 与官方 openai SDK 依赖已经在锁文件，不需额外 GPU、Chrome 或 Node 来执行模型工具调用。用户模型可能在云端或本地；连接安全、额度、API Key 保密与实际支持的 `chat_completions` 模式需要在目标机器测。自托管 CI **绝不可**从 secrets 注入真实模型密钥做每次 commit 的自动付费测试。

本阶段新增 `tests/unit/test_b07_launch.py` 只做启动前保护验证，不对外联网，也不声称 G4 PASS。

所有未完成项回填 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md)，并在 [IMPLEMENTATION_LEDGER.md](./IMPLEMENTATION_LEDGER.md) 记录真实模型、真实执行时间、测试结果和签认。
