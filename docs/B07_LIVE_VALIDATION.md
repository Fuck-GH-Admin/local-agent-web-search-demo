# B07 DeepSeek 真实模型验收记录

2026-10-14 实际核对云端 main `856ca50`、B07 PR #8/#9；两份草稿都尚无真实 API 证据。本次在 PR #9 的 `feat/b07-real-model`、已验收 B06 基线上执行用户授权的官方 DeepSeek 测试。源码提交 `d087d07c4de8cd19ad5fc4250779ecbfc15801a3`，原有 B06 默认关闭与安全传输保持有效。

## 结果

| 实机场景 | 模型回合 | 搜索/读取 | 引用 | 总耗时 ms | 结论 |
|---|---:|---|---:|---:|---|
| auto 无工具控制 | 1 | 0 / 0 | 0 | 1312.646 | 正确回答，DONE |
| required 通路 | 2 | 1 / 0 | 0 | 3210.378 | required → auto，DONE |
| auto 初次完整闭环 | 3 | 2 / 1 | 1 | 10482.152 | DONE |
| auto 增补阶段审计 | 3 | 1 / 1 | 1 | 5395.504 | DONE |
| auto 最终提交复验 | 3 | 1 / 2 | 1 | 7269.597 | DONE |

完整数字、API 响应 ID、执行时间和原始轨迹 SHA-256 见 [acceptance.json](../reports/B07/validation/acceptance.json)。5 个场景共 12 次实际模型请求，不在 CI 注入密钥，不配置自动付费任务。三个 auto 联网轨迹机器初筛均 READY_FOR_HUMAN_REVIEW。

最终复验是模型主动选择 1 次搜索、2 次读取，均来自本次搜索结果；HTTP 200，下载 25,411 / 70,033 bytes，三解析器各自成功。选择 Selectolax，给模型的短页正文完整、长页截断至 6,000 字符。最终一条引用指向本次成功读取的短页。模型轮次、工具参数、call_id、模型/工具/下载/解析耗时与公网连接审计均真实记录，没有追加模型未发出的工具请求。

## 内容与来源检查

Codex 阅读五份原始轨迹：控制答案正确；强制搜索后说明找到结果并按要求结束；三个联网回答所述并发语法、IO 工作负载、并发运行协程、网络 IO/IPC 等论断都由本次读取的短概览正文支持，未出现未核 URL。每次工具读取都属于对应运行的搜索来源集合，调用 ID 独立且有真实本地结果。较长页面被截断的事实保留，不把未提供正文作为证据。

搜索的 Brave 上游存在 too many requests / suspended 错误，其他引擎返回结果，整体搜索 PASS；不称全部上游正常。实际模型 API 未发生拒绝、429、超时或无正文失败；这些路径的离线覆盖仍属于离线证据，不能升级为真实故障实测。

正式用户签认待补。机器初筛和 Codex 内容复核不填写人类用户签名。原始回答/URL/正文只留在本机忽略目录，公开复核摘要 [review.md](../reports/B07/validation/review.md) 与脱敏指标已可供审阅；本机原文对照为 `reports/B07/raw/content-review.md`。

## 实现与回归

- 增加显式 thinking 与每响应 token 上限，保留工具续轮需要的 reasoning_content，不把思考内容放公开 trace。
- required 只作用于首轮工具决定，后续允许 auto 回答。该修复与另一云端草稿的判断一致，保留当前已验收基线。
- SDK 调用记录仅含安全的响应元数据、用量、耗时及错误类型/状态；非正常结束不计 DONE。单独保留 Core 下载/三解析器与安全审计，不加到模型工具结果中。
- 补充阶段日志时曾导致两个既有零参数安全工厂注入测试失败：312 PASS / 2 FAIL。恢复原工厂兼容后全量 314 PASS，前次 JUnit 哈希在公开报告，原文件仅本机 raw/；没有删除失败或放松安全断言。
- 新增 9 个实际 SDK 经 MockTransport 的兼容/隐私/结束测试，加上草稿原有 7 个保护测试，本机 **314 passed in 9.47s**，0 skipped。uv lock/pip/JS 检查通过；B04 3/3、B05 CLI/API 5/5、B06 4/4 通过。
- 源码两轮 CI SUCCESS。实际下载 [#38545299093](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38545299093) 日志及 artifact #11883968497：314 passed in 11.67s，20 步成功，新 9 项与 Core/安全工件确认；见 [ci-source.json](../reports/B07/validation/ci-source.json)。

## 仍需完成

G4 用户签认；普通 CLI/WebUI/API Agent 激活（B07-INTERFACES-01）；B08 完整联调与报告。当前独立 B07 启动器的真实工具链 LIVE_PASS，不标 B07 全部入口完成。其他模型/思考模式/Responses 没有实机证据。
