# B02 — HTTPX 网页获取层（独立于正文解析）

状态：**B02 自动化自检 PASS（77/77）；真实网站 smoke NOT_RUN**。

## 责任边界

B01 是 URL 搜索；B02 根据 URL 下载 HTML；B03 才运行 Trafilatura / Readability / Selectolax。B02 不能使用任一正文提取器判断正文质量。

源码：`src/local_search_demo/fetch/httpx_fetcher.py`

- `create_http_client()`：可复用 HTTPX AsyncClient，连接池、5 次跳转上限、8 秒超时、默认遵循系统代理环境变量。
- `HTMLFetcher(client).fetch(url, max_bytes=..., timeout=...)`：返回 `FetchedHTML`，包含 Pydantic `FetchResult` 元数据、一次下载获得的内存 HTML bytes 和解码文本。
- 记录：初始 URL / 最终 URL / 跳转来源列表 / HTTP 状态 / Content-Type / 响应体字节数 / 使用的字符编码 / 下载耗时与错误。
- 解码优先次序：HTTP charset → BOM → HTML meta charset → UTF-8 替换回退，适配 GB18030 中文。
- 拒绝明确非 HTML 内容类型（如 PDF），但这不等于 PDF 功能失败；它本就不在 B02 范围。
- 文件保存：`save_html(document, path)` 写回相同的已下载 bytes，不重新发请求。成功下载但只有 JS 壳仍是**获取成功**，以后 B03 决定正文是否有用。
- 失败类型：INVALID_URL、INVALID_OPTIONS、HTTP_ERROR、RATE_LIMITED、TIMEOUT、NETWORK_ERROR、TOO_MANY_REDIRECTS、UNSUPPORTED_CONTENT_TYPE、TOO_LARGE、EMPTY_BODY。

## 已完成的 CI 自检

- GitHub Actions： [B02 77 项全量回归](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38426304082)。
- 固定 Python 3.12.13，`uv run --locked pytest -q` → **77 passed in 6.25s**，0 失败；涵盖 HTTPX MockTransport 与真实 localhost HTTP 服务。
- 结构化结果保存在 [`reports/B02/fetch-tests.json`](../reports/B02/fetch-tests.json)。
- **本机公网 HTML smoke 尚未执行。** 这项原计划非阻断，不能根据 CI 声称已验证你机器的代理和实际网页获取。

## 已实施的离线测试

单元测试：`tests/unit/test_httpx_fetcher.py`，HTTPX MockTransport；集成测试：`tests/integration/test_fetch_http_local.py`，在 127.0.0.1 临时端口启动真实 HTTP 服务。

关键验收内容：

1. Unicode 中文、GB18030 字节原样保留；文件保存 SHA 可匹配原始下载体。
2. 302 跳转前后 URL 正确；过多跳转报错。
3. 404、429、503 分类且**绝不返回伪正文**。
4. application/pdf 等非 HTML 返回 UNSUPPORTED_CONTENT_TYPE。
5. Content-Length / 流式读取达到大小限制均停止；gzip 解压后的大小也受限制。
6. 本地慢响应触发读取超时，网络断开与超时不混淆。
7. 一份 `AsyncClient` 可以完成多次请求；联网下载耗时不会混入下一批解析器耗时。
8. 原 B00/B01 全量回归无退化。

**计划验收命令：**

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked pytest -q tests/unit/test_httpx_fetcher.py tests/integration/test_fetch_http_local.py
```

## 可选真实网站 smoke

这里验证目标机器对公网 HTML 的下载能力，不作为离线单元测试必过项：

```bash
uv run --locked python scripts/b02-live-smoke.py
# 指定其它站点：
uv run --locked python scripts/b02-live-smoke.py --url https://example.org/ --timeout 10 --save-html
```

默认目标为 example.org 与 Python 官方文档；JSON 会保存至 `reports/B02/live-smoke.json`。使用 `--save-html` 时原始内容存入 Git 忽略的 `reports/B02/raw/`，不要把大 HTML 数据盲目推送 GitHub。输出记录最终 URL、下载字节、编码、状态、错误和 SHA-256。

注意：**宿主机本地 CLI 的 HTTPX 默认遵循 `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` 环境变量，Docker 容器的 host 网络 override 不会自动给宿主机 Python 进程配置代理。** B01 实际经历了代理问题，所以 B02 对目标网站的联网 smoke 必须独立确认，而不能依据 SearXNG 可用就宣称网页可读。

## B02 通过条件

- 固定本地 HTTP 和 Mock 测试实际运行通过。
- 403/404/429/非 HTML/异常编码/超时/跳转/响应过大分类无混淆。
- 测试可验证 bytes 仅下载一次，后续解析器可以在不重新请求的前提下使用。
- 记录环境与自动测试证据；若公网读取无法进行，标为可选 LIVE_BLOCKED，不隐瞒事实。

本批不把 CLI `read` 接成完整正文读取；按照计划 B04 实现统一 Core 和 CLI。下一批 B03 在本模块基础上接三个解析器。
