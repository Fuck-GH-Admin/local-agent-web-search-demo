# B08 — 整体验收、性能与质量观察（执行合同）

**状态：PREPARED / G5 NOT_RUN**。此开发分支从 B07 接口工作分支派生，依赖 `B07-INTERFACES-01` 完成本机浏览器实测；目前不能合入 main，也不能把已有 G4 签认当作 G5 通过。

## 交付

- `scripts/b08-validation.py`：严格区分 `OFFLINE_ONLY`（默认）与显式 `--live`。离线会运行完整 pytest、B04 CLI、B05 parity、B06 工具轨迹、B07 普通入口 SDK 回环测试并采集实际退出码与时长。
- 显式 `--live` 才会重新抓取 B03 已研究的六个独立网站，每站调用一次 B04 下载与三个解析器；记录当前请求时间、HTTP、下载字节、各解析器状态/字符数/耗时、文本与原始输出 SHA、被选结果。**不会沿用旧 B03 的质量标签**。
- `--save-private` 附加将完整网页和解析结果写进本机 Git 忽略的 `reports/B08/raw/`，0600 权限；没有明确 `--live` 时拒绝。
- `reports/B08/observations.json` 只是机器观测值；每行 `human_quality_review=NOT_RUN`，不能自动按锚点判 correct。
- `docs/DEMO_TEST_REPORT.md` 是最终报告的结构草案，人工检查与实机性能数据未补齐前不得标 PASS。

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

- [ ] B07-INTERFACES-01 本机真实 CLI/API/WebUI Agent 验收 PASS，跨批次索引更新。
- [ ] B00–B07 的验收索引没有未解释的 FAIL/BLOCKED；例外必须明确描述并保留。
- [ ] 完整 pytest、B04/B05/B06/B07 回归真实 PASS。
- [ ] SearXNG 中英文真实搜索和上游错误分类重新观察，不声明全部引擎健康。
- [ ] 至少五个**不同域名**的真实网页，三解析器结果和人工理由齐全（包含正确、部分、噪声、空正文、拒绝/超时样例）。
- [ ] 至少一次真实 Agent search→safe read→answer 重复运行，引用 URL 能在本次成功读取的网页中找到。
- [ ] 搜索/下载/三解析器/模型/总耗时与 Docker/SearXNG 常驻内存、Python 进程内存真实记录；不对性能设置无证据阈值。
- [ ] `docs/DEMO_TEST_REPORT.md` 含所有 PASS、FAIL、BLOCKED、NOT_RUN、复现命令、限制、后续优化候选，不预设全网成功率。
- [ ] 全部截图和原始文本脱敏；模型 Key 永不上传。

本批不会改变已签认的 G2/G3/G4 原始证据。**最终 G5 需要人工审核报告并明确签认**，不能由自动 JSON 总结自封通过。
