# Local Agent Web Search Demo

> 状态：**B00 基线与 B01 搜索层已实施，本机 G0 技术检查和 G1 真实搜索通过**。网页获取/解析、WebUI、Agent 属于 B02–B08，尚未实现或验收。

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

上述目录必须尚不存在。也可以从 GitHub 的 B00 分支创建全新 checkout 后重复第一组命令：

```bash
git clone --branch b00/environment-baseline https://github.com/Fuck-GH-Admin/local-agent-web-search-demo.git b00-rebuild
cd b00-rebuild
```

`environment` 命令可单独运行，仅读取本地信息：

```bash
.venv/bin/python -m local_search_demo environment --output reports/B00/environment.json
```

在 B00 交付时 `search`、`read`、`agent` 都是空入口；当前 B01 已实现搜索，`read` 与 `agent` 仍返回 `NOT_IMPLEMENTED` 和退出码 2。
B00 历史验收不包含真实联网；当前搜索实测见下方 B01，浏览器与真实模型尚未运行。

验收详情见 [`docs/B00_ACCEPTANCE.md`](docs/B00_ACCEPTANCE.md)，原始输出位于 `reports/B00/`。

## B03 三解析器横向比较（待 G2）

`Trafilatura`、`readability-lxml`、`Selectolax` 已基于同一份下载 HTML 独立提取正文和记录耗时，不会各自下载页面。CI 已产出 18 组 JSON/Markdown 对比及空白人工复核表。

- [B03 代码与 G2 验收标准](docs/B03_ACCEPTANCE.md)
- [解析器真实 CI 对比摘要](reports/B03/auto-observations.json)
- [跨批次未通过与待补验索引](docs/OPEN_VALIDATION_INDEX.md)

```bash
uv run --locked pytest -q
uv run --locked python scripts/b03-compare-fixtures.py
# 完成人工标注之后：uv run --locked python scripts/b03-g2-check.py
```

## B02 HTTPX 网页获取层（自动化自检已通过）

[查看 B02 验收依据](docs/B02_ACCEPTANCE.md) · [自动测试证据](reports/B02/fetch-tests.json)

HTTPX 已具备一次下载、跳转追踪、字符编码、内容类型过滤、原始 HTML bytes 与错误分类；与 B03 三解析器解耦。GitHub Actions 已通过 **77/77** 离线测试；暂未验证本机公网 HTML 下载，另外此阶段 `read` 仍是占位命令。

```bash
uv run --locked pytest -q
uv run --locked python scripts/b02-live-smoke.py
```

## B01 本地关键词搜索（G1 LIVE_PASS）

B01 仅实现 SearXNG 搜索层；网页读取和 Agent 仍返回 `NOT_IMPLEMENTED`。
运行之前需要本地 Docker / Docker Compose v2，及 B00 的 `uv sync --locked --all-extras` 环境。

```bash
docker compose -f deploy/searxng/compose.yml up -d
uv run --locked python -m local_search_demo search "python asyncio" --limit 5 --json
uv run --locked python -m local_search_demo search "电磁干扰" --language zh-CN --time-range week --json
uv run --locked python scripts/b01-live-smoke.py
uv run --locked python scripts/b01-deployment-evidence.py
```

搜索可配置 `SEARXNG_BASE_URL` 或 CLI `--base-url`，结果保留真实 HTTP 状态、来源引擎、耗时和错误。回归测试使用 HTTPX MockTransport，不依赖联网。
镜像已固定实际 digest。当前本机通过已有的 `127.0.0.1:7890` 代理访问上游，因此实际启动使用下面的可选 Linux 配置；具有直接外网连接的环境可使用上方默认命令：

```bash
export SEARXNG_OUTGOING_PROXY=http://127.0.0.1:7890
docker compose -f deploy/searxng/compose.yml -f deploy/searxng/compose.proxy.yml up -d
```

该配置使用 host 网络访问已有代理，SearXNG 仍仅监听 `127.0.0.1:8080`。不创建新代理服务。
本机 **55 项离线测试通过**，中英文真实烟测均为 HTTP 200、各 5 个有效结果；首轮 DNS 失败与后续上游限流/超时均保留在 `reports/B01/`。
详情见 [B01 技术与 G1 验收](docs/B01_ACCEPTANCE.md)。本批分支为 `feat/b01-searxng-search`，可从该分支 clone 后按上面步骤复现。

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

- [跨批次未通过与待补验索引](docs/OPEN_VALIDATION_INDEX.md) — 每次进入下一批，先核对仍需补做的检查，完成后保留证据再更新状态。

1. [`docs/DEMO_EXECUTION_PLAN.md`](docs/DEMO_EXECUTION_PLAN.md) — B00–B08 逐批工作、验收关卡与证据要求（当前唯一执行计划）。
2. [`docs/UPSTREAM_RESEARCH.md`](docs/UPSTREAM_RESEARCH.md) — 六个上游项目的官方文档与关键源码研读记录，以及 clone 失败的环境说明。
3. [`docs/DEMO_REQUIREMENTS_DRAFT.md`](docs/DEMO_REQUIREMENTS_DRAFT.md) — 原始需求草案及决定记录。

**B00–B02 验收/自检已通过；B03 自动化 93 项通过，G2 人工复核待完成**：本机 G0 与 G1 已通过；B02 HTTPX 网页获取层 77 项 CI 回归通过，机器公网网页读取另列可选补验。正文解析、WebUI 和真实 Agent 测试仍未进行。

## 参考项目

- [SearXNG](https://github.com/searxng/searxng)
- [HTTPX](https://github.com/encode/httpx)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [Selectolax](https://github.com/rushter/selectolax)
- [readability-lxml](https://github.com/buriy/python-readability)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
