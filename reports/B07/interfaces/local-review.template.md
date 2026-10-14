# B07-INTERFACES-01 目标机界面验收（待执行模板）

**状态：NOT_RUN**。本模板不是自动验收证据。请本机执行后另存 `local-review.md`；截图和真实模型输出默认不提交公共/共享仓库，先人工脱敏。

版本：
- commit：
- Ubuntu / 浏览器版本：
- 测试时间、时区：
- 本地 SearXNG 可用：是/否
- 本地模型配置存在（不要填入具体 Key）：是/否
- WebUI 监听地址：127.0.0.1:8765

## 操作结果

| 项目 | 预期 | 实际状态（PASS/FAIL/BLOCKED） | 证据或问题 |
|---|---|---|---|
| 普通 CLI agent 无凭据 | BLOCKED，退出 2、不联网 | NOT_RUN | |
| 普通 CLI agent 无工具控制题 | 模型真实回答、trace 正常 | NOT_RUN | |
| 普通 CLI agent auto 搜索→安全读取 | 两种工具与最终引用可核验 | NOT_RUN | |
| API 缺少模型凭据 | HTTP 503、不暴露 Key | NOT_RUN | |
| API 无 server 读取开关 | 即使请求勾选也返回 403 | NOT_RUN | |
| API 跨 Origin | HTTP 403，无付费调用 | NOT_RUN | |
| UI Agent 页签、模型答复 | 显示真实内容及错误 | NOT_RUN | |
| UI 工具轨迹 | 调用 ID、参数、引用、耗时可看 | NOT_RUN | |
| UI 窄视口与失败恢复 | 正常响应、无 JS 报错 | NOT_RUN | |
| 私网 URL / 未在本次搜索中出现 URL | 均阻断；不发请求 | NOT_RUN | |
| 相同 Core 接口对照 | CLI/API 结果结构与 G4 轨迹可比 | NOT_RUN | |
| 回归 CI | 运行成功、测试数量核实 | NOT_RUN | |

## 结论

- B07-INTERFACES-01：**NOT_RUN**
- G4 既有用户签认：PASS（本表不重签）
- 未完成/阻断：
- 复核者：
- 提交对应证据（脱敏）：
- 更新 `docs/OPEN_VALIDATION_INDEX.md` 和 `docs/IMPLEMENTATION_LEDGER.md`：否
