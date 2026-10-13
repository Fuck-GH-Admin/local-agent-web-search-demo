# Local Agent Web Search Demo

> 状态：**B00 基线已实施，本机 G0 技术检查通过**。搜索、网页获取/解析、WebUI、Agent 业务功能属于 B01–B08，尚未实现或验收。

用于验证**本地客户端内嵌的联网搜索与网页正文解析能力**，以及 AI Agent 通过工具调用自主搜索、读取网页并根据证据回答问题的可行性。

## B00 实际可用入口与复现

实测基准：Linux x86_64、CPython 3.12.13、uv 0.12.5。`uv.lock` 保存完整依赖图，
`requirements.lock` 保存包含开发依赖的版本和下载哈希，`upstream-lock.json` 保存六份上游 SHA、Selectolax 子模块与许可证文件哈希。

在本地 B00 分支的 checkout 内执行（需要 Git、uv，首次安装需要 GitHub/PyPI 网络）：

```bash
uv python install 3.12.13       # 已有该版本可跳过
python3 scripts/restore_upstreams.py
uv sync --locked --all-extras
.venv/bin/python -m local_search_demo --help
.venv/bin/local-search-demo --help
.venv/bin/python scripts/verify_b00.py
```

另一终端的独立环境重建，不重新解析依赖：

```bash
bash scripts/rebuild_environment.sh .venv-fresh
```

上述目录必须尚不存在。也可以从已经交付的**本地仓库**创建全新 checkout 后重复第一组命令；本轮提交仅在本地，没有推送远端：

```bash
git clone --no-hardlinks --branch b00/environment-baseline /absolute/path/to/local-agent-web-search-demo b00-rebuild
cd b00-rebuild
```

`environment` 命令可单独运行，仅读取本地信息：

```bash
.venv/bin/python -m local_search_demo environment --output reports/B00/environment.json
```

目前 `search`、`read`、`agent` 是空入口，执行会明确返回 `NOT_IMPLEMENTED` 和退出码 2。
没有运行 SearXNG、浏览器或真实模型，也没有把安装成功算作业务功能成功。

验收详情见 [`docs/B00_ACCEPTANCE.md`](docs/B00_ACCEPTANCE.md)，原始输出位于 `reports/B00/`。

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

1. [`docs/DEMO_EXECUTION_PLAN.md`](docs/DEMO_EXECUTION_PLAN.md) — B00–B08 逐批工作、验收关卡与证据要求（当前唯一执行计划）。
2. [`docs/UPSTREAM_RESEARCH.md`](docs/UPSTREAM_RESEARCH.md) — 六个上游项目的官方文档与关键源码研读记录，以及 clone 失败的环境说明。
3. [`docs/DEMO_REQUIREMENTS_DRAFT.md`](docs/DEMO_REQUIREMENTS_DRAFT.md) — 原始需求草案及决定记录。

**当前完成 B00**：上游 clone、版本锁、项目骨架、六个统一模型、六类 HTML 与五类搜索 JSON 样本、离线测试和独立环境重建。SearXNG 部署、真实搜索和 Agent 测试尚未进行。

## 参考项目

- [SearXNG](https://github.com/searxng/searxng)
- [HTTPX](https://github.com/encode/httpx)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [Selectolax](https://github.com/rushter/selectolax)
- [readability-lxml](https://github.com/buriy/python-readability)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
