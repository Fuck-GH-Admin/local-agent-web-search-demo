# B07 — 真实模型 Agent 闭环（运行入口与验收）

**当前状态：B06 已核验合入 main，B07 实现/真实模型联调阶段；G4 REAL_MODEL_NOT_RUN。** 本分支从 B06 已验收的 `main` 创建。运行入口与保护测试不等于实际模型可用。

## 核心原则

- 真正使用 `openai.AsyncOpenAI` Chat Completions 的 `tools`/函数调用；不调用服务商内建联网、内建浏览器或者 Responses API 作为隐式替代。
- 工具仍复用 B06 `AgentRunner` 和 `AgentToolDispatcher`，因此 `search_web` 走本地 SearXNG、`read_webpage` 走 B04 三解析器。
- API Key 只从 `OPENAI_API_KEY` 环境变量读取，不写入报告。模型和 API 端点可由 `OPENAI_MODEL`、`OPENAI_BASE_URL` 提供。不要把真实 Key、私人浏览页面或含凭据的终端截图推送仓库。
- 默认 `--tool-choice auto`，用以验证模型是否主动选择工具；可用 `--tool-choice required` 单独确认函数调用通路。强制工具结果**不能**作为自主调用能力的证据。
- 未要求启动时脚本不调用模型；`--allow-live-read` 默认关闭。启用时必须同时满足 `docs/OPEN_VALIDATION_INDEX.md` 内 `B06-URL-SEC-01` 已明确标注 PASS，以及本机 `reports/B06/safe-http-live.json` 两个目标都 PASS。除此之外实际下载还有 SafePublicTransport 逐跳 DNS/IP 校验，不会退回普通 HTTPX。

## 前置工作

1. **已完成**：B06 实际 CI #38526842708、298/298、两站真实 HTTPS、11/11 安全检查全部 PASS，技术基线已经合入 `main`。参考 `docs/B06_READINESS_AUDIT.md`。
2. **既有证据**：Ubuntu 已执行 `scripts/b06-safe-http-live.py`，两站 PASS，结果 `reports/B06/safe-http-live.json`。如更换宿主机或网络，请重跑此步骤；若仅允许代理，则不能改为不安全的普通 HTTPX。
3. **已完成技术门槛**：`OPEN_VALIDATION_INDEX.md` 的 `B06-URL-SEC-01` 与 `B06-HTTPS-01` 均为 PASS。仍需要操作者在 B07 命令中显式加 `--allow-live-read`，否则真实读取保持关闭。
4. 从自己的终端/私有配置注入 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY`，不要将值写入 GitHub。

## 实际命令

```bash
git fetch origin
git switch feat/b07-real-model
uv sync --locked --all-extras

# 无须公网读取的真实模型控制题，测试是否按 auto 决策
uv run --locked python scripts/b07-agent-live.py \
  --question "3+4 等于几？" --tool-choice auto \
  --output reports/B07/no-tool-control.json

# 搜索题目；未使用 --allow-live-read 时只能搜索，不会执行真实网页读取
uv run --locked python scripts/b07-agent-live.py \
  --question "查找 Python asyncio 官方文档的链接" --tool-choice auto \
  --output reports/B07/search-only.json

# 仅在已验收安全基线和操作者显式 --allow-live-read 之后执行完整工具闭环
uv run --locked python scripts/b07-agent-live.py \
  --question "搜索 Python asyncio 官方文档，打开网页读取内容，并引用确切链接回答。" \
  --tool-choice auto --allow-live-read \
  --output reports/B07/agent-live.json
```

以上只是可供目标主机执行的命令，**本会话没有实际执行模型 API、也没有收到模型选择与工具调用的真实证据**。如果服务商只提供 Responses API，本脚本会显式拒绝并记录不兼容，不伪造支持。

**重要：** `reports/B07/*.json` 已列入 Git 忽略，防止模型真实回答、网页内容和提问随惯常的 `git add -A` 泄漏。人工查看原始轨迹后再编写脱敏的 G4 验收摘要，禁止直接强制添加原始 JSON。

### G4 脱敏机器复核（不能代替人工）

完成实际 auto 模式 search→read→answer 的本机调用之后，运行：

```bash
uv run --locked python scripts/b07-g4-review.py \
  --input reports/B07/agent-live.json \
  --output reports/B07/g4-local-review.md
```

检查真实模型标识、工具模式、search→read 顺序、实际读取正文、引用是否匹配读取来源。机器仅输出 `READY_FOR_HUMAN_REVIEW` 或 `NOT_READY`；人工检查 **回答内容是否由引用支撑** 后才能签收。此摘要不复制问题/网页正文/链接，但提交前仍应自行审阅。

## G4 必须核验

- 至少一次真实兼容模型通过 `search_web → read_webpage → answer`，读取到的确实是本地函数的实时结果；保存轮次、call_id、参数、下载成功、正文和每段耗时。
- 最终回答的引用 URL 应与本次成功读取 URL 匹配；非本次读取来源标成 `UNVERIFIED_CITATION`，不当作有效引用。
- 对 `auto` 的外网题与本来无需联网的控制题分别测试；`required` 强制测试只证明 SDK 工具链能够调用。
- 记录真实模型返回的 API 兼容/不兼容状态，超时、拒绝工具、上游不可用、页面抽取无正文等失败类别。
- 人工检查全部 Trace，签收前状态只能是 `G4 NOT_RUN/BLOCKED/FAIL`，不可由离线 ScriptedModelProvider 的 PASS 自动变更。

## 机器依赖与安全约束

现有 Python 与官方 openai SDK 依赖已经在锁文件，不需额外 GPU、Chrome 或 Node 来执行模型工具调用。用户模型可能在云端或本地；连接安全、额度、API Key 保密与实际支持的 `chat_completions` 模式需要在目标机器测。自托管 CI **绝不可**从 secrets 注入真实模型密钥做每次 commit 的自动付费测试。

本阶段新增 `tests/unit/test_b07_launch.py` 及 G4 脱敏初筛，只做启动前保护和证据结构校验，不对外联网，也不声称 G4 PASS。

所有未完成项回填 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md)，并在 [IMPLEMENTATION_LEDGER.md](./IMPLEMENTATION_LEDGER.md) 记录真实模型、真实执行时间、测试结果和签认。

## 与旧草稿的分支迁移

旧 `feat/b07-real-model-prep` 建立在未合并的早期 B06 上，与最终主分支分叉。正式 B07 在 `feat/b07-real-model` 从已验收 `main` 重新构建，仅择取并修订启动器、保护测试和本阶段文档，不采用旧分支中的旧 DNS/SSRF 实现。旧 Draft PR 只作历史参考。
