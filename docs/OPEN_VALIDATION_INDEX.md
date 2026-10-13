# 未通过 / 待补验事项索引（跨批次）

> 本文件不是缺陷清单，而是**任何尚未取得 PASS 证据的验收、人工检查、非阻断实验的统一入口**。每批开始和结束均需阅读、更新。凡未执行不得写 PASS；关闭必须附报告路径和时间。

| ID | 来源 | 状态 | 是否阻断下批 | 应做什么、怎么做 | 证据与回填位置 |
|---|---|---|---|---|---|
| **B02-LIVE-01** | B02 网页获取 | **NOT_RUN** | 否（B02 计划定义为可选） | 在目标 Linux 宿主机运行 `uv run --locked python scripts/b02-live-smoke.py`；检查实际公网 HTML 下载、代理继承、HTTP 状态、编码与耗时。注意 SearXNG 容器的 host 代理不会自动作用到 Python 进程。 | `reports/B02/live-smoke.json`，`docs/B02_ACCEPTANCE.md` |
| **B03-G2-01** | B03 三解析器 | **NOT_RUN（自动 93/93 通过；人工待办）** | **是（进入 B04 完整验收前）** | 先下载 [B03 CI 对比报告工件](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38429154060/artifacts/11830362359)，或在锁定环境执行 `uv run --locked python scripts/b03-compare-fixtures.py`。对 18 组结果逐项检查，按实际质量填写 `reports/B03/manual-review.json` 全部理由、设 human_review_status=REVIEWED，随后 `uv run --locked python scripts/b03-g2-check.py` 检查完整性；再人工签认，不得拿自动检查替代质量判断。 | `reports/B03/parser-comparison.json`、`reports/B03/manual-review.json`、`docs/B03_ACCEPTANCE.md` |
| **B03-LIVE-02** | B03 质量外推 | **NOT_RUN** | 否（B03 原计划 G2 重点为固定样本） | 选部分真实网页采集 HTML，独立比较三解析器输出和质量；与 B08 至少 5 个真实网站的要求衔接，不能将固定样本表现当作全网成功率。 | `reports/B08/` 或专项真实网页比较记录 |
| **B05-G3-01** | B05 双入口 | **FUTURE** | 是（B05 完成后） | CLI 与 WebUI 同样 fixture 的结果一致性及 WebUI 人工操作验收。 | `docs/DEMO_EXECUTION_PLAN.md` |
| **B07-G4-01** | B07 实际 Agent | **FUTURE** | 是（B07 完成后） | 真实模型执行 search_web → read_webpage → answer；核对来源和工具调用 trace。 | `docs/DEMO_EXECUTION_PLAN.md` |

## 状态规则

- `NOT_RUN`：当前应做但还未执行；`FUTURE`：对应批次未到；`BLOCKED`：已尝试但受阻；`FAIL`：已执行且未达标；`PASS`：核验实际报告符合标准。
- **不能将 CI 离线 PASS 等同于目标主机真实联网 PASS**。G2 人工正文质量不得从锚点匹配自动赋值。
- 每次开发交接必须回看本表，将变更理由、测试时间、commit SHA 与证据路径补充进 `docs/IMPLEMENTATION_LEDGER.md`。
- 此文件中历史待补事项**不会因后续进入新批次而自动消失**；完成后改为 `PASS` 并保留记录，不删行。
