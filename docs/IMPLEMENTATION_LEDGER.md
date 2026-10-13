# 实施与验收台账

执行依据：`DEMO_EXECUTION_PLAN.md`；起点 `e90892ed9d278978fff3a583f96ec271d9c45ea5`。
B00 工作分支：`b00/environment-baseline`；B00 内容已快进到 `main`。当前 B01 工作分支：`feat/b01-searxng-search`。

| 批次 | 状态 | 证据与说明 |
| --- | --- | --- |
| B00 | PASS | 本机技术验收与独立重建通过；用户人工阶段签认 NOT_RUN |
| B01 | IN_PROGRESS / G1 NOT_RUN | 51/51 GitHub CI 离线通过（含 CLI→回环 HTTP 集成）；本机 Docker 搜索尚未验收 |
| B02 | NOT_RUN | 未执行 |
| B03 | NOT_RUN | 未执行 |
| B04 | NOT_RUN | 未执行 |
| B05 | NOT_RUN | 未执行 |
| B06 | NOT_RUN | 未执行 |
| B07 | NOT_RUN | 未执行 |
| B08 | NOT_RUN | 未执行 |

## B00 执行记录

- 2026-10-13：阅读 README、需求、预研、执行计划；从 main 建分支。
- 先建立忽略规则，真实凭据和上游 checkout 不纳入提交。
- 计划没有修改；基础入口和样本准备不代表搜索/解析/Agent 功能通过。
- 批次初始化均为 TODO；B00 完成后转 PASS，后续统一记录 NOT_RUN。
- 六份上游 clone 均成功，Selectolax 的 Lexbor 子模块已初始化；完整 SHA 与许可证文件哈希存于 `upstream-lock.json`。
- 建立 pyproject、uv 锁及带下载哈希的 requirements 锁；CPython 3.12.13/Linux x86_64。
- 完成六个主模型与辅助模型、六类 HTML 和五类搜索 JSON，正文质量评价仍未执行。
- 首轮 32 项测试 PASS；第二个独立虚拟环境按哈希锁重建，32 项测试 PASS，包表、Python 版本、依赖锁哈希均相等。
- G0 的本机技术条件 PASS；人工阶段签认 NOT_RUN。没有豁免、没有技术阻断，本轮不进入 B01。
- GitHub 交付：用户随后授权将代码和验收证据推送到 `origin/b00/environment-baseline`；README 已补充远端分支重建命令。

### 本批交付五件

1. 变更：环境/依赖、上游版本锁、共享模型、固定样本、CLI 骨架、环境检查与重建脚本、32 项离线测试。实现提交：`eb8c626c582ec515aa0cb96060d77f33aa4e6a5c`；证据与本条台账更新在后续本地证据提交中保存（最终 SHA 可由 `git log -1` 获取）。
2. 命令与结果：`uv sync --locked --all-extras`、`.venv/bin/python scripts/verify_b00.py`、`bash scripts/rebuild_environment.sh .venv-rebuild` 全部 PASS；详见 README。
3. 自动化证据：`reports/B00/environment.json`、`test-summary.txt`、`pytest.xml`、`checks.json`、`upstream-clones.json`、`rebuild-summary.txt`、`rebuild-check.json`、`rebuild-environment.json`、`rebuild-verification.txt`、`hygiene.json`、`acceptance.json`。实现提交后再次核验两个环境，测试均为 32 PASS。
4. 人工任务：复核 `B00_ACCEPTANCE.md` 和报告，再决定后续 G0 阶段签认；无 B00 技术问题阻断。其余批次和实机业务测试均未执行。
5. 台账与结论：本文件及 `B00_ACCEPTANCE.md`；B00 本机技术通过，后续保持 NOT_RUN。

## 变更记录

没有修改验收标准或删除主字段。增加 ErrorDetail/SearchItem/ToolCall 辅助模型及 encoding/html_path；计时统一为毫秒，未执行结果保持 null。
源码复核后选用实际可安装的 OpenAI SDK 3.29.0（HTTPX2 传输），同时保留 HTTPX 0.28.1 作为本项目获取层；这是版本选择，没有调整任务范围。

## B01 当前批次（2026-10-13）

- 基线：`main` 与 B00 的 `b00/environment-baseline` 均指向 `d63adc85b1cab34afe88715951ffcb76da31b693`；用非强制快进更新，无需合并已分叉的旧 `feat/b00-foundation`。
- 分支：`feat/b01-searxng-search`（本阶段仅在该分支写代码；`main` 不包含 B01 新实现）。
- 已提交：SearXNG Docker Compose / JSON 配置、HTTPX 搜索适配器、CLI 真实 search、MockTransport 离线用例及显式 live-smoke 脚本。
- 数据契约：在 `SearchResult` 增加可选 `http_status`，保留已有字段语义；`read/agent` 仍计划后续实施。
- 验收依据：[B01_ACCEPTANCE.md](./B01_ACCEPTANCE.md)，分 `离线测试` 与 `G1 本地真实搜索` 两道检查。
- **离线 CI 证据**：[`reports/B01/ci-offline.json`](../reports/B01/ci-offline.json)，关联 GitHub Actions 运行 #38420077726，`51 passed in 4.52s`；不代表联网成功。
- **当前证据状态**：SearXNG 在目标本机尚未启动，本批 G1 **NOT_RUN**；不得用静态配置、HTTPX Mock 或 GitHub CI 冒充 G1 通过。
- 待执行：本机 Docker Compose 启动 + 两个真实关键词 + `scripts/b01-live-smoke.py` + 镜像 digest、上游错误和耗时记录。通过后再将 G1 改为 PASS。
