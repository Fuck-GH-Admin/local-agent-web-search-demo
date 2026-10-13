# 实施与验收台账

执行依据：`DEMO_EXECUTION_PLAN.md`；起点 `e90892ed9d278978fff3a583f96ec271d9c45ea5`。
工作分支：`b00/environment-baseline`。本轮范围为 B00/G0。

| 批次 | 状态 | 证据与说明 |
| --- | --- | --- |
| B00 | PASS | 本机技术验收与独立重建通过；用户人工阶段签认 NOT_RUN |
| B01 | NOT_RUN | 未执行，等待后续指令和阶段确认 |
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

### 本批交付五件

1. 变更：环境/依赖、上游版本锁、共享模型、固定样本、CLI 骨架、环境检查与重建脚本、32 项离线测试。实现提交：`eb8c626c582ec515aa0cb96060d77f33aa4e6a5c`；证据与本条台账更新在后续本地证据提交中保存（最终 SHA 可由 `git log -1` 获取）。
2. 命令与结果：`uv sync --locked --all-extras`、`.venv/bin/python scripts/verify_b00.py`、`bash scripts/rebuild_environment.sh .venv-rebuild` 全部 PASS；详见 README。
3. 自动化证据：`reports/B00/environment.json`、`test-summary.txt`、`pytest.xml`、`checks.json`、`upstream-clones.json`、`rebuild-summary.txt`、`rebuild-check.json`、`rebuild-environment.json`、`rebuild-verification.txt`、`hygiene.json`、`acceptance.json`。实现提交后再次核验两个环境，测试均为 32 PASS。
4. 人工任务：复核 `B00_ACCEPTANCE.md` 和报告，再决定后续 G0 阶段签认；无 B00 技术问题阻断。其余批次和实机业务测试均未执行。
5. 台账与结论：本文件及 `B00_ACCEPTANCE.md`；B00 本机技术通过，后续保持 NOT_RUN。

## 变更记录

没有修改验收标准或删除主字段。增加 ErrorDetail/SearchItem/ToolCall 辅助模型及 encoding/html_path；计时统一为毫秒，未执行结果保持 null。
源码复核后选用实际可安装的 OpenAI SDK 3.29.0（HTTPX2 传输），同时保留 HTTPX 0.28.1 作为本项目获取层；这是版本选择，没有调整任务范围。
