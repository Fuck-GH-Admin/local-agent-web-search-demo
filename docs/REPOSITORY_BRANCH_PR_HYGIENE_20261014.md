# 仓库分支与 PR 整理记录（2026-10-14）

**范围：** `Fuck-GH-Admin/local-agent-web-search-demo`。本次将 GitHub 真实远端分支逐一与 `main` 比较，并核实 PR #1–#12 的状态。此文为可复核的整理报告，**不伪称已经删除远端分支**。

## 1. 当前清单

- 整理前 **18 个远端分支**，含 `main`；`main` 在盘点时 HEAD 为 `a1db44e960e5970b1d329ed5024151142d477056`。
- PR **#1–#12** 共 12 个：**唯一打开的是 Draft #12**（`research/e00-benchmark-availability-20261014`）；#1–#6、#9–#11 均 merged；#7、#8 closed but NOT merged（旧 B07 方案，被 #9 正式实现取代）。
- `main` 的 B00–B08 G5 已签收；`B08-GNU-LIVE-01` 已接受的独立 BLOCKED 例外保留。**任何分支清理不能篡改已签收证据。**
- `research/e00-benchmark-availability-20261014` 相对盘点时 main **ahead 7, behind 0**，是真正进行中的研究分支，**不能删除**。本次清理 commit 会使其自然落后新 main，后续 PR 合并前正常同步即可。

## 2. 安全可删（12 个：HEAD 已被 main 完整包含）

以下十二个比较结果均为 `status=behind, ahead_by=0`；从提交图上已经是主分支祖先，删除分支引用不会丢代码或 Git 历史里的原始提交。

| 分支 | 整理前落后主分支提交数 | 对应阶段 |
|---|---:|---|
| `b00/environment-baseline` | 244 | B00 早期环境基线 |
| `feat/b01-searxng-search` | 216 | B01 / PR #1 merged |
| `feat/b02-httpx-fetch` | 196 | B02 / PR #2 merged |
| `feat/b03-parser-comparison` | 156 | B03 / PR #3 merged |
| `feat/b04-core-cli` | 136 | B04 / PR #4 merged |
| `feat/b05-fastapi-webui` | 102 | B05 / PR #5 merged |
| `feat/b06-agent-tool-loop` | 64 | B06 / PR #6 merged |
| `feat/b06-readiness-audit` | 64 | B06 实机收尾 |
| `feat/b07-agent-interfaces` | 20 | B07 / PR #10 merged |
| `feat/b07-real-model` | 48 | B07 G4 / PR #9 merged |
| `feat/b08-final-validation` | 2 | B08 / PR #11 merged |
| `feat/live-quality-url-security` | 88 | 早期真实网页/URL 安全修复 |

**执行方式**：`scripts/prune_merged_branches.sh` 默认只打印预检结果，必须显式 `CONFIRM_DELETE_MERGED_BRANCHES=YES` 才会远端删除。它会重新拉取远端 refs、核对 origin 仓库名称、`merge-base --is-ancestor` 验证该提交仍在主分支中，先创建并读回校验与旧分支**同名、同 SHA 的轻量 Git 标签**保存历史版本，再使用指向预检 SHA 的 lease 防止误删被他人更新的分支。若远端或本地存在指向不同提交的同名标签，自动保留该分支；如果分支有独有提交，也自动保留。无需运行 `git branch -D`、无需 `git push --force` 覆盖历史。

```bash
# 在该仓库的本地 Git 工作树里
git fetch origin
bash scripts/prune_merged_branches.sh

# 检查 12 项名单确实都是 SAFE TO ARCHIVE 后，再有意执行
CONFIRM_DELETE_MERGED_BRANCHES=YES bash scripts/prune_merged_branches.sh
```

**远端删除执行状态：NOT_RUN。** 仅提供单一正式入口 `scripts/prune_merged_branches.sh`；重复的维护脚本已移除。 当前可用 GitHub 连接器支持比较、编辑、PR 管理，但不提供删除 Git 分支 ref 的写操作；因此不能声称已经远端删除。该步骤由具有 push/delete 权限的本地 Git 凭据执行，或使用 GitHub 网页 Branches → Delete branch。脚本属于可实际运行的交付，不是执行日志。

## 3. 暂留的四个有独有提交的分支（不要批量删除）

| 分支 | 与整理前 main 的关系 | 原因与下一决策 |
|---|---|---|
| `codex/miku-small-runner-20261014` | **ahead 2, behind 0** | `.github/workflows/b01-offline.yml` 将 runner 标签从 `[self-hosted, linux, x64]` 改为包含 `local-high-resource`。它是**尚未并入主分支的 CI 机器选择变更**，可能会让未打该标签的 Runner 无法接单；应核对目标 Runner 标签后单独决定是否吸收，不自动合并或删除。 |
| `feat/b00-foundation` | **diverged, ahead 48, behind 247** | 早期基础结构的独立开发历史；虽然很多功能后来实现于 main，但这 48 个独有 commit 不可简单等同于“已经合并”。保留直到核对补丁/历史价值。 |
| `feat/b07-real-model-prep` | **diverged, ahead 7, behind 69** | 被 B07 正式 PR #9 取代的旧方案，原 PR #7 已 closed / not merged；逻辑被替代不等于 SHA 提交图上已包含。保留作历史，审阅后再决定删除。 |
| `feat/b07-real-model-integration` | **diverged, ahead 15, behind 64** | 被 B07 正式 PR #9 取代的另一旧方案，PR #8 已 closed / not merged；保留独有历史，审阅后再决定删除。 |

不建议把这四个分支快进到 `main` 或为了合并显示“全绿”而强行 merge。它们不是当前工作线路，且其中 Runner 增加了机器标签约束。

## 4. PR 整理结果

| PR | 状态 | 动作 |
|---|---|---|
| #1–#6 | MERGED | 保留历史关闭状态；不重复合并 |
| #7 / #8 | CLOSED, NOT MERGED | 旧 B07 草案，正式实施由 #9 代替；不 reopen |
| #9–#11 | MERGED | 保留 G4/G5 审批与验收记录 |
| **#12** | **OPEN / DRAFT，documentation 标签** | 唯一在做的 **E00 基准可用性研究**；不额外建“清理 PR”干扰入口，保留待 review |

整理前 GitHub 的 PR 列表事实上已经相当干净，只是 branches 列表还留下了大量已结束分支。

## 5. 已直接处理的 CI 噪声

`.github/workflows/b01-offline.yml` 已从只读历史分支和多余的堆叠 PR base 中移除监听，收敛为：

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

这不会删除测试作业、验收工件或旧 PR；仅减少历史分支触发重复耗时 CI。真正的 PR #12 目标仍是 `main`，会继续正常触发回归。该 workflow 变更已直接写入主分支，需以新 CI 的实际运行结果检验。

## 6. 后续仓库约定

1. **只维护两条活动线路：** `main`（已签收稳定版）与 `research/e00-benchmark-availability-20261014`（研究阶段 Draft #12）。E00 后续 A1/A2 若从现有分支继续，要先核实 base 和状态；不再为一个阶段制造多个旧草稿。
2. 分支对应阶段通过 CI、实机验收与用户签认后，合并并删除远端功能分支；PR 记录、证据文档、Git SHA 保留。
3. 如工作尚未通过人工验收，保持 Draft 并在 OPEN_VALIDATION_INDEX 中记录阻断，**不要用一个 PR 伪装成已验收**。
4. `main` 工作流只监听 `main` 和 PR to main；不要为每个已结束工作流永久添加 `push.branches` 监听项。
5. 定期运行 `git branch -r --merged origin/main` 核对归档分支；绝不直接将 `--no-merged` 分支批量删除。

## 7. 完成度（本轮）

| 工作 | 状态 |
|---|---|
| 完整分支和 PR 云端盘点 | PASS |
| 12 分支祖先关系逐项验证 | PASS（检查时刻） |
| 唯一活跃 PR 确认 | PASS |
| 减少过时 CI 触发 | 已提交主分支，CI 结果待核查 |
| 创建带 SHA 锁、历史同名标签备份和 dry-run 的远端清理脚本 | PASS（脚本已提交，用户本机尚未执行） |
| 12 个分支真正从 GitHub 远端删除 | **NOT_RUN / 当前连接器不支持删除分支引用** |
| 4 个有独有提交的分支留存和备注 | PASS（保留，未强删） |
