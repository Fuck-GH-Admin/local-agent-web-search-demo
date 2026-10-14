# B08 — 整体验收、性能与质量观察（执行合同）

**状态：G5 PASS（2026-10-14 用户签认，GNU站点例外保留）**。B07普通接口技术验收已完成，B08的347项回归、五成功域名/24条解析复核、新真实Agent与资源观测均已执行。GNU站点内容blocked与安全脚本整体FAIL例外保留，详见 [最终报告](DEMO_TEST_REPORT.md)。用户在获GNU失败解释后明确回复“那我签认G5”，正式G5签认已记录，覆盖本轮新B07接口与B08报告；[G5签认记录](../reports/B08/validation/g5-signoff.json)绑定已交付81815e2与27份公开原Git blob及15份本机原证据。

## 交付

- `scripts/b08-validation.py`：严格区分 `OFFLINE_ONLY`（默认）与显式 `--live`。离线会运行完整 pytest、B04 CLI、B05 parity、B06 工具轨迹、B07 普通入口 SDK 回环测试并采集实际退出码与时长。
- 显式 `--live` 才会重新抓取 B03 已研究的六个独立网站，每站调用一次 B04 下载与三个解析器；记录当前请求时间、HTTP、下载字节、各解析器状态/字符数/耗时、文本与原始输出 SHA、被选结果。**不会沿用旧 B03 的质量标签**。
- `--save-private` 附加将完整网页和解析结果写进本机 Git 忽略的 `reports/B08/raw/`，0600 权限；没有明确 `--live` 时拒绝。
- `reports/B08/observations.json` 只是机器观测值；每行 `human_quality_review=NOT_RUN`，不能自动按锚点判 correct。
- `docs/DEMO_TEST_REPORT.md` 已补齐本轮实际结果、正文复核、故障和资源观察；技术记录不等于用户签认。

## 目标 Ubuntu 执行（两阶段）

```bash
git fetch origin
git switch feat/b08-final-validation
uv sync --locked --all-extras

# 零额外公网网页和零模型费用；跑离线与本地 HTTP fixture
uv run --locked python scripts/b08-validation.py

# 仅在你确认有权限请求这些公网网站时，执行六站实时下载
uv run --locked python scripts/b08-validation.py --live --save-private
```

真实模型 G4 已签收，但 G5 仍须单独**重新执行**一次真实 Agent 端到端，并记录当前模型服务、工具调用、引用和性能；该动作必须由本机明确执行，脚本不会偷偷调用付费模型。

## G5 验收核对

- [x] B07-INTERFACES-01 本机真实 CLI/API/WebUI Agent 验收 PASS，跨批次索引更新。
- [x] B00–B07 的验收索引没有未解释的 FAIL/BLOCKED；例外必须明确描述并保留。
- [x] 完整 pytest、B04/B05/B06/B07 回归真实 PASS。
- [x] SearXNG 中英文真实搜索和上游错误分类重新观察，不声明全部引擎健康。
- [x] 至少五个**不同域名**的真实网页，三解析器结果和人工理由齐全（包含正确、部分、噪声、空正文、拒绝/超时样例）。
- [x] 至少一次真实 Agent search→safe read→answer 重复运行，引用 URL 能在本次成功读取的网页中找到。
- [x] 搜索/下载/三解析器/模型/总耗时与 Docker/SearXNG 常驻内存、Python 进程内存真实记录；不对性能设置无证据阈值。
- [x] `docs/DEMO_TEST_REPORT.md` 含所有 PASS、FAIL、BLOCKED、NOT_RUN、复现命令、限制、后续优化候选，不预设全网成功率。
- [x] 公开截图捕获时脱敏；原始文本不上传，公开指标与哈希经敏感信息检查；模型Key永不上传。
- [x] 用户审核本报告、新B07接口与GNU例外，明确签认最终G5（“那我签认G5”）。

本轮已核对并保留已签认的G2/G3/G4原始证据。机器 `observations.json` 保留生成时NOT_RUN，当前技术结果以 `reports/B08/validation/` 和最终报告为准；当前正式用户签认以 `g5-signoff.json` 为准，原快照不改写。**最终 G5 需要人工审核报告并明确签认**，不能由自动 JSON 总结自封通过。
