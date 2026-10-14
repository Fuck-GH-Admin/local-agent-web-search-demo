# 未通过 / 待补验事项索引（跨批次）

> 本文件不是缺陷清单，而是**任何尚未取得 PASS 证据的验收、人工检查、非阻断实验的统一入口**。每批开始和结束均需阅读、更新。凡未执行不得写 PASS；关闭必须附报告路径和时间。

| ID | 来源 | 状态 | 是否阻断下批 | 应做什么、怎么做 | 证据与回填位置 |
|---|---|---|---|---|---|
| **B02-LIVE-01** | B02 网页获取 | **PASS（2026-10-14）** | 否（B02 计划定义为可选） | 在目标 Linux 宿主机运行 `uv run --locked python scripts/b02-live-smoke.py`；检查实际公网 HTML 下载、代理继承、HTTP 状态、编码与耗时。注意 SearXNG 容器的 host 代理不会自动作用到 Python 进程。 | 已实测 example.org、Python asyncio 文档均 HTTP 200；保存 bytes SHA 一致。`reports/B02/live-smoke.json`、`saved-html-checks.json`，`docs/B02_ACCEPTANCE.md`；交付提交 `64008dbf3549ca8451317197e8a9ebb381af1c16`。 |
| **B03-G2-01** | B03 三解析器 | **PASS（2026-10-14 用户签认）** | 否（原为 B04 前阻断项；G2 已通过） | 先下载 [B03 CI 对比报告工件](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38429154060/artifacts/11830362359)，或在锁定环境执行 `uv run --locked python scripts/b03-compare-fixtures.py`。对 18 组结果逐项检查，按实际质量填写 `reports/B03/manual-review.json` 全部理由、设 human_review_status=REVIEWED，随后 `uv run --locked python scripts/b03-g2-check.py` 检查完整性；再人工签认，不得拿自动检查替代质量判断。 | 2026-10-14 18 行质量及理由完整（14 correct / 1 noise / 3 no_content），用户已明确签认，human_review_status=REVIEWED；工作表检查退出 0。`reports/B03/g2-signoff.json`、`quality-review.md`、`parser-comparison.json`、`manual-review.json`、`g2-check.txt`，`docs/B03_ACCEPTANCE.md`；签认报告提交 `83ccfae346956e7d9149fe1e190418b10047771d`，解析实测提交 `e979b6fabd5544cd50b4134235c179bed035917e`。 |
| **B03-LIVE-02** | B03 质量外推 | **NOT_RUN** | 否（B03 原计划 G2 重点为固定样本） | 选部分真实网页采集 HTML，独立比较三解析器输出和质量；与 B08 至少 5 个真实网站的要求衔接，不能将固定样本表现当作全网成功率。 | `reports/B08/` 或专项真实网页比较记录 |
| **B04-LIVE-01** | B04 统一读取真实公网 URL | **NOT_RUN** | 否（B04 验收规定为固定输入自动化自检） | 在实际 Ubuntu 上通过 CLI `read` 分别读取至少一篇完整文章及一页文档，保留 fetch、三个 parser、被选正文和可解释决策；不得把 CI loopback 结果算成公网网页读取。可与 B08 多页面真实质量对比一起补验。 | `reports/B04/` 专项 live JSON，`docs/B04_ACCEPTANCE.md`；之后更新本索引 |
| **B06-URL-SEC-01** | B06/B07 模型控制网页读取 | **FUTURE** | **是（Agent 真实联调前）** | 模型工具 `read_webpage` 必须对用户/网页诱导的 URL 做 SSRF 访问策略检查，默认拒绝 localhost、内网/链路本地地址、云元数据端点与非 HTTP(S)，并对跳转后地址重新校验；测试 DNS 解析、跳转绕过与端口情形。仅 B04 本地 CLI 自测允许显式 loopback fixture，不自动授予模型此权限。 | `docs/B06_ACCEPTANCE.md` / `docs/B07_ACCEPTANCE.md`；未来回归与安全测试报告 |
| **B05-G3-01** | B05 双入口 | **FUTURE** | 是（B05 完成后） | CLI 与 WebUI 同样 fixture 的结果一致性及 WebUI 人工操作验收。 | `docs/DEMO_EXECUTION_PLAN.md` |
| **B07-G4-01** | B07 实际 Agent | **FUTURE** | 是（B07 完成后） | 真实模型执行 search_web → read_webpage → answer；核对来源和工具调用 trace。 | `docs/DEMO_EXECUTION_PLAN.md` |

## 状态规则

- `NOT_RUN`：当前应做但还未执行；`FUTURE`：对应批次未到；`BLOCKED`：已尝试但受阻；`FAIL`：已执行且未达标；`PASS`：核验实际报告符合标准。
- **不能将 CI 离线 PASS 等同于目标主机真实联网 PASS**。G2 人工正文质量不得从锚点匹配自动赋值。
- 每次开发交接必须回看本表，将变更理由、测试时间、commit SHA 与证据路径补充进 `docs/IMPLEMENTATION_LEDGER.md`。
- 此文件中历史待补事项**不会因后续进入新批次而自动消失**；完成后改为 `PASS` 并保留记录，不删行。
