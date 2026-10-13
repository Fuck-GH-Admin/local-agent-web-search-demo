# B00–B08 实施与验收台账

> 2026-10-13 创建。状态来源必须是实际执行证据，不能以计划代替测试。

## 批次状态

| 批次 | 状态 | 验收 | 备注 |
|---|---|---|---|
| B00 | IN_PROGRESS / BLOCKED_LOCAL | G0 NOT_PASS | 骨架已建，离线 pytest 10/10 PASS；GitHub DNS 不可用，无法 clone 上游或完整安装 |
| B01 | NOT_RUN | G1 NOT_RUN | 未开始 |
| B02 | NOT_RUN | 批次自检 NOT_RUN | 未开始 |
| B03 | NOT_RUN | G2 NOT_RUN | 未开始 |
| B04 | NOT_RUN | 批次自检 NOT_RUN | 未开始 |
| B05 | NOT_RUN | G3 NOT_RUN | 未开始 |
| B06 | NOT_RUN | 批次自检 NOT_RUN | 未开始 |
| B07 | NOT_RUN | G4 NOT_RUN | 未开始 |
| B08 | NOT_RUN | G5 NOT_RUN | 未开始 |

## 本机调试协作补充（2026-10-13）

- 已提供 [本机开发环境、诊断与日志回传说明](./LOCAL_DEV_ENVIRONMENT.md)。
- 新增 `scripts/local-diagnostics.py`：只读环境检查，按需 `--network`；本地报告写在被忽略的 `reports/local/preflight.json`，不会自动上传。
- 加强 `scripts/b00-g0-check.py`：除包版本外逐一真实导入，还执行 `python -m pip check`。新逻辑**尚待目标本机执行验证**，不改变此前云端容器的 10/10 测试结果。
- GitHub 连接器不能替代本机执行；应由用户本机产生、审阅并选择性提交 JSON 证据，之后才能更新 G0。

## B00 交付及阻塞

- 工作分支：`feat/b00-foundation`（未合并 main）。
- 本批范围：`.gitignore`、`pyproject.toml`、`.env.example`、配置/数据 Schema、占位命令、离线 fixture、pytest、环境记录以及 `scripts/clone-upstream.sh` / `scripts/b00-g0-check.py`。
- 当前容器离线执行：`pip install --no-deps --no-build-isolation -e .` 成功；`python -m pytest -q` = **10 passed**；`python -m local_search_demo doctor` 成功；`python -m local_search_demo search test` 返回 `not_implemented`，退出码 **3**，符合 B00 占位约定。此安装**未解析全部依赖**，不得视为完整安装。
- 上游仓库：6 个 clone 均待执行，不能记录不存在的 SHA。
- 完整依赖锁文件：待目标机器成功安装后，记录已解析的所有直接与传递依赖版本。`pyproject.toml` 范围声明不是 lock file。
- SearXNG Docker：当前容器未检测到 docker 可执行文件；部署属于 B01，不在 B00 假装完成。
- 检验命令与结果：见 `reports/B00/verification.json` 和 `reports/B00/`；G0 补验用 `python scripts/b00-g0-check.py`，报告输出 `reports/B00/g0-local-check.json`，仅证明实际执行的部分。
- G0 判定：**NOT_PASS / BLOCKED_LOCAL**。不可开始需要真实上游依赖的验收；允许继续编写可离线运行的独立工作。

## 本机补验清单（G0 必须完成）

1. 网络可用的本地工作站运行 `bash scripts/clone-upstream.sh`，clone 六份上游仓库到 `.references/upstream/`，逐项执行 `git -C <path> rev-parse HEAD` 并记录。
2. `python -m venv .venv`、激活、`python -m pip install -e '.[dev]'`，保存最终 lock/版本清单（可选 uv pip compile / pip freeze），执行 `python -m local_search_demo doctor`。
3. `python scripts/b00-g0-check.py`（自动复验 pytest、doctor、CLI、clone SHA 与依赖；报告应为 PASS），确认 `python -m local_search_demo search test` 明确返回 NOT_IMPLEMENTED/退出码 3。
4. 更新本台账：机器/OS/Python/包版本、实际 commit、命令、退出码、证据路径和 G0 是否 PASS。

## 后续更新模板

- Batch：`Bxx`
- Commit：`<sha>`
- Command：`<exact command>`
- Result：`PASS | FAIL | BLOCKED | NOT_RUN | WAIVED`
- Evidence：`reports/Bxx/...`
- Human check：`<steps and actual result>`
- Open issues：`<issue IDs and blocking judgement>`
