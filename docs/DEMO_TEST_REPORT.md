# Local Agent Web Search Demo — 最终测试报告

<escape>状态：DRAFT / B08 G5 NOT_RUN</escape>

## 一、实验范围与环境

项目：本地 SearXNG + HTTPX + Trafilatura / readability-lxml / Selectolax + 可配置 OpenAI 兼容模型；CLI + WebUI 共享 Core。

已记录历史基线：B00–B06 PASS，B07 独立模型 G4 用户签认 PASS。普通 Agent CLI/API/WebUI 接入属于 `B07-INTERFACES-01`，本报告撰写时实机验收未完成。

待补：本轮测试提交 SHA、运行时刻、Ubuntu/Python/uv、镜像 digest、模型名称/模式（不能含 Key）、代理/直连方式。

## 二、测试项目与实际执行结果

| 测试 | 本轮执行状态 | 证据 |
|---|---|---|
| 完整 pytest | NOT_RUN | `reports/B08/observations.json` |
| CLI 搜索/读取、API 对照 | NOT_RUN | 同上 |
| B07 普通 Agent 入口三端 | NOT_RUN | `docs/B07_INTERFACES_ACCEPTANCE.md` |
| 中英文真实 SearXNG | NOT_RUN | 本轮搜索原始响应 |
| 五站以上真实网页/三解析器 | NOT_RUN | `reports/B08/raw/` + 人工标签 |
| 实际 Agent 再运行 | NOT_RUN | 本机脱敏轨迹和核验记录 |
| 搜索/获取/解析/模型分段耗时 | NOT_RUN | 本机观察 |
| Docker/SearXNG 和 Python 内存 | NOT_RUN | 本机观察 |
| 截图、敏感信息检查 | NOT_RUN | 检查记录 |

## 三、正文质量与失败分类

不能沿用 B03 六站人工质量标签推断 B08 本轮结果。新请求须逐个记录来源、正文、完整性、导航噪声、SPA 无正文及异常错误。

## 四、风险与限制

已有历史证据显示部分 SearXNG 引擎限流、长页面送入模型时可能截断、SPA 空壳不能由纯 HTTPX 读取动态正文。这些是需在本轮重新观测的已知边界。

本项目不提供“达到 ChatGPT 搜索准确率 80%”结论：尚未进行同题、代表性问题集、独立参考答案与人工盲评。不能将工程回归数量当准确率。

## 五、结论、复现与后续优化

**G5：NOT_RUN**。目前没有进行本次 B08 全量实机测试、页面复核和用户签认。

复现说明见 `docs/B08_ACCEPTANCE.md`。待补实际结论、错误复现、性能瓶颈、仍未解决的问题和下一阶段优化候选。
