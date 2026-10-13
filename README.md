# Local Agent Web Search Demo

> 状态：需求范围已初步确认，技术预研与执行计划已形成；**B00 工程骨架已建立、离线测试 10/10 通过；真实联网功能尚未实现。**

用于验证**本地客户端内嵌的联网搜索与网页正文解析能力**，以及 AI Agent 通过工具调用自主搜索、读取网页并根据证据回答问题的可行性。

## 预期两种操作模式

1. **独立关键词搜索**：输入关键词，调用 SearXNG，返回结果列表；可独立选取 URL 读取，查看各解析器原始结果、兜底过程和耗时，无须模型。
2. **AI Agent 测试**：通过 Python `openai` SDK 连接可配置模型接口，把本地 `search_web` / `read_webpage` 注册为模型工具；记录实际工具调用和结果，最终给出带来源的回答。

## 暂定技术栈

- 搜索：SearXNG（本地部署，自有 JSON 搜索接口）
- 网页获取：HTTPX
- HTML 解析与正文抽取：Trafilatura / readability-lxml / Selectolax（均保留、支持观察各自结果）
- AI 调用：官方 openai Python SDK（可配置 `base_url`, `api_key`, `model`）
- 运行形态：共享 Python Core + `argparse` CLI + FastAPI / 原生 HTML/JS WebUI 双入口；无 Chrome/Chromium 抓取依赖

**注：** HTTPX 负责请求，其他三个负责不同层面的 HTML 处理；这些工具并不是功能完全等价的四个解析器。

## 范围边界

本阶段**只做可行性验证**，不是发布级客户端。界面、安全加固、性能极限优化、搜索 API 商业化方案不作为当前重点。PDF、复杂反爬/登录态、动态浏览器渲染、客户端正式集成先记为后续事项。

**开发前必读**：

1. [`docs/LOCAL_DEV_ENVIRONMENT.md`](docs/LOCAL_DEV_ENVIRONMENT.md) — 本机必需工具、按阶段安装、诊断脚本和日志回传；**本机开发者首先阅读**。
2. [`docs/DEMO_EXECUTION_PLAN.md`](docs/DEMO_EXECUTION_PLAN.md) — B00–B08 逐批工作、验收关卡与证据要求（当前唯一执行计划）。
3. [`docs/UPSTREAM_RESEARCH.md`](docs/UPSTREAM_RESEARCH.md) — 六个上游项目的官方文档与关键源码研读记录，以及 clone 失败的环境说明。
4. [`docs/DEMO_REQUIREMENTS_DRAFT.md`](docs/DEMO_REQUIREMENTS_DRAFT.md) — 原始需求草案及决定记录。

## B00 实施状态（2026-10-13）

当前变更位于 `feat/b00-foundation` 分支，未合并到 `main`。

- 已建立 Python package、配置模块、共享数据模型、CLI `doctor` 与三条尚未实现的命令入口。
- 已提交 6 类 HTML fixture、2 份搜索 JSON fixture、10 项通过的离线测试及原始环境日志。
- 当前测试容器 Python 3.13.5：执行 `python -m pip install --no-deps --no-build-isolation -e .` 和 `python -m pytest -q`，结果为 **10 passed**。这是**部分安装及离线测试**，不代表完整依赖可用。
- **G0 阻塞：** 当前容器 DNS 无法解析 GitHub；六个上游 clone、完整依赖安装及解析版本锁定待在可联网的本地机器补验。尚无 SearXNG 真实搜索或 Agent 运行记录。

请先参考 [本机环境与调试回传指南](docs/LOCAL_DEV_ENVIRONMENT.md)、[B00 本机补验步骤](docs/B00_LOCAL_SETUP.md)、[实施台账](docs/IMPLEMENTATION_LEDGER.md) 和 [原始验收证据](reports/B00/verification.json)。

本阶段可以运行：

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m local_search_demo doctor
python -m local_search_demo --help
```

注意：此处是预期的联网完整安装命令；当前测试容器**只成功执行了不下载依赖的 editable 安装**。搜索、读取和 Agent 在 B00 返回明确的 `not_implemented`，后续批次才实现。


## 参考项目

- [SearXNG](https://github.com/searxng/searxng)
- [HTTPX](https://github.com/encode/httpx)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [Selectolax](https://github.com/rushter/selectolax)
- [readability-lxml](https://github.com/buriy/python-readability)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
