# B06 完整核对与 B07 交接

**2026-10-14：B06 本机与 CI 完整验收 PASS，可以进入 B07；本次实际模型调用为 0，停止在 B07 之前。** CI、源码提交与最终远端同步状态以附带证据和实际分支为准。

## 核对结果

| 项目 | 结果 | 证据 |
|---|---|---|
| B00–B05 已接受基线 | PASS | 原报告保留；G2/G3 签认 Git blob 绑定和全部 16 张截图 SHA 再核验 |
| B03 真实网站质量专项 | PASS | 六网站/18 行原记录完整，本机输入和输出哈希 6/6 匹配；未重写标签或声称重新用户签认 |
| B06 整合基线 | PASS | 正常 merge 纳入上游 B06 `688c5ae` 与已验安全分支 `adea99b`，没有丢弃任一分支历史 |
| 模型读取默认开关 | PASS | 默认 `enable_live_reads=False`，只有受信操作者显式启用；保持兼容既有 B07 草稿接口 |
| URL 策略 | PASS | 两个传输 API 共用 PublicURLTransport，全部 DNS 校验、IP 固定、原域名 TLS、逐跳校验、端口/特殊地址拒绝和代理隔离 |
| 真实 HTTPS 前置 | PASS | `reports/B06/safe-http-live.json`，example.org 与 Python 文档均 200；真实 DNS/TLS，无环境代理 |
| 安全实机检查 | PASS | 11/11，包括真实 SearXNG→受保护读取；真实本地 sentinel 收到 0 个请求 |
| B06 SDK 适配与循环 | PASS | 实际 openai SDK + HTTPX MockTransport：序列化、关联 ID、search→read→answer、401/429/503、空 choices；没有实际模型请求 |
| 全量回归与打包 | PASS | 298/298；B06 四轨迹、B04 3/3、B05 5/5、依赖锁、JS 与 wheel 均通过 |
| 既有 B07 草稿前置条件 | PASS | 只导入并调用无网络 gate 函数，确认当前索引/HTTPS 报告和构造函数匹配；没有执行 launcher/run_live |
| 真实模型配置 | 留给 B07 配置 | 当前 OPENAI_BASE_URL / OPENAI_MODEL / OPENAI_API_KEY 未设置；只记录有无，未打印或保存值 |
| B07/G4 与 B08/G5 | NOT_RUN | 用户要求本次验证完成后停下；本次不构成真实模型能力或最终 Demo 验收 |

## 修复的实际缺口

- 原循环把 None、空字符串和纯空白回答标成 DONE；现在返回 NO_ANSWER / EMPTY_MODEL_RESPONSE。
- 同一回合多工具达到数量/时间限制后，原循环提前 break，漏掉尚未处理的调用 ID；现在对剩余 ID 记录限额/超时错误，禁止更多执行和模型回合。
- 旧测试仅用 ScriptedModelProvider，未经过真实 SDK 的请求/响应适配；新增 13 个前置回归，其中 8 个检查实际 SDK 离线协议，5 个检查循环缺口。修复前实际 5 FAIL / 8 PASS 已保存，不删除失败证据。
- 上游 SafePublicTransport 与既有 PublicURLTransport 原本是两份地址策略；现保留两个导入 API，使用同一底层策略，消除特殊地址过滤和 TLS 虚拟主机复用差异。

SDK 工具结果消息对照 [OpenAI 官方 Function calling 文档](https://developers.openai.com/api/docs/guides/function-calling) 的 Chat Completions 关联字段；实际结果由 SDK 离线测试核验。当前只实现 chat_completions；具体提供方兼容性及是否需要 Responses 属于 B07，未配置的模型不能推定兼容。

## 可复现前置验证

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked python scripts/b06-offline-tool-smoke.py
uv run --locked python scripts/b06-safe-http-live.py
uv run --locked python scripts/b06-url-security-smoke.py --live --output reports/B06/readiness-audit/live-new.json
uv run --locked python scripts/b03-g2-check.py
uv run --locked python scripts/b03-live-check.py
```

完整本次命令/环境、JUnit、失败前快照、签认绑定、前置接口核验和 CI 工件证据见 [`reports/B06/readiness-audit/`](../reports/B06/readiness-audit/)。早期 155/179/259 项报告属于各自历史提交，不能代替本次整合后的 298 项结果。

## 交接边界

代码与安全前置验证完成后，B06 可以结束并进入 B07。验收版本必须先以非强制方式同步 B06/main，最后核对远端 SHA 和该提交 CI；不得从未整合的旧分支继续。

下一次 B07 工作从已验证 main 更新现有 `feat/b07-real-model-prep` 草稿，注入实际模型配置，再按 B07/G4 做真实自动选择、无工具控制、搜索→读取→引用回答与失败分类。操作者显式启用 live read 时仍受完整 URL 策略约束。本次没有新的人类签认声明，也没有提前启用模型运行。

## 已核对的实际 CI

[Actions #38526842708](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38526842708)，实现提交 `4aa924158094e437327f6ce3c939ea20ad58cd70`；self-hosted ghrunner-local-agent-web-search-demo 的 19 步全部成功。实际下载日志确认 298 passed in 11.34s；工件 #11876107695 的 JUnit 共 298 项、0 失败/跳过，其中新增前置回归 13 项。安全 smoke 8/8，两次实机 loopback 请求 0；B04 3/3、B05 5/5、B06 4/4；新 B03 工作表仍未赋人工标签。最终证据提交后还需核对同提交 CI，确认后按用户要求停止。
