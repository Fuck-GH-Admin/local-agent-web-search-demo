# B07 DeepSeek 实机复核（待用户签认）

2026-10-14；官方端点；模型 deepseek-flash；Chat Completions；thinking=disabled。
实现提交：d087d07c4de8cd19ad5fc4250779ecbfc15801a3。

| 实机场景 | API 轮次 | 成功搜索 | 成功读取 | 引用 | 总耗时 ms |
|---|---:|---:|---:|---:|---:|
| no-tool-control | 1 | 0 | 0 | 0 | 1312.646 |
| forced-tool-path | 2 | 1 | 0 | 0 | 3210.378 |
| agent-live-initial | 3 | 2 | 1 | 1 | 10482.152 |
| agent-live-observability | 3 | 1 | 1 | 1 | 5395.504 |
| agent-live | 3 | 1 | 2 | 1 | 7269.597 |

三次 auto 联网轨迹均完成 search → safe read → answer；强制场景只用于检查通路。最终提交复验读取两页，均 HTTP 200，六个解析器结果均 PASS；引用一条，未核引用为零。

Codex 已检查五份轨迹的调用 ID、参数、来源集合、安全连接记录、错误和回答：三个联网回答的主要论断在短概览页正文中逐项可找到；第二个长页面给模型的正文为 6000 字符截断，未以截断部分证明额外论断。无工具控制题结果正确。

SearXNG 返回了可用结果，同时保留 Brave 限流。未宣称所有搜索上游正常。

本机离线回归：314/314；B04 3/3、B05 5/5、B06 四轨迹 PASS。共实际发出 12 次 Chat Completions 请求，输入 17408 tokens，输出 1133 tokens；没有重试或后台付费任务。

正式 G4：PENDING_USER_SIGNOFF。原始回答/URL/正文只在本机 Git 忽略目录；此公开摘要仅含脱敏结果和原始文件 SHA-256（见 acceptance.json）。普通 CLI agent 与 WebUI/API Agent 仍为占位，单独记入接口待办；不将此报告称为 B07 全部入口完成或 B08 通过。
