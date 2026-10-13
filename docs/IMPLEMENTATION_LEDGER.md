# 实施与验收台账

执行依据：`DEMO_EXECUTION_PLAN.md`；起点 `e90892ed9d278978fff3a583f96ec271d9c45ea5`。
B00/B01 与 B02 初始自检已合入 main；当前 B03 工作分支为 `feat/b03-parser-comparison`，本次另合入 B02 完整补验提交 `64008dbf3549ca8451317197e8a9ebb381af1c16`。另见 [跨批次待补验索引](./OPEN_VALIDATION_INDEX.md)（每批必读）。

| 批次 | 状态 | 证据与说明 |
| --- | --- | --- |
| B00 | PASS | 本机技术验收与独立重建通过；用户已明确授权进入 B01 |
| B01 | PASS / G1 LIVE_PASS | 55/55 本机离线通过；真实中英文搜索均 HTTP 200 / 5 条；Docker 状态、固定镜像 digest、初始失败与上游错误均有证据 |
| B02 | PASS / LIVE_PASS | 本机 91/91 通过，含 36 项获取层用例；两个公网 HTML 均 HTTP 200，保存 bytes 的 SHA-256 一致 |
| B03 | PASS / G2 PASS | 本机 109/109（18 项 B03）通过；18 组内容复核完整，14 correct / 1 noise / 3 no_content；用户明确签认，完整性检查退出 0 |
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
