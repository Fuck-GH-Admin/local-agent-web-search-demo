# B07 — 真实模型 Agent 闭环

**当前状态：DeepSeek 实机技术检查 LIVE_PASS；G4 PASS（2026-10-14 用户签认）；B07 普通入口实机技术验收已完成，新增接口用户审核已随G5签认。** 2026-10-14 在已验收 B06 的 main `856ca50` 之上继续验证云端 `feat/b07-real-model` 草稿。实际实现提交 `d087d07c4de8cd19ad5fc4250779ecbfc15801a3`。

## 实际证据

- 官方 `https://api.deepseek.com/models` 鉴权 HTTP 200，返回 `deepseek-flash`、`deepseek-v4-pro`。实际付费调用只使用 `deepseek-flash`、Chat Completions、`thinking=disabled`。
- auto 控制题：1 个模型回合，正确回答，0 次工具调用。
- required 通路：首轮强制调用本地搜索，之后恢复 auto，2 个回合正常回答；此场景不作为自主选择证据。
- 3 次 auto 联网轨迹均完成模型选择搜索、本地 SearXNG、本地安全下载/三解析器、最终引用回答。最终提交复验为 3 个模型回合、1 次搜索、2 次读取、1 条已核引用，7,269.597 ms；两次下载 HTTP 200，六个 parser 结果 PASS，逐跳安全审计均 ALLOWED/固定 IP。
- Codex 已逐项阅读五份轨迹，对照回答与实际正文，相关论断有来源支持。原机器复核 READY_FOR_HUMAN_REVIEW；用户现已明确签认，正式 G4 PASS。
- 全部 12 次真实 Chat Completions 请求：17,408 prompt tokens、1,133 completion tokens。无自动重试，CI 不接入密钥或付费模型。
- 本机 314/314；源码 [CI #38545299093](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38545299093) 实际 314/314、20 步 SUCCESS；B04 3/3、B05 5/5、B06 4/4 与安全工件通过。

公开证据：[实机复核摘要](../reports/B07/validation/review.md)、[脱敏完整指标与 SHA-256](../reports/B07/validation/acceptance.json)、[实际 CI 日志/工件核验](../reports/B07/validation/ci-source.json)、[详细验收说明](./B07_LIVE_VALIDATION.md)。原始 JSON、模型回答、读取正文和 source URL 留在本机 Git 忽略目录。

## 运行与保护

API Key 只从 `OPENAI_API_KEY` 环境变量读取，不写报告、源码、GitHub 或持久配置。模型端点使用标准 `openai.AsyncOpenAI` 的 Chat Completions `tools`，无服务商内建搜索、浏览器或隐式协议回退。

`search_web` 复用本地 SearXNG；`read_webpage` 复用 B04 单次下载/三个解析器，并使用 B06 公网 DNS 校验、固定 IP、原域名 TLS 与逐跳校验。真实读取默认关闭。显式 `--allow-live-read` 还要求索引 B06-URL-SEC-01 PASS 和本机两站 HTTPS smoke PASS。

```bash
uv sync --locked --all-extras
# 在私有终端配置 OPENAI_API_KEY；不要把实际值写入命令历史或 Git。
export OPENAI_BASE_URL=https://api.deepseek.com
export OPENAI_MODEL=deepseek-flash

uv run --locked python scripts/b07-agent-live.py \
  --question "3+4 等于几？" --tool-choice auto --thinking disabled \
  --max-tokens 256 --output reports/B07/no-tool-control.json

uv run --locked python scripts/b07-agent-live.py \
  --question "搜索 Python asyncio 官方文档，读取网页，并根据正文引用确切链接回答。" \
  --tool-choice auto --thinking disabled --allow-live-read \
  --output reports/B07/agent-live.json

uv run --locked python scripts/b07-g4-review.py \
  --input reports/B07/agent-live.json --output reports/B07/g4-local-review.md
```

DeepSeek 当前默认启用思考模式；通过 `extra_body.thinking` 显式关闭。思考模式的工具后续消息需保留 `reasoning_content`，已实现 SDK 离线验证；**没有实际运行思考模式**。`required` 与显式思考模式组合在启动前拒绝。依据：[官方思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)、[官方 Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)。

默认预算为最多 6 个模型回合、8 个工具调用、70 秒、每个模型响应 1,024 tokens；可显式调整。非正常 finish_reason 不包装成完整回答。日志记录响应 ID、usage、模式和耗时，错误只记录类型/状态码。原始报告权限 0600；`reports/B07/*.json` 与 `raw/` 已 Git 忽略。

## G4 签认与待办

机器初筛不能替代内容复核。**人工检查回答内容是否由引用支撑后才能签收。** Codex 内容复核完成后，用户明确回复“签认。”；记录时间 2026-10-14T18:10:35.077751+08:00，正式 G4 PASS。签认文件 [g4-signoff.json](../reports/B07/validation/g4-signoff.json) 绑定此前已交付的 `761b868bdeb43ee6a02f68fbd9c81d377709d10b`、五个公开原 Git blob 及五份原始轨迹 SHA。原始模型调用与 `acceptance.json` 编制时的待签认状态保留；当前正式状态以签认文件为准，没有重新生成模型结果。用户可查看本机 `reports/B07/raw/content-review.md`。

普通 `python -m local_search_demo agent`、`POST /api/agent` 与 WebUI Agent 页签已激活并完成技术实测：同一Core、真实CLI/UI闭环、340项回归与CI、9项真实浏览器检查及5张脱敏截图。详见 [入口验收](B07_INTERFACES_ACCEPTANCE.md) 和 [实机报告](../reports/B07/interfaces/validation/review.md)。原G4用户签认不变，新增接口用户审核已随本轮G5签认，见 [G5签认记录](../reports/B08/validation/g5-signoff.json)。

限制：Brave 限流但其他 SearXNG 结果可用；每页给模型的正文上限 6,000 字符，最终较长页面被截断，回答论断由完整短概览支持；未实测其他模型、Responses、模型服务 401/429/超时或空正文故障。离线负例与真实模型证据分开。本轮B08已复测，记录当前采样和站点失败例外，见 [最终报告](DEMO_TEST_REPORT.md)。

所有状态回填 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md)，历史签认和 B06 安全证据保留。
