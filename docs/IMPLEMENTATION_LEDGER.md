# 实施与验收台账

执行依据：`DEMO_EXECUTION_PLAN.md`；起点 `e90892ed9d278978fff3a583f96ec271d9c45ea5`。
B00 工作分支：`b00/environment-baseline`；B00 内容已快进到 `main`。当前 B01 工作分支：`feat/b01-searxng-search`。

| 批次 | 状态 | 证据与说明 |
| --- | --- | --- |
| B00 | PASS | 本机技术验收与独立重建通过；用户已明确授权进入 B01 |
| B01 | PASS / G1 LIVE_PASS | 55/55 本机离线通过；真实中英文搜索均 HTTP 200 / 5 条；Docker 状态、固定镜像 digest、初始失败与上游错误均有证据 |
| B02 | IN_PROGRESS | B01 已快进 main；已提交 HTTPX 获取模块、本地集成测试与 B02 验收文档；测试证据待更新 |
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
- 上述 CI 完成时 G1 为 NOT_RUN；本次用户明确要求完整执行 B01，依据已有 G0 本机证据进入本批，无须重复请求阶段许可。
- **本次实测状态**：G1 LIVE_PASS。英文与中文 smoke 均 HTTP 200、各 5 条有效 URL；CLI 两条真实查询亦各 5 条，原始 curl JSON 返回 27 条。
- **网络处理**：默认 bridge 首轮两个请求均无结果，日志证明容器 DNS 失败；已保留 `search-smoke-before-proxy.json` 和 `compose-logs-before-proxy.txt`。宿主机使用现有 loopback 代理，通过可选 `compose.proxy.yml` 接入后实测通过；未修改宿主机代理设置。
- **镜像锁**：pull 后固定 `sha256:9b61996edcc679fb6665290f95fda15389a14eda6060e41a25c63ab2758f2436`；镜像 revision 与 B00 SearXNG 源码 SHA 一致。容器运行且仅监听 `127.0.0.1:8080`。
- **分类修正**：live-smoke 区分本地 429/5xx（SERVICE_ERROR）、无错误空结果（NO_RESULTS）、明确的上游失效（UPSTREAM_BLOCKED）；补充 4 项测试，本机完整回归为 55 PASS。
- **实际限制**：成功查询仍记录 Brave 限流/暂停和 Google CSE 超时；镜像其他启动与 DOI 警告保留在日志，不宣称全部引擎健康。
- **下一批**：B02–B08 NOT_RUN；用户人工 G1 阶段签认尚未发生。本轮任务只完成本机 B01 技术验收并推送云端。

### B01 本批交付五件

1. 变更：镜像 digest 锁、可选既有代理配置、验收失败分类修正及 4 项回归、运行证据采集脚本、文档与实际报告。基于 `6875414` 续作；实测实现提交为 `e254a6db55e5e85cc28effe3fd5d97b986c61234`；本批原始输出与机器验收汇总在后续证据提交保存。
2. 测试：`uv sync --locked --all-extras`、`uv pip check --python .venv/bin/python`、`pytest -q`、Compose 启动、原始 curl、两个真实 CLI 查询、live-smoke、deployment-evidence；本机全部通过。最初无代理 smoke 为 UPSTREAM_BLOCKED，修复环境后 G1 LIVE_PASS。
3. 输出：`reports/B01/test-summary.txt`、`pytest.xml`、`search-smoke.json`、`curl-search.json`、`cli-search-en.json`、`cli-search-zh.json`、`live-command-checks.json`、`image.json`、`deployment.json`、`compose-state.json`、`compose-ps.txt`、`compose-logs.txt`、`instance-config.json`、`environment.json`、`loopback-listener.txt`；失败历史单独保留。
4. 未解决：上游限流和部分超时有实测记录，不阻断“至少一次有效结果”的 G1 标准；其他环境仍需实际验证。待用户复核本批证据，后续批次未执行。
5. 台账：本节与 `docs/B01_ACCEPTANCE.md` 记录实际技术验收；机器汇总位于 `reports/B01/acceptance.json`。不以历史 CI 代替本机搜索。

## B02 开发记录（2026-10-13）

- B01 根据已推送的本机 G1 实测证据（55/55、英文/中文各 5 条、Docker 真实镜像 digest）接受技术验收，经安全快进至 `main`，未强制重写提交。
- B02 分支：`feat/b02-httpx-fetch`，从 B01 合并后的 `main` 建立；不并行修改已合并的 B01 历史。
- 实现：`src/local_search_demo/fetch/httpx_fetcher.py`，提供共享 HTTPX 客户端、URL/HTTP/超时/编码/大小/跳转错误处理、原始 HTML bytes 保留和可选保存。
- 只扩展 `FetchResult.redirect_history`；继续保留 B00/B01 的 SearchResult、ExperimentRecord 等现有字段语义。
- 测试：HTTPX MockTransport 单测及本机临时 HTTP 服务器集成测试；真实公网脚本为单独可选烟测，不做正文质量评判。
- 文档：[B02_ACCEPTANCE.md](./B02_ACCEPTANCE.md)。
- 进度：**本批尚未完成验收，不能标为 PASS**；CI/本机测试输出录入后更新。B03–B08 NOT_RUN。
