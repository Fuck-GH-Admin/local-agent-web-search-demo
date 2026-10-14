# 实施与验收台账

执行依据：`DEMO_EXECUTION_PLAN.md`；起点 `e90892ed9d278978fff3a583f96ec271d9c45ea5`。
B00–B04 已按各批标准接受；当前核对分支为 `feat/b06-readiness-audit`；已正常合并上游 B06 `688c5ae` 与已验安全分支 `adea99b`，统一 B07 前置基线。另见 [跨批次待补验索引](./OPEN_VALIDATION_INDEX.md)（每批必读）。

| 批次 | 状态 | 证据与说明 |
| --- | --- | --- |
| B00 | PASS | 本机技术验收与独立重建通过；用户已明确授权进入 B01 |
| B01 | PASS / G1 LIVE_PASS | 55/55 本机离线通过；真实中英文搜索均 HTTP 200 / 5 条；Docker 状态、固定镜像 digest、初始失败与上游错误均有证据 |
| B02 | PASS / LIVE_PASS | 本机 91/91 通过，含 36 项获取层用例；两个公网 HTML 均 HTTP 200，保存 bytes 的 SHA-256 一致 |
| B03 | PASS / G2 PASS | 本机 109/109（18 项 B03）通过；18 组内容复核完整，14 correct / 1 noise / 3 no_content；用户明确签认，完整性检查退出 0 |
| B04 | PASS / LIVE_PASS | 既有 CI 124/124 与三场景 smoke 已接受；本次两个目标机真实 CLI read 通过，与 WebUI 核心字段严格相同 |
| B05 | PASS / G3 PASS | 本机 133/133、CLI/API 5/5、真实 Chrome 17/17，16 张截图已复核并获用户明确签认；self-hosted 完整 CI 两轮通过 |
| B06 | PASS / READY_FOR_B07 | 298 项本机与 CI、实际 SDK 离线适配、四轨迹、两站 HTTPS、11 项安全检查及历史签认绑定通过 |
| B07 | G4 PASS / INTERFACES IN_PROGRESS | DeepSeek 实机 3 次 auto 闭环 + 用户 G4 签认；普通 CLI/API/WebUI Agent 已接 Core，接口回归与浏览器人工验收待完成 |
| B08 | PREPARED / G5 NOT_RUN | 已建立独立 B08 离线与显式 live 证据收集工具、最终报告草案；真实页面人工评审及本机性能/G5 尚未执行 |

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
- 进度：**B02 自动化自检 PASS**：GitHub Actions #38426304082，77 passed in 6.25s；机器公网 HTML 读取 `LIVE_NOT_RUN`（本计划非阻断）。固定证据见 `reports/B02/fetch-tests.json`；B03–B08 NOT_RUN。

### B02 分支合入记录

- B02 最终 CI：[GitHub Actions #38426510641](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38426510641)；`77 passed in 6.12s`、0 失败。此前用于固定报告的 #38426304082 为 `77 passed in 6.25s`，两份证据均真实发生。
- B02 满足执行计划的**自动化自检**条件后，已通过非强制 fast-forward 更新至 `main`，提交 SHA `fb4164a6d7c7c0f588149ddb85685bb991bee0f8`。未测试目标机器的公网 HTML，所以继续记录 `LIVE_NOT_RUN`。
- 后续工作只能基于该主分支最新状态开始 B03，不再使用已分叉的旧 B00 骨架分支。

## B02 本机完整补验（2026-10-14）

- 用户明确要求完整阅读文档、继续验证 B02 并上传。将现有 B02 分支非强制快进到最新 main `613bd217a3eddf5ea8e3c80810e74a3859102225`，保留所有既有提交。
- 已完整阅读本分支 README、需求草案、执行计划、上游预研、B00/B01/B02 验收、台账与 deploy/fixtures/web 说明，并复核 HTTPX 官方文档和下载器及测试源码。
- 原有 77 项测试在本机复现 PASS。发现 base64_codec、hex_codec、idna 三种 charset 会使下载器直接抛出解码异常；只检查 codec 注册不足以判断它能否用于文本。
- 修复：用非空输入检查文本解码及 replace 支持，异常标签按既定次序回退；原始 bytes 不改写。TIMEOUT 维持原分类，message 记录具体 Connect/Read/Write/Pool 子类型。没有修改 Schema 或验收标准。
- 回归增加 14 项：异常 charset、三种 BOM、HTTP 403、四种超时以及真实本地 403/429/503；已有保存用例证明只发生 1 次下载。完整 pytest **91 PASS**，其中 B02 **36 项**，没有失败或跳过。
- 目标宿主机使用现有代理环境变量，example.org 与 Python asyncio 文档实际返回 HTTP 200、UTF-8 HTML；原始 bytes 保存于 Git 忽略的 raw 目录，SHA-256 与结果记录一致。
- 新增 `scripts/verify_b02.py`，保存实际逐用例 JSON、JUnit、环境与依赖检查；`--live --save-html` 显式补验公网并保存已有 bytes。
- 旧 77 项 CI 报告完整保留为 `reports/B02/ci-offline.json`；修复前和中间失败快照单独保留。`fetch-tests.json` 是本次本机实测，不是旧 CI 或估算结果。
- 本次不运行正文提取、浏览器或模型，不合入远端 B03 开发分支；B03–B08 在本批中 NOT_RUN。

### B02 本机补验交付五件

1. 变更：charset 崩溃修正、超时子类型、14 项回归、可重复执行验收脚本、同步文档；实测实现 commit 为 `921bd7d9d2c1b288f4f31931ead1b1d8104279e4`，提交后统一验收命令再次通过。原始输出与本条更新在后续证据提交保存。
2. 命令：`uv sync --locked --all-extras`、`uv pip check --python .venv/bin/python`、`pytest -q`、`python scripts/verify_b02.py --live --save-html`；固定测试 PASS，公网 LIVE_PASS。
3. 证据：`reports/B02/fetch-tests.json`、`pytest.xml`、`test-summary.txt`、`environment.json`、`verification-checks.txt`、`live-smoke.json`、`live-command.txt`、`saved-html-checks.json`、`acceptance.json`；历史失败快照与旧 CI 分开保存。
4. 未解决：没有阻断 B02 的问题；公网结果仅代表这两个 URL 在此次环境的实际表现，正文质量待后续 B03。无需 B02 额外人工关卡，下一批未执行。
5. 台账：本节及 `B02_ACCEPTANCE.md`；完成本机技术验收后将代码、文档和非敏感证据推送现有 B02 分支。

## B03 当前批次（2026-10-14）

- 来源：从已接受 B02 自检的 `main` 建立 `feat/b03-parser-comparison`。
- 新增：Trafilatura、readability-lxml、Selectolax 三个独立适配器，比较层保证只输入同一份 HTML、保留三份可独立观察的输出、单个失败不影响其他结果。
- 测试/证据：6 类固定 HTML，B02→B03 单请求集成；`scripts/b03-compare-fixtures.py` 生成对比 JSON 和默认 `UNREVIEWED` 质量复核模板。正式统计结果待 CI 完成后更新。
- 数据契约：`ParserResult.metadata` 新增默认空字典（与既有字段兼容），正文长度与原始格式分开记录。
- G2：`NOT_RUN`；没有完成 18 组人工质量判定前不记通过。待处理事项在 `docs/OPEN_VALIDATION_INDEX.md`，包括继承的 `B02-LIVE-01` 和本阶段 `B03-G2-01`。
- B04–B08 未开始；当前不替 B04 选择“最佳解析器”。

### B03 自动化成果与观察记录

- 已核验 GitHub Actions #38429154060：Python 3.12.13、`93 passed in 6.22s`，CI 还生成并上传 JSON/Markdown 对比和人工标注空白模板。新增的 G2 工作表完整性检查已纳入本次 CI 并通过。
- 实际对比：[CI artifact #11830362359](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38429154060/artifacts/11830362359)。6 类合成页面 × 3 adapter = 18 组；15 个 PASS（有文本）、3 个 EMPTY（SPA 空壳），未观测到脚本字符串被误抽作正文。
- 有意义的差异：技术文档的 Readability 结果包含导航 `Overview Installation API Changelog`，Trafilatura 和 Selectolax 不包含；已列为 G2 人工复核重点。单次耗时差异仅做观察，不预先宣布最优库。
- 固化证据：[reports/B03/auto-observations.json](../reports/B03/auto-observations.json)；`G2 NOT_RUN`，必须依照 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md) 的 `B03-G2-01` 填写 18 组人工判断。
- 上述历史 CI 时的 B02 遗留 `B02-LIVE-01` 已于本次补验关闭：证据为 B02 分支 `64008dbf3549ca8451317197e8a9ebb381af1c16` 的真实下载记录；索引条目保留并更新为 PASS。

### B03 本机补验与 G2 内容复核（2026-10-14，签认前记录）

- 用户要求同时完成 G2，并指定阅读跨批次待补验索引。当前 B03 分支先以普通 merge 合入已验收 B02 提交 `64008dbf3549ca8451317197e8a9ebb381af1c16`，合并提交 `b9eaab86ddacff90e376e759acfec2bceccdf33e`；保留 B02 的 91 项实测和历史 CI 证据。合并后原有 107 项测试在本机全部通过。
- 发现比较层在模块初始化时一起导入三个 adapter，缺少 trafilatura/readability 依赖时整个入口异常退出，不符合现有失败隔离要求。两项新解释器回归实测修复前均失败，原始输出见 `reports/B03/import-isolation-before-fix.txt`。
- 修复为在每个 parser 的异常捕获范围内延迟导入；同时将公共文本函数的 Selectolax 导入移到 HTML 转文字函数，避免单纯 normalize_text 不必要地加载它。两项缺依赖回归已通过；错误仍为 PARSER_ERROR，未修改 Schema 或验收标准。Readability 的 HTML 后处理仍依赖 Selectolax，不能宣称三种算法完全无共享依赖。
- 本批由 Codex 逐项阅读六份输入和 18 组原始/规范化输出后填写质量判断与理由。按索引要求，最终人工签认须单独记录；自动锚点和工作表格式检查均不代替质量判断。

- 实测实现提交 `e979b6fabd5544cd50b4134235c179bed035917e` 上全量回归 **109 passed in 6.55s**，B03 为 18 项。环境、锁检查、完整逐用例与 JUnit 均保存在 `reports/B03/`。
- 全部输入及输出已逐项阅读；工作表 18 行均有标签和完整理由，14 correct / 1 noise / 3 no_content。技术文档 Readability 保留了 35 字顶层导航，残缺 HTML 的 Trafilatura 有词句粘连；保留差异，不外推真实网页覆盖率或预选 B04 算法。
- CI 工件改为在独立目录重新生成未标注表，避免旧质量标签套到新观测；保存工作表不受新生成影响的实际检查见 `ci-artifact-isolation.json`。
- `agent_review_status=REVIEWED`，最终用户签认 PENDING。实际运行完整性脚本仅因 human_review_status 尚未 REVIEWED 而返回 2，原始输出现保存为 `g2-check-before-signoff.txt`；当时没有把该运行包装成 G2 PASS。B03-LIVE-02 保持 NOT_RUN。

### B03 本机补验交付五件

1. 变更：合入 B02 真实补验、修复 parser 依赖导入隔离、增加两项新解释器回归，生成完整固定样本比较与逐项质量理由；解析实现 SHA 见上。
2. 命令：锁定环境、依赖检查、全量 pytest、`b03-compare-fixtures.py`、`b03-g2-check.py`；109 回归通过，工作表最终人工状态待签认。
3. 证据：`reports/B03/parser-comparison.json` / `.md`、`manual-review.json`、`quality-review.md`、`parser-tests.json`、`pytest.xml`、`pytest-summary.txt`、`environment.json`、`dependency-checks.txt`、`ci-artifact-isolation.json`、`import-isolation-before-fix.txt`、`g2-check.txt`。
4. 待办：用户对具体 18 行报告的人工签认；B03-LIVE-02 为后续非阻断真实网站实验，B04–B08 未开始。
5. 台账与交付：本节、`B03_ACCEPTANCE.md`、执行计划与索引已同步；代码、文档及非敏感证据推送 `feat/b03-parser-comparison`。

- 云端证据：推送报告提交 `546b3af789fc5884ea78de18ed2ba4ccecc9f797` 后，Actions #38485766242 与 #38485758925 均 SUCCESS；实际日志 109 passed in 7.50s。下载工件 #11859067857 验证 18 组正文/标题/状态及输入 SHA 与本机一致，人工表全部 UNREVIEWED，证明未继承本机复核标签。记录见 `reports/B03/ci-offline.json`；G2 最终人工签认仍 PENDING。

### G2 用户签认与关闭（2026-10-14）

- 用户在本会话明确回复“我签认，你可以继续”，签认报告提交 `83ccfae346956e7d9149fe1e190418b10047771d` 的 18 组内容复核结论；记录时间 `2026-10-14T07:58:02.972072+08:00`（Asia/Shanghai）。内容判断仍标明 Codex 辅助复核，用户负责最终签认，未冒充用户重新运行测试。
- 签认证据 `reports/B03/g2-signoff.json` 绑定原始比较、签认前工作表和摘要 SHA-256；18 行原有标签与理由保持原样，14 correct / 1 noise / 3 no_content，已观察到的导航和词句粘连继续保留。
- `manual-review.json` 人工状态设为 REVIEWED、签认状态 APPROVED。实际运行 `.venv/bin/python scripts/b03-g2-check.py` 退出 **0**，输出 Worksheet COMPLETE (18 reviewed)；旧待签认输出保存在 `g2-check-before-signoff.txt`，最终结果为 `g2-check.txt`。
- 同步 README、B03 验收、执行计划、跨批次索引及 acceptance.json 为 **G2 PASS**。`B03-G2-01` 保留历史行并关闭，B02-LIVE-01 继续 PASS，B03-LIVE-02 继续 NOT_RUN。
- 本次仅更新签认记录和验收状态，解析实现与已通过的 109 项回归保持同一代码版本；完成一致性检查后推送 B03 分支并核对新提交 CI。

## B04 已实施记录（2026-10-14）

- G2 PASS 后，B03 完整分支 `24cb052ebe5c53a59db13a166939fe857825169a` 已非强制 fast-forward 合入 `main`；B04 从其上新建 `feat/b04-core-cli`，不覆盖历史。
- 交付：`pipeline/reader.py` 将 B02 一次 HTML 下载、B03 三解析器比较与透明候选选择整合；`pipeline/chooser.py` 保留每个候选评分、淘汰解释与原始三个结果；CLI `read` 接入，JSON/`--output`、可选 HTML bytes 保存。Agent 仍 NOT_IMPLEMENTED。
- 保持已验收 B03 的结果结构，在 `ReadResult` 和 `ExperimentRecord` 增加兼容的可选字段 `selected_text`、`selection_evidence`，不改变 G2 结论。
- 第一轮 CI `123 passed, 1 failed`，失败是原 B00 占位测试仍要求 `read` 返回 NOT_IMPLEMENTED；实际 `read` 已实现。旧断言已更换为真实 INVALID_URL 行为检查，**旧失败历史保留在 GitHub Actions #38489056872**。
- 修复后实际 CI：[GitHub Actions #38489137689](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38489137689)；`124 passed in 9.03s`。同批 CLI smoke 三场景 PASS；读取 CI 工件核实：单文章/SPA/404，正文选择/无正文分类正确；固定摘要 `reports/B04/ci-offline.json`。
- 验收判断：**自动化自检 PASS**，不是目标 Ubuntu 机器公网网页读取 PASS，也不是全网正文质量结论。经最终 CI #38489462556 确认（124 passed in 9.12s，三场景 smoke PASS）后，已安全 fast-forward 合入 main；公网真实读取仍在跨批次索引中开放。
- 遗留追踪：`B03-LIVE-02` 仍为 NOT_RUN；新增 `B06-URL-SEC-01`，模型控制的 URL 必须在 B07 真实调用前做 SSRF 防护策略与绕过测试。详见 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md)。

### B04 最终自动验收与合入

- 最新 B04 提交 `8e289d4f463b32e3546d6a23ff7d2c00e1300405`： [GitHub Actions #38489462556](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38489462556) **SUCCESS**，`124 passed in 9.12s`；真实本地 HTTP CLI smoke **3/3 PASS**，并核实了下载的 JSON 工件。
- 已用非强制 fast-forward（期待旧 main SHA `24cb052ebe5c53a59db13a166939fe857825169a`）将 B04 合入 `main`。代码和当前索引一致；未覆盖已验收的 B03。
- 需要补验：`B03-LIVE-02`、`B04-LIVE-01` 均 NOT_RUN/非阻断；`B06-URL-SEC-01` 是模型控制 URL 前的安全阻断项。所有记录保留在 `docs/OPEN_VALIDATION_INDEX.md`。

## B05 开发记录（2026-10-14）

- 从通过 B04 CI（124/124 + 3/3 CLI 回环测试）的最新 `main` 建立 `feat/b05-fastapi-webui`，不改变 B00–B04 历史。
- 新增 FastAPI HTTP JSON API 和原生 HTML/CSS/JS 三页签；搜索/读取均直连已有 B01/B04 Core。Agent 明确返回 501。
- 统一 HTTPX AsyncClient 与生命周期；WebUI 第三方页面内容仅以文本显示。设置开发服务 `127.0.0.1:8765`，不得作为未鉴权公网服务。
- 新增 TestClient API 回归、同一 fixture CLI/API 实际 loopback 对照 JSON 脚本、wheel 静态资源检查；完整结果以最新 CI 实际输出为准，不伪造运行证据。
- G3 人工浏览器验收还未在用户机器执行，当前 `NOT_RUN`；必须核对 [B05_ACCEPTANCE.md](./B05_ACCEPTANCE.md) 与 [OPEN_VALIDATION_INDEX.md](./OPEN_VALIDATION_INDEX.md) 的 `B05-G3-01`。
- 继续保留 `B03-LIVE-02`、`B04-LIVE-01` 和 `B06-URL-SEC-01`。

### B05 自动化验收结果（2026-10-14）

- GitHub Actions #38492556772 首轮 132/132 成功，CLI/API 5/5 PASS，wheel 资源检查通过；随后加入 Host 白名单与 CSP/no-store 等安全头，并补一项回归。
- **最终实现测试证据**：[GitHub Actions #38492812276](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38492812276)，`133 passed in 8.33s`，CLI/API 5 场景全部 PASS，`node --check` PASS，`uv build --wheel` 资源检查 PASS。
- 直接下载并核对 CI artifact #11861829788；固定到 `reports/B05/api-tests.json` 和 `reports/B05/ci-offline.json`。4 组核心对比严格一致（忽略随机 ID/时间戳/耗时），本地合成 HTTP 源对每条页面/搜索查询均收到 CLI 与 API 各 1 次请求。
- 技术自检 **PASS**；G3 实际浏览器、搜索源联网、三解析器可视化人工检验仍 **NOT_RUN**。执行步骤及空白检查模板见 `docs/B05_ACCEPTANCE.md`、`reports/B05/g3-local-review.template.md`。
- **不得在 G3 前把本批总验收写成 PASS 或合并 main**。跨批次索引 `B05-G3-01` 已更新；`B03-LIVE-02`、`B04-LIVE-01`、`B06-URL-SEC-01` 不变。

## B05 目标主机完整验收与 G3 实机证据（2026-10-14）

- 用户明确要求继续 B05，包含 G3 实机证据与索引清单。同步 `origin/main` 3bec4da 和 B05 `4e5f56331f02dfd04864782f12198c9fd6c41f2c`，已包含已接受 B04 与 G2 签认；没有重写主分支或历史记录。
- 本机回归 **133 passed in 8.42s**，CLI/API 固定输入 **5/5 PASS**，依赖、JS 语法、wheel 静态打包检查均实际通过。现 api-tests.json 为本机版本，原 CI 工件保留为 ci-api-tests.json。
- 新增两个可复现 QA 驱动：loopback saved HTML 服务和外部 Playwright 驱动的真实 headed Chrome/Xvfb；不修改应用业务逻辑、Schema、验收标准或依赖锁。测试实际产生 17 项检查和 16 张 PNG，脚本内容 SHA 可追溯。
- 中英文搜索在浏览器实际 HTTP 200、各 5 条；两页真实读取成功并与 CLI 的正文、全部三解析器、候选决策严格相同。API 返回与浏览器 DOM 逐项断言一致；截图再由 Codex 逐张阅读确认显示。
- 真实搜索另一次 CLI 请求的 URL 排序/错误不同，未当作严格相同；来源与时刻保存在 live-cli-ui-parity.json。Brave 限流和 Wikidata 超时/暂停原样保留；固定输入 5/5 对照说明业务入口同值。
- 未捕获 JS 异常 0，console 网络提示 3 条（favicon 404、主动断网、Agent 501）逐项记录。SPA、404、断网及恢复、302、无效查询与 390px 窄屏均有真实截图。
- `B04-LIVE-01` 已用此次两个真实 CLI read 关闭；`B03-LIVE-02` 的独立质量泛化专项继续 NOT_RUN，不能用 UI/CLI 相等替代准确率。B06-URL-SEC-01 与 B07-G4-01 仍待对应阶段。
- 实机执行及 Codex 截图复核完成，正式 G3 仍 AWAITING_USER_REVIEW；根据 B05_ACCEPTANCE.md 的“由用户审核后将状态写为 G3 PASS”，最终签认必须另行记录，未从已有 G2 授权推定 G3 已签认。

### B05 本机验收交付五件

1. 变更：两项主机 QA 驱动、真实浏览器记录与 16 张原始截图、本机回归与严格对照、实际公网读取补验；应用实现 SHA `4e5f56331f02dfd04864782f12198c9fd6c41f2c`，业务逻辑与依赖锁保持相同。
2. 命令：锁定环境、全量 pytest、b05-api-parity、JS/wheel、uvicorn、saved fixture origin、Chrome/Xvfb 真实表单驱动及真实 CLI 中英文搜索/两页 read；技术检查通过。
3. 证据：reports/B05/g3-local-review.md、screenshots/、browser-observations.json、live-cli-ui-parity.json、cli-live-commands.json、api-tests.json、pytest.xml、pytest-summary.txt、pytest-cases.json、environment.json、wheel-check.json；完整公共网页响应只在忽略 raw/ 保存。
4. 待办：具体 G3 证据的最终用户审核；B03-LIVE-02 和后续 B06/B07 保留。没有隐藏实机执行或把 CI 截图冒充本机截图；未宣称 console 全部无错误。
5. 台账与交付：B04/B05 验收、执行计划、索引与 README 同步；代码、非敏感证据和原始 Chrome PNG 推送 B05 分支，G3 正式签认前不合并 main。

### B05 云端新提交诊断（2026-10-14）

- 已推送实机证据提交 `d059b8028a2661703cc27bbc62c1c8dbd4cc6f02`，实际远端 SHA 核对相同。
- 新 Actions #38497254054（pull_request）及 #38497249637（push）在约两秒内结束 failure，无 runner、无执行步骤、日志空。直接读取两份 check-run annotations，GitHub 明确提示账户付款失败或支出限额需要提高；不是已执行 pytest 后断言失败。
- 原始诊断与实际 annotation 保存在 reports/B05/ci-startup-blocked.json，索引新增 B05-CI-01 BLOCKED。账户限制解除后再补跑当前提交的云端回归；没有修改账单、预算或工作流回避检查。
- 本机 133/133、CLI/API 5/5、浏览器 17/17 和 16 张实机截图均已完成，仍如实保留；正式 G3 最终用户审核独立 PENDING，PR #5 保持原有 Draft，不合入 main。

## G3 用户签认与本地 runner CI 复验（2026-10-14）

- 用户明确回复“签认。还有关于ci可以重跑，我应该是添加了一个本地的。”，签认已提供的 `b1168c74115ec1ea9c746808af2dcc99abaaf699` G3 报告，记录时间 `2026-10-14T11:43:09.331072+08:00`。签认文件 reports/B05/g3-signoff.json 绑定报告、浏览器观察及 16 张原始截图；17 项检查与截图不重生成，不冒充用户亲自执行过操作。
- GitHub API 确认一个 online/空闲的 repo runner：ghrunner-local-agent-web-search-demo，Linux/X64、版本 2.338.0。主分支新提交 `d259d5986e026244327e2e566b27a6a07661ecb3` 改为 self-hosted；已普通 merge 合入 B05，保留全部既有自动化步骤。
- G3、B05-G3-01 同步 PASS；历史 hosted 计费 failure 与原始 annotations 保留，B05-CI-01 仍待实际新的 self-hosted 运行通过后关闭。重新触发时使用最新已合入路由配置的提交；原分支旧 workflow 仍指向 ubuntu-latest，不把仅注册 runner 当作复跑成功。
- 本次未改变业务逻辑、Schema、依赖锁、已签认的实际输入和图片；推送签认及路由合并提交后核验实际 job runner、完整日志与对照/构建工件。

### self-hosted 首轮与 Node 环境修正

- 实际在 ghrunner-local-agent-web-search-demo 执行 #38508022220 / #38508026568，原 hosted 计费启动问题已被新的 runner 路由解决。
- 首轮完整 pytest **133 passed in 9.08s**，B03/B04/B05 Core 检查均运行；JS 步骤实际退出 127：`node: command not found`。原始失败日志保存为 reports/B05/ci-self-hosted-node-failure.txt，完整步骤状态保存为 ci-self-hosted-before-fix.json；没有把失败运行写成完整 CI PASS。
- 保留 JS 检查，新增 actions/setup-node@v4 显式准备与本机 QA 相同的 Node 22.23.2；只影响 CI 工具，不改 Python 应用依赖、业务逻辑或已签认截图。依据：[官方 setup-node v4](https://github.com/actions/setup-node/tree/v4)。
- 环境修正后重新执行同一套完整流水线，再据实际结果关闭 B05-CI-01。

### B05 / G3 最终签认与 CI 关闭

- 用户已签认 G3，证据 g3-signoff.json 绑定签认前提交 b1168c7 的报告与 16 张真实 PNG；17 项原检查保持相同。本批本机与实际 WebUI 验收 PASS。
- 新 self-hosted 最终提交 `26d3c55ff1c19a0b662fcd54c1ac3087f6f091ca`，Actions #38508574650（push）和 #38508577291（PR）在 ghrunner-local-agent-web-search-demo 均 SUCCESS。读取真实日志确认 133 passed in 8.95s / 8.97s；全部 17 个步骤成功，包括显式 Node 22.23.2、JS、wheel 和工件上传。
- 下载 artifact #11868234389 核验 B05 对照 5/5、B04 smoke 3/3 与请求计数；B03 18 行 CI 工作表仍空白，不冒充已签认质量。结果写入 reports/B05/ci-self-hosted.json、ci-self-hosted-api-tests.json、ci-self-hosted-b04-smoke.json。
- 关闭 B05-CI-01 为 PASS，并保留原 hosted 计费失败、self-hosted 首轮 Node 缺失日志与修复证据。B05-G3-01 已 PASS；B03-LIVE-02、B06-URL-SEC-01 和 B07-G4-01 继续保留，不删历史条目。
- 原 G3 签认与业务实现保持一致，工作流使用用户已配置的本地 runner 并保留全部检查；最终签认和 CI 证据继续推送 B05 分支。

## B06 工作批次（2026-10-14）

- B05 证据交叉核验：本机 133/133、17 项真实 Chrome 操作/16 张截图、G3 用户签认；GitHub Actions self-hosted #38508574650 和 #38508577291 两次完整运行 SUCCESS（均 133 项，通过静态资源/JS/B04/B05 回归）。
- B05 分支包含 `main` 全部此前提交，已通过非强制 fast-forward 将最终提交 `125bb9b50a761c1fed09071bc67670c7a43eabaf` 安全合入 `main`；没有覆盖历史。B06 从最新主分支创建 `feat/b06-agent-tool-loop`。
- 本批已开发：JSON Schema、ScriptedModelProvider、OpenAI Chat Completions SDK 适配接口、有限回合的 AgentRunner、工具 ID/错误 trace、引用 URL 核验及实际复用搜索/读取 Core 的 MockTransport 实验脚本。
- **安全阻断**：`B06-URL-SEC-01` 在真实模型读取时仍 NOT_PASS；当前 Dispatcher 的模型控制真实 URL 读取全部被 `URL_POLICY_NOT_READY` 拒绝。DNS 绑定和跳转逐跳复核属于下一部分，严禁跳过。B06 的模拟模式使用明确注入的 `httpx.MockTransport`，不接公网。
- 本阶段运行状态：测试提交并由 CI 执行后补充实际通过数量；真实模型与 G4 属于 B07 尚未启动。待办见 `docs/OPEN_VALIDATION_INDEX.md` 中 `B06-MOCK-01`。

## B03-LIVE-02 与 B06-URL-SEC-01 一次性补验（2026-10-14）

- 用户明确要求“那一趟做完吧”，授权补齐两项并延续 GitHub 推送。发现远端最新 B06 工具循环分支 `a3875dd`，基于该版本创建 `feat/live-quality-url-security`，避免实现重复工具入口。实现提交 `f432b8c`。
- B03 实际采集六个不同网站，全部 HTTP 200；同页同 HTML 输入三解析器，原始输入/完整输出只在忽略 raw/ 保存。逐项读源正文、raw 结构、规范化全文、标题及元数据，用差异定位辅助，人工写 18 行理由；12 correct / 2 partial / 2 noise / 2 no_content。内容阅读者 Codex，非自动赋分，未声称用户新增签认。
- 质量差异真实保留：Wikipedia Readability 只保留部分法律段落，MDN Readability 缺导语/章节标题；Selectolax 百科结果含分类/维护噪声；draw.io Trafilatura 只取 noscript 提示，另两者为空。原 G2/G3 签认和算法不变，不作全网覆盖率/单次性能排名。
- B06 在 live Dispatcher 接入独立 PublicURLTransport：初始语法与本次来源检查、全部 DNS 回答公网检查、IP 绑定连接、原域名 Host/SNI/证书验证、逐跳复核/5 次上限、端口及特殊地址拒绝、禁环境代理/跨域错误连接复用。SearXNG 本地客户端不能用于模型 URL 读取；复用 Runner 清除前轮来源。
- 发现并保留实际失败：空 userinfo 规范化使第一次回归失败；旧地址分类允许 deprecated relay/site-local。修复及新增回归后通过，不删除 before-fix 证据。
- 本机 `uv lock --check`/`uv pip check`、全量 **259 passed in 8.63s**、B06 模拟 **4/4**、B04 **3/3**、B05 CLI/API **5/5**、JS 和 wheel 模块/资源检查通过。新安全 103 项与循环 23 项；完整命令、JUnit 和包/源码哈希保存在 reports/B06/url-security/。
- `b06-url-security-smoke.py --live` **11/11 PASS**：受保护生产 transport 直连 Python/GNU 均 200，真实 SearXNG 搜索结果经 live Dispatcher 读取 200；实机 loopback sentinel 收到 0 个请求。脚本调用不是实际模型决策，不标 B07 G4 PASS。
- 关闭索引 B03-LIVE-02、B06-URL-SEC-01 与本次确实执行的 B06-MOCK-01；B07/G4、B08/G5 仍按后续批次。CI 待读取新分支的实际运行/工件后另附，不由本机结果推定。

### 本次实现 CI 核验

实现提交 `f432b8c68b1beb540a0ae74c7596084a27203bdd` 已推送；[Actions #38515437204](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38515437204) 的 19 步在 ghrunner-local-agent-web-search-demo 全部成功，实际日志 **259 passed in 9.44s**。下载 artifact #11871173508：安全 8/8、sentinel 两次均 0 请求，B04 3/3、B05 5/5、B06 4/4；新 B03 CI 人工表仍 18 行 UNREVIEWED。独立保存 `ci-source-implementation.json`/`ci-source-smoke.json`，原始 ZIP 只在忽略 raw/。最终文档与证据提交后，再读取该提交的 CI 状态，不通过继续改证据来制造无限新提交。

## B06 全面核对并停止在 B07 前（2026-10-14）

- 用户要求“你去核对现有进度，做验证。确保下一步可以推进B07后停下来。”远端 main 仍为 accepted B05 `125bb9b`；B06 已推进到 `688c5ae`，另有 B07 草稿 `dfaea53`。发现前次补验与上游默认关闭/安全传输分叉，正常 merge `7086691` 整合，保留双方历史与默认关闭开关。
- SafePublicTransport 保留上游 API、复用更完整的 PublicURLTransport 策略，消除第二份 IP 分类与连接复用差异。兼容现有 B07 的 enable_live_reads 参数，未改变 B07 草稿或执行其 run_live。
- 新补测发现空回答误记 DONE、数量/时间限制提前 break 漏记剩余调用 ID；实际修复前 **5 FAIL / 8 PASS** 快照保留。修复提交 `4aa924158094e437327f6ce3c939ea20ad58cd70`；新增 13 项，其中 8 项经过实际 SDK 的离线 HTTP 请求/响应。没有用 ScriptedModelProvider 代替 SDK 接口检查，没有真实模型 API 调用。
- 本机全量 **298 passed in 8.74s**；四轨迹、B04 3/3、B05 5/5、依赖锁/JS/wheel 全通过。两站 b06-safe-http-live 实际 PASS，安全烟测 11/11、loopback 0 请求。G2/G3 已签认的原 Git blob 与 16 张 PNG 哈希全部重新核验，六网站原始快照/工作表检查完整。
- 实际 [CI #38526842708](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38526842708) 19 步通过，下载日志和 artifact，确认 298 项、13 项新前置回归、8 项安全 smoke 及 B04/B05/B06 工件结果。原始日志 ZIP 只在忽略 raw/；早期失败与待验记录不删除。
- B06 整体技术自检、B06-MOCK-01、B06-HTTPS-01 和 B06-URL-SEC-01 均通过，可以进入 B07。当前三项真实模型环境变量均未配置，只核对有无且不记录值；配置与真实兼容性属于 B07，不能推定 G4 已通过。未声明新的人类用户签认，保留操作者显式启用要求。
- 最终证据提交后核对最新 CI，以非强制 fast-forward 同步 B06/main 并验证远端 SHA；B07/G4 与 B08/G5 保持 NOT_RUN，按用户要求停下，不自动开始下一批。

## B07 开发恢复（2026-10-14）

- 新请求授权继续 B07。核对：B06 正式分支与 `main` identical；最终 CI #38526842708，298/298、19 步成功。B06 三项技术关卡已在 `OPEN_VALIDATION_INDEX.md` 关闭 PASS。原旧草稿 `feat/b07-real-model-prep` 已与 main 分叉（7 ahead / 5 behind），不可直接作为已验收基础。
- 基于已验证 `main` 重新建立 `feat/b07-real-model`，仅迁移旧草稿中 B07 启动器、保护测试及 G4 文档，调整已有 B06 G6 PASS 事实。不把旧分支中的 B06 DNS/SSRF 实现覆盖进来；旧草稿 Draft PR 作为历史参考。
- 新增 `scripts/b07-g4-review.py`：用真实模型原始轨迹检查 auto/tool-call/搜索到读取顺序/有正文/引用来源一致等机器可验证条件；输出无提问、页面正文和 URL 的脱敏 Markdown，**不会自动标 G4 PASS**。
- 新增 `reports/B07/*.json` Git 忽略，防止真实模型输出、提问、读取内容与 API 相关敏感上下文在正常 `git add -A` 时提交。真实 API 测试需操作者显式本机启动、提供环境变量；代码与离线自检本身不收费。
- B07 状态 `IN_PROGRESS / REAL_MODEL_NOT_RUN`，全量回归及 launcher 离线自检要以新 CI 结果为准。G4 仍须目标 Ubuntu 真实 API 调用与人工证据签收；B08 NOT_RUN。

## B07 用户凭据授权与 DeepSeek 实机验证（2026-10-14）

- 用户授权查看云端并用其官方 DeepSeek API 测试。核对 main `856ca50`、草稿 PR #8/#9，选择 main 后创建的正式 `feat/b07-real-model` / PR #9 继续。密钥通过关闭回显的临时进程标准输入注入，只在进程/子进程环境中使用；未写仓库、bashrc、报告或 CI secrets。
- 实际官方 /models 鉴权 200；仅实测 deepseek-flash、Chat Completions、thinking disabled。显式模式按当日官方 docs 核对；thinking reasoning_content 续轮和非正常 finish_reason 仅离线补测，未虚报思考模式实测。
- 源码提交 `d087d07c4de8cd19ad5fc4250779ecbfc15801a3`：显式模式与 token 预算、安全 SDK 调用元数据、required 首轮后 auto、原始报告 0600、独立 Core 阶段与 DNS/IP 固定证据。普通入口没有激活，按原 B05/B07 执行计划新增 B07-INTERFACES-01 待办，避免把独立启动器等同全部接口完成。
- 真实 auto 控制 1 回合/0 工具正确；required 2 回合/1 搜索正常结束；3 次 auto 联网均完整闭环，最终提交 3 模型回合/1 搜索/2 读取/1 引用/0 未核引用，7269.597 ms，两站 HTTP 200，六个 parser PASS。实际所有模型调用共 12 次，17408 prompt / 1133 completion tokens；无自动重试。
- Codex 逐项阅读五份轨迹的输入/调用 ID/结果/正文/回答，相关论断由短概览正文支持。长页给模型 6000 字符截断保留；Brave 限流保留但 SearXNG 有可用来源。实际没有诱发模型 401/429/超时、拒绝或空正文，不把离线负例当真实故障实测。
- 阶段日志扩展一度破坏两个既有无参数工厂注入测试：312 PASS/2 FAIL。恢复兼容且保持原安全断言，最终本机 314 passed in 9.47s、0 skip；前次 JUnit/raw 及其 SHA 保留。B04 3/3、B05 5/5、B06 4/4、锁/依赖/JS 通过。
- 源码 push #38545290884 与 PR #38545299093 CI SUCCESS；下载 PR 日志与 artifact #11883968497 确认 314 passed in 11.67s、20 步、9 个新增 SDK 测试及 Core/安全工件。CI 不注入模型凭据，不进行付费模型调用。公开 `reports/B07/validation/ci-source.json`，原始 ZIP 本机忽略 raw/。
- 独立启动器技术状态 LIVE_PASS；正式 G4 用户签认 NOT_RUN / PENDING_USER_SIGNOFF。将“真实模型未运行”的旧状态更新为已实测待签认，并保留正式 PASS 必须有用户签认的边界。公开 summary/acceptance 仅脱敏指标与原始 SHA，原始 JSON、URL、模型回答和页面正文不上传。B08 NOT_RUN；最终文档提交的精确 head CI 另作只读核验，避免重复提交证据触发新一轮。

## G4 用户签认与准确性边界（2026-10-14）

- 用户明确回复“签认。”，批准上一条交付的 G4 DeepSeek 实机报告；记录时间 `2026-10-14T18:10:35.077751+08:00`。`reports/B07/validation/g4-signoff.json` 绑定已交付证据提交 `761b868bdeb43ee6a02f68fbd9c81d377709d10b` 的 5 个原 Git blob、五份本机轨迹 SHA，以及实际模型实现 `d087d07`。哈希逐一核对通过，三个 auto 联网候选重新只读初筛 READY_FOR_HUMAN_REVIEW；未重新调用模型或改写原轨迹。
- 原始 `acceptance.json` 保留签认前编制快照；正式当前状态由签认文件与索引记录。G4 / B07-G4-01 改为 PASS，内容复核者 Codex、最终签认者用户。普通 CLI/WebUI/API Agent 激活仍为 B07-INTERFACES-01 NOT_RUN，B08 未完成；不将 G4 签认扩展为这些未执行事项的批准。
- 用户同时询问搜索准确性能否达到本会话助手的 80%。现有 314 个工程回归和同一官方文档题目的三次重复实测不构成代表性对照评测；没有本项目或本会话助手在相同题集上的准确率/分数比。验收文档明确记录“尚不能量化”，签认不包含任何 80% 质量声明。参考官方任务评测原则，记录同题、独立答案与人工评分的测量方式；本次不运行新增付费评测。
- 签认前精确 head 的 push #38546691573 / PR #38546698764 均 SUCCESS，已实际核验日志与 artifact #11884787383：314 passed in 10.17s、零 fail/error/skip、Core 与安全工件 PASS。签认文档提交后核验新 head CI，原模型证据保持相同。

## B07 普通入口接入（2026-10-14）

- 新分支 `feat/b07-agent-interfaces` 从已签收 G4 的 `feat/b07-real-model` 安全快进后的 `main` 创建。原 G4 用户签认绑定 `reports/B07/validation/g4-signoff.json`，本子批不变更签认依据。
- 新增 `agent/service.py` 共享执行逻辑；普通 CLI agent 入口支持明确的本机凭据、预算、JSON/0600 报告、`--allow-live-read`；FastAPI/API + WebUI 使用同一逻辑，不注入云端模型凭据到浏览器。
- 安全：Host/CSP 不退化，API Agent 拒绝不匹配 Origin；WebUI 需要服务端 `LOCAL_AGENT_ALLOW_LIVE_READ=1` 和单次勾选双重授权；B06 signed + HTTPS gate 仍有效。
- 本批状态为 `IN_PROGRESS / LOCAL_UI_NOT_RUN`，自动 CI 和目标机真实浏览器验证待补；绝不将 B07-G4 已通过直接升级 B07-INTERFACES-01。
- 子批说明 `docs/B07_INTERFACES_ACCEPTANCE.md`；跨批次索引始终保留不通过条目。B08 仍未开始。

## B08 筹备批次（2026-10-14）

- 从 B07 普通 Agent 入口开发分支 `feat/b07-agent-interfaces` 派生 `feat/b08-final-validation`；两批保持独立验收，B07-INTERFACES-01 本机人工验收未通过前不签收 G5。
- `scripts/b08-validation.py` 默认仅做离线回归，显式 `--live` 从 B03 六个不同真实站点重新下载，并记录三个解析器新输出的 SHA/状态/耗时；绝不拷贝旧质量标签。私有 HTML/JSON 可经 `--save-private` 写入 0600 且 Git 忽略的 raw 目录。
- 收集已有 G2/G3/G4/B06 签认元数据与进程峰值 RSS；不虚构目标机 Docker/SearXNG 常驻内存或模型额外重测数据。
- `docs/B08_ACCEPTANCE.md` 定义整体验收步骤与未完成事项，`docs/DEMO_TEST_REPORT.md` 为状态 DRAFT 的最终报告模板。
- 当前未在目标机执行 B08 真实公网六站、B07 普通浏览器、Agent G5 重测或人工评分，**G5 NOT_RUN**。任何 CI 离线成功不能取代这些工作。

### B07-INTERFACES-01 自动化实测

- 旧 CI #38550515144：pytest 323/323，通过，但 B05 parity 的 501 占位断言过时导致整体验证失败；已修正，不隐藏失败。
- [新 CI #38551213517](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38551213517)：`323 passed in 10.53s`、B07 7+9 项专项测试、SDK HTTP 回环 CLI/API PASS，B04 3/3、B05 5/5、B06 4/4 仍 PASS。
- 定义 `SELF_CHECK_PASS / LOCAL_UI_NOT_RUN`；目标 Ubuntu 上真实模型驱动的普通 CLI/API/WebUI Agent 操作、截图、错误恢复与访问安全仍须由实机验收，见 `docs/B07_INTERFACES_ACCEPTANCE.md` 和 `reports/B07/interfaces/local-review.template.md`。
- 代码仅在独立 Draft PR #10，未合入主分支，B07 G4 的用户签认历史不变。

## B07 接口核验的协议补充（2026-10-14，实施前记录）

- 用户授权继续 B07 接口与 B08 验收，基于云端 69993bf 接口实现。既有 323 项回归通过；补充真实接口边界检查发现预算类型/非有限值、空白提问的处理和请求验证回显需修复，修复前 JUnit 保存于本机 interfaces/raw/。
- 原普通入口返回 AgentTrace 仅包含总体/工具耗时，丢失 provider.call_log 与 Dispatcher 阶段证据；B08 要求模型/下载/三解析器分阶段计时。向 AgentTrace 增加可选默认空列表 model_calls 和 core_execution_evidence，只记录已有安全元数据，业务工具结果和选择算法不变，旧 JSON 仍可载入。影响普通 CLI/API 的观测字段；既有 G4 签认的原 Git blob 和原轨迹不改写。

## B07-INTERFACES-01 实机技术验收（2026-10-14）

- 在云端已实现接口上补验并修复：8项入口边界/计时失败，实际 CLI/UI 误判中文引用，保留 raw/before-edge-fixes 与 before-citation-fix。源码 a5d4bcf、735bccf、85d65d6 连续记录；新增 8+9 项回归，不放宽私网/来源校验。早期 CLI 发行状态猜测保留，收紧来源提示后复验，未宣称通用准确率改善。
- 最终真实 CLI/API UI均 DONE；auto 联网各3模型回合、2搜索/2读取，两个共同官方页面选中解析器/模型正文 SHA 相同。最终回答与实际正文逐项对照，未知稳定版本明确未核实。控制题正确；七项实际接口拒绝/缺配置保护通过。
- 真正 Chrome153/Xvfb、390px、错误恢复、固定恶意HTML文本安全及零JS未捕获错误：9/9，5张捕获时脱敏PNG逐张检查。未将固定Scripted安全负例当实际模型输出；原图/回答只在本机 raw/。
- 源码 CI #38555991213/#38555999471 SUCCESS，下载 PR22步实际日志及artifact11890506809核对340/340（9.89s）、Core/安全/SDK接口工件。公开 evidence仅脱敏指标/原始SHA，原G2/G3/G4签认不重生成。
- 本项技术PASS，可继续用户已授权B08；新增用户审核随G5具体报告提供，不伪造接口或G5签名。准确性基准按用户要求延期。

## B08 采集器证据完整性修正（2026-10-14）

- 正常 merge da478b1 将实机通过的 B07 分支接入 B08，保留双方提交与文档历史。新补测发现原采集器只保存解析 JSON、没有原始 HTML，重复采集覆盖原记录，且缺失/无绑定的 APPROVED 元数据仍可得到 precheck 成功。修复前三项均 FAIL，JUnit 留本机 B08/raw/。
- 修复为每轮独立 0700 目录，原 HTML 先创建 0600、单次下载即保存、记录字节 SHA，与解析 JSON 绑定且不覆盖旧轮；Core 算法不复制。回归子脚本的历史输出归档本轮新结果后恢复原 bytes，保留 G2/G3/G4 签认材料。
- 原关卡校验核对原 Git blob、G3 16 PNG、可用的 G4 本机轨迹 SHA、B06 原源码/锁文件；缺失或无绑定不计 precheck PASS。CI fetch-depth=0 用于历史审批绑定，CI 不接模型密钥。七项采集器/启动保护测试通过；本轮网站内容与模型仍需接着实测。

## B08 本轮整体验收与最终报告（2026-10-14）

- 采集源a14df8a、应用源85d65d6：347/347（9.67s），B04/B05/B06/B07分别3/5/4/4实际子进程PASS；历史审批原Git blob/PNG/G4轨迹校验3/19/11/10通过。新增e48a8f2将实际CLI受控429/403/超时3/3纳入CI，无公网或付费模型调用。
- 六原站首次5成功域名，GNU失败重试仍失败；补充中文Kubernetes同域实际成功，共8下载尝试、6成功页、24解析复核行：10correct/4partial/2noise/2no_content/6blocked。逐项对照本轮原HTML/raw/text/标题/元数据与缺失差异，不沿用B03质量标签；固定六fixture18内容与原已签G2一致但没有新伪造签认。
- 官方DeepSeek Flash普通CLI新的auto闭环：3模型回合、2搜索/2读取、2引用、0未核引用，14534.379ms；实际模型文本与主要论断核对，有中文抽取遗漏和历史说明英文杂词备注，不声称输出完美或通用准确率。
- GNU下载本轮NETWORK_ERROR，安全实机两轮整体各10/11 FAIL原样保留（GNU正向失败；其它政策/真实sentinel0/真实搜索安全读取PASS）。五其他成功域名满足采样，GNU例外另列B08-GNU-LIVE-01；未关闭TLS，根因尚未定位。
- 实际分阶段耗时、采集进程峰值107452KiB、应用请求后RSS/HWM106260KiB、Docker58.7MiB/CPU0.20%已记录；不是活动CLI峰值或吞吐基准。CI源码a14日志/工件347/347（10.29s）/23步下载核对，后续交付头CI独立读回。
- docs/DEMO_TEST_REPORT.md、reports/B08/validation/记录PASS、FAIL、BLOCKED、NOT_RUN及复现。机器快照保留其生成时状态，正式G5与新增接口用户审核PENDING_USER_SIGNOFF，原G2/G3/G4不改写，不提前进行准确性基准。

## G5 最终用户签认（2026-10-14）

- 用户在收取81815e2最终报告和获解释GNU失败后明确回复“那我签认G5”。新增 `reports/B08/validation/g5-signoff.json` 记录原句、实际记录时刻、范围与限制，绑定27份原公开Git blob和15份本机网页JSON/HTML/模型轨迹SHA，包含B07接口报告与5张脱敏截图。
- 正式G5 PASS，GNU例外获用户接受；GNU自身仍BLOCKED、安全脚本两轮10/11 FAIL与解析器遗漏/回答备注保留，不伪造已修复。原G2/G3/G4与签认前B08 `acceptance.json`/正文复核/机器快照均保留原bytes。
- 签认前交付头push #38564060601 与PR #38564066306均SUCCESS；实际工件347/347、HTTP故障3/3、24步骤核对。此次签认记录不重新调用付费模型或公网采样。
- 更新当前索引/报告/README，批准关卡后将已验收B07/B08按原PR依次合入main，新增main push CI触发用于核对最终主分支。准确性基准保持未启动，不将G5等同准确率达标。

## E00-R｜外部搜索与 Agent 基准来源可用性研究（2026-10-14）

- **开始全新评测研究阶段，不影响 B00–B08 已验收 G5，也不关闭 B08-GNU-LIVE-01**。从当前 main `a1db44e960e5970b1d329ed5024151142d477056` 创建独立分支 `research/e00-benchmark-availability-20261014`。
- 已核查 Exa Search Benchmarks、SealQA、FreshQA、LiveNewsBench、CRAG、OpenBenchmarks、FRAMES、DeepSearchQA、BrowseComp、BrowseComp-Plus、Artificial Analysis，及 Promptfoo/EvalScope/Ragas 的官方页面、数据卡/README、公开性、已知许可、版本/评分和接入成本，重点区分真实联网搜索与固定语料 RAG。
- 新增 `docs/evals/00_BENCHMARK_AVAILABILITY_AUDIT_20261014.md`（逐项可用性与适配风险）、`docs/evals/BENCHMARK_SOURCE_REGISTRY.json`（来源机器登记）、`docs/evals/01_EVAL_ADOPTION_AND_SCREENING_PROTOCOL.md`（E00-R/A1/A2/S 与 E01–E03 关卡、下轮筛题合同）。
- 首轮建议：EXA 论文检索/技术文档抽取、SealQA、中文自建金标优先；CRAG/FreshQA/LiveNewsBench 在有日期和限制的前提下第二轮探测；DeepSearchQA、FRAMES、BrowseComp 延后，BrowseComp-Plus 需新增固定语料索引。Artificial Analysis/OpenBenchmarks 私有排行榜只做方法参考。
- **执行真实性：本轮仅完成官方来源网页级研究与仓库文档提交**；尚未在目标 Ubuntu 下载/校验完整数据、运行评分器、调用付费模型或筛选任何问题。`questions_selected=0`，各外部来源 `local_probe=NOT_RUN`。这不是 benchmark PASS。
- 统一索引新增 `E00-A1-UPSTREAM-01`、`E00-SCREEN-01`、`E00-JUDGE-01`，待后续逐项真实核验。公开仓库禁止上传解密 Gold、未经批准的完整原网页及真实 API Key；Git 忽略规则同步强化。
