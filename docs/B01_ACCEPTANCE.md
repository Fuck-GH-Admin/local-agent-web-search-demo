# B01 — SearXNG 本地搜索实现与 G1 验收

状态：**本机离线回归 PASS（55/55），G1 LIVE_PASS**。本报告记录 2026-10-13 的实际容器、原始 JSON、CLI 和中英文真实搜索证据。用户人工阶段签认尚未发生；本轮范围止于 B01。

## 交付

- `deploy/searxng/compose.yml`：仅绑定本机 `127.0.0.1:8080`。
- 官方镜像已按实际 pull 固定 digest；`compose.proxy.yml` 提供使用既有本机代理的可选 Linux 配置。
- `deploy/searxng/settings.yml`：在上游默认配置之上开启 `html`、`json` 输出；关闭本机演示的 limiter。
- `src/local_search_demo/search/searxng.py`：HTTPX 异步搜索客户端、URL 去重、来源合并、错误分类、耗时统计。
- `src/local_search_demo/interfaces/cli.py`：`search` 由占位变为真实查询，`environment` 保持 B00 行为；`read/agent` 仍返回 NOT_IMPLEMENTED。
- `tests/unit/test_searxng.py`：覆盖正常、空结果、字段缺失、重复 URL、403、429、5xx、非法 JSON、超时、上游失效、CLI。
- `scripts/b01-live-smoke.py`：显式触发中英文真实搜索，结果保存至 `reports/B01/search-smoke.json`。
- `scripts/b01-deployment-evidence.py`：记录实际容器状态、镜像、健康接口、启用引擎、配置哈希与非敏感日志；不保存容器环境变量集合。
- CI 只运行离线 pytest，**CI 不能代替 G1 实际搜索**。

## 已完成的离线 CI 证据

- GitHub Actions：[B01 offline regression](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38420077726)。
- 实际运行：`uv run --locked pytest -q`，**51 passed in 4.52s**；Python 3.12.13 依赖安装、构建和 pytest 均成功。
- 新增集成用例通过真实本机回环 HTTP 服务验证 CLI 的查询、JSON 解析与输出，但并不连接 SearXNG 的真实引擎。
- 固定证据：[`reports/B01/ci-offline.json`](../reports/B01/ci-offline.json)。该历史 CI 记录不包含 Docker/SearXNG 联网结果；本次 G1 真实验收记录见下一节。

## 已完成的本机 G1 证据

平台：Linux x86_64、CPython 3.12.13、uv 0.12.5、Docker 29.1.3、Compose 2.40.3。
基线主分支已更新为 `d63adc85b1cab34afe88715951ffcb76da31b693`；续作基于远端已有的 `feat/b01-searxng-search`，起点为 `6875414`。

| 实测动作 | 结果 | 证据 |
| --- | --- | --- |
| 本机完整离线 pytest | 55 PASS、0 失败/跳过 | `test-summary.txt`、`pytest.xml` |
| 容器与健康接口 | running、0 次重启、HTTP 200 | `compose-state.json`、`instance-config.json` |
| 英文 smoke：python asyncio documentation | HTTP 200，5 条，3023.872 ms；DuckDuckGo | `search-smoke.json` |
| 中文 smoke：电磁干扰 科学研究 | HTTP 200，5 条，2785.785 ms；DuckDuckGo / Google CSE | `search-smoke.json` |
| 原始 curl JSON：python asyncio | HTTP 200，27 条 | `curl-search.json`、`live-command-checks.json` |
| CLI 英文/中文真实查询 | 均 HTTP 200，各 5 条；保存 ExperimentRecord | `cli-search-en.json`、`cli-search-zh.json` |
| 当前监听地址 | 127.0.0.1:8080 | `loopback-listener.txt` |
| 镜像与版本锁 | 固定 digest，SearXNG 2026.10.13+22c64b8d3 | `image.json`、`deployment.json` |

证据目录为 `reports/B01/`。每个 smoke 记录开始/结束 UTC、真实来源、状态、耗时与上游错误；原始结果没有由测试脚本编造。
英文结果包含 `https://docs.python.org/3/library/asyncio.html`，中文结果包含来自 DuckDuckGo 与 Google CSE 的可点击 HTTP(S) URL。搜索结果包含 PDF 链接不代表已实现 PDF 读取。

镜像 digest：`sha256:9b61996edcc679fb6665290f95fda15389a14eda6060e41a25c63ab2758f2436`。
镜像 revision 为 `22c64b8d394b680c7ea96be25f36dad14126420a`，与 B00 源码锁一致；不是事前猜测的 digest。

### 网络失败与上游限制的实际记录

首轮默认 bridge 部署的两个请求均为 HTTP 200 / 0 条，错误为上游域名无法解析，状态记录为 `UPSTREAM_BLOCKED`。
原始输出保存于 `search-smoke-before-proxy.json` 和 `compose-logs-before-proxy.txt`。排查确认宿主机需要既有的 loopback 代理访问上游。
使用可选 host 网络配置后，两条真实查询均通过；SearXNG 仍只监听本机 loopback，宿主机代理设置未改动。

成功 smoke 仍记录了 Brave 的限流与暂停、英文 Google CSE 超时。镜像日志另有 tracker rules 下载超时、ahmia/torch 注册失败和 DOI 回调警告，均原样保留；当前查询通过可用引擎获得结果。
不据此宣称所有引擎可用或其他网络环境必然通过。没有浏览器渲染、付费搜索 API 或模型调用。

验收脚本补齐了分类：本地 429/5xx 为 `SERVICE_ERROR`，接口/JSON 配置错误为 `CONFIG_ERROR`，本地超时/连接错误为 `BLOCKED_LOCAL`，明确的上游错误为 `UPSTREAM_BLOCKED`，无错误空结果为 `NO_RESULTS`，无请求为 `NOT_RUN`。
新增 4 项回归覆盖该修正；业务搜索适配器仍保留既定 SearchResult 字段和错误语义。

## 测试与验收

### 第一层：离线回归（无需 Docker）

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked python -m local_search_demo search "  " --json
```

空白查询应输出 `INVALID_QUERY`，退出码 1，**不进行网络请求**。B00 原有的 `read/agent` 未实现行为应保持不变。

### 第二层：本机 SearXNG（G1 必做）

具有直接外网连接的环境使用默认配置。当前实测机器必须使用已存在的代理，实际启动命令为：

```bash
export SEARXNG_OUTGOING_PROXY=http://127.0.0.1:7890
docker compose -f deploy/searxng/compose.yml -f deploy/searxng/compose.proxy.yml up -d
```

```bash
# 仅可直接联网时使用默认启动；本次机器用上方的代理 override：
# docker compose -f deploy/searxng/compose.yml up -d
docker compose -f deploy/searxng/compose.yml ps
docker compose -f deploy/searxng/compose.yml logs --tail=100
curl -sS -G 'http://127.0.0.1:8080/search' \
  --data-urlencode 'q=python asyncio' \
  --data-urlencode 'format=json'

uv run --locked python -m local_search_demo search "python asyncio" --json --limit 5
uv run --locked python -m local_search_demo search "无人机 电磁干扰" --json --limit 5
uv run --locked python scripts/b01-live-smoke.py
```

镜像 digest、Compose 状态和非敏感日志已保存。复现后可重新采集：

```bash
uv run --locked python scripts/b01-deployment-evidence.py
```

**G1 PASS 门槛**：

1. 容器实际可访问，`/search?format=json` 返回合法 SearXNG 结构；
2. 中英文真实搜索至少一次获得 HTTP(S) URL，不能把 HTTP 200 + 空 `results` 判为成功；
3. Mock 固定测试对 403/429/超时/JSON 错误/空结果/上游故障分类符合契约；
4. 记录真实 SearXNG 引擎状态、搜索耗时、实际查询时间和 Docker 镜像 digest；
5. 验收结果、真实命令与输出追加进 `docs/IMPLEMENTATION_LEDGER.md`。

若服务可访问但全部上游被屏蔽，则 `UPSTREAM_BLOCKED`；若 Docker 不可达则 `BLOCKED_LOCAL`；**都不是 G1 PASS**。

### 注意

- 本轮不用商业搜索 API、不部署 Chrome/Chromium、不做网页提取和 AI。
- 首次 pull 使用 latest；实际部署和交付已固定观察到的 digest。
- JSON 查询的 `language` 和 `time_range` 是传给上游的筛选请求，**不能保证所有引擎都执行这些筛选**。
- 本次新增的唯一共享数据字段是 `SearchResult.http_status`（可选，空值允许）；既有 B00 主字段不变。

容器安装依据 [SearXNG 官方容器文档](https://docs.searxng.org/admin/installation-docker.html)，JSON 参数及 403 行为依据 [官方 Search API](https://docs.searxng.org/dev/search_api.html)。通过结论来自上述本机证据。
