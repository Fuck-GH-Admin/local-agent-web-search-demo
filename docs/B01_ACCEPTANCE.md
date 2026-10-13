# B01 — SearXNG 本地搜索实现与 G1 验收

状态：**离线回归 PASS（51/51），G1 NOT_RUN**。以下列出的命令是待实机执行的验收步骤，未提供真实容器与搜索结果前不能标为 G1 PASS。

## 交付

- `deploy/searxng/compose.yml`：仅绑定本机 `127.0.0.1:8080`。
- `deploy/searxng/settings.yml`：在上游默认配置之上开启 `html`、`json` 输出；关闭本机演示的 limiter。
- `src/local_search_demo/search/searxng.py`：HTTPX 异步搜索客户端、URL 去重、来源合并、错误分类、耗时统计。
- `src/local_search_demo/interfaces/cli.py`：`search` 由占位变为真实查询，`environment` 保持 B00 行为；`read/agent` 仍返回 NOT_IMPLEMENTED。
- `tests/unit/test_searxng.py`：覆盖正常、空结果、字段缺失、重复 URL、403、429、5xx、非法 JSON、超时、上游失效、CLI。
- `scripts/b01-live-smoke.py`：显式触发中英文真实搜索，结果保存至 `reports/B01/search-smoke.json`。
- CI 只运行离线 pytest，**CI 不能代替 G1 实际搜索**。

## 已完成的离线 CI 证据

- GitHub Actions：[B01 offline regression](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38420077726)。
- 实际运行：`uv run --locked pytest -q`，**51 passed in 4.52s**；Python 3.12.13 依赖安装、构建和 pytest 均成功。
- 新增集成用例通过真实本机回环 HTTP 服务验证 CLI 的查询、JSON 解析与输出，但并不连接 SearXNG 的真实引擎。
- 固定证据：[`reports/B01/ci-offline.json`](../reports/B01/ci-offline.json)。这不是 Docker/SearXNG 联网结果；G1 仍需本机验收。

## 测试与验收

### 第一层：离线回归（无需 Docker）

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked python -m local_search_demo search "  " --json
```

空白查询应输出 `INVALID_QUERY`，退出码 1，**不进行网络请求**。B00 原有的 `read/agent` 未实现行为应保持不变。

### 第二层：本机 SearXNG（G1 必做）

```bash
docker compose -f deploy/searxng/compose.yml up -d
docker compose -f deploy/searxng/compose.yml ps
docker compose -f deploy/searxng/compose.yml logs --tail=100
curl -sS -G 'http://127.0.0.1:8080/search' \
  --data-urlencode 'q=python asyncio' \
  --data-urlencode 'format=json'

uv run --locked python -m local_search_demo search "python asyncio" --json --limit 5
uv run --locked python -m local_search_demo search "无人机 电磁干扰" --json --limit 5
uv run --locked python scripts/b01-live-smoke.py
```

运行 G1 后还需要记录镜像 digest、Compose 状态和无敏感信息的尾部日志；建议保存在 `reports/B01/` 作为手工验收附录：

```bash
docker image inspect --format '{{json .RepoDigests}}' docker.io/searxng/searxng:latest
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
- 选用 `searxng:latest` 仅用于首次验证，不视为可复现镜像；G1 后记录 digest，下一轮决定是否固定它。
- JSON 查询的 `language` 和 `time_range` 是传给上游的筛选请求，**不能保证所有引擎都执行这些筛选**。
- 本次新增的唯一共享数据字段是 `SearchResult.http_status`（可选，空值允许）；既有 B00 主字段不变。
