# B02 — HTTPX 网页获取层（独立于正文解析）

状态：**B02 本机技术验收 PASS（91/91）；两个真实网站 smoke LIVE_PASS**。本次目标机器验收日期为 2026-10-14；历史 CI 记录单独保留。

## 责任边界

B01 是 URL 搜索；B02 根据 URL 下载 HTML；B03 才运行 Trafilatura / Readability / Selectolax。B02 不能使用任一正文提取器判断正文质量。

源码：`src/local_search_demo/fetch/httpx_fetcher.py`

- `create_http_client()`：可复用 HTTPX AsyncClient，连接池、5 次跳转上限、8 秒超时、默认遵循系统代理环境变量。
- `HTMLFetcher(client).fetch(url, max_bytes=..., timeout=...)`：返回 `FetchedHTML`，包含 Pydantic `FetchResult` 元数据、一次下载获得的内存 HTML bytes 和解码文本。
- 记录：初始 URL / 最终 URL / 跳转来源列表 / HTTP 状态 / Content-Type / 响应体字节数 / 使用的字符编码 / 下载耗时与错误。
- 解码优先次序：HTTP charset → BOM → HTML meta charset → UTF-8 替换回退，适配 GB18030 中文。
- charset 还须支持文本解码及 replace 错误处理。对 base64_codec、hex_codec、idna 等不适合 HTML 的注册 codec 回退，保留原始 HTML bytes，避免异常直接退出。
- 拒绝明确非 HTML 内容类型（如 PDF），但这不等于 PDF 功能失败；它本就不在 B02 范围。
- 文件保存：`save_html(document, path)` 写回相同的已下载 bytes，不重新发请求。成功下载但只有 JS 壳仍是**获取成功**，以后 B03 决定正文是否有用。
- 失败类型：INVALID_URL、INVALID_OPTIONS、HTTP_ERROR、RATE_LIMITED、TIMEOUT、NETWORK_ERROR、TOO_MANY_REDIRECTS、UNSUPPORTED_CONTENT_TYPE、TOO_LARGE、EMPTY_BODY、TRANSFER_DECODING_ERROR。TIMEOUT 的 message 保留 ConnectTimeout / ReadTimeout / WriteTimeout / PoolTimeout 具体类型。

## 已完成的 CI 自检

- GitHub Actions： [B02 77 项全量回归](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38426304082)。
- 固定 Python 3.12.13，`uv run --locked pytest -q` → **77 passed in 6.25s**，0 失败；涵盖 HTTPX MockTransport 与真实 localhost HTTP 服务。
- 该历史结构化结果原位于 fetch-tests.json，现完整保存在 [`reports/B02/ci-offline.json`](../reports/B02/ci-offline.json)。本次目标机器逐用例结果写入 [`fetch-tests.json`](../reports/B02/fetch-tests.json)。
- 该历史 CI 没有访问公网 HTML；目标机器实际下载记录见下面的本机验收，不根据 CI 推断网络可用性。

## 2026-10-14 本机完整验收

从最新 main `613bd217a3eddf5ea8e3c80810e74a3859102225` 非强制快进现有 B02 分支，完整阅读 README、执行计划、需求、上游预研、B00–B02 验收与台账及辅助说明，并复核 HTTPX 文档和下载器源码。
本机为 Linux x86_64 / CPython 3.12.13 / HTTPX 0.28.1 / uv 0.12.5，实际环境见 `reports/B02/environment.json`。
实测实现提交为 `921bd7d9d2c1b288f4f31931ead1b1d8104279e4`。在该提交上运行 `verify_b02.py --live --save-html`，91 项回归与两个公网下载均再次通过；非敏感证据在后续提交保存。

| 项目 | 本机结论 | 证据 |
| --- | --- | --- |
| B00/B01/B02 完整 pytest | 91 PASS，0 失败/跳过；B02 为 36 项 | `test-summary.txt`、`pytest.xml`、`fetch-tests.json` |
| 真正 localhost HTTP 服务 | 302→GB18030、403/404/429/503、非 HTML、空体、gzip 限制和慢响应分类通过 | integration 用例及逐用例记录 |
| 四种超时与网络错误 | TIMEOUT 保留子类型；ConnectError 为 NETWORK_ERROR | 参数化回归 |
| 异常 charset、BOM 与原始字节 | 无未捕获异常；UTF-8/UTF-16 BOM 与 GB18030 正确；保存只使用一次下载的 bytes | 单元用例、请求计数及文件比对 |
| example.org | 实际 HTTP 200、PASS、UTF-8，原始 bytes 已保存并校验 SHA-256 | `live-smoke.json`、本地 raw |
| Python asyncio 官方文档 | 实际 HTTP 200、PASS、UTF-8，原始 bytes 已保存并校验 SHA-256 | `live-smoke.json`、本地 raw |
| 依赖与复现 | 锁文件一致、已安装包兼容，验收命令可重复执行 | `verification-checks.txt`、`environment.json` |

两个目标的实际 URL、最终 URL、HTTP 状态、Content-Type、字节数、编码、耗时、预览与 SHA-256 都保存在 JSON；最终文件完整性检查保存在 `saved-html-checks.json`。
原始 HTML 位于 `reports/B02/raw/`，保持 Git 忽略；没有上传网页全文或真实凭据。正文解析耗时和正文质量尚未测量，获取阶段的 elapsed_ms 包含请求、接收和字符解码。

### 本次发现和修复

旧实现仅检查 codecs.lookup，导致 base64_codec、hex_codec、idna 三种 charset 在完整响应解码时发生未捕获异常。修复后使用非空文本解码探测，因为空 bytes 会跳过真正的解码器；不可用标签按既定次序继续回退。
同时在原 TIMEOUT 分类中补充具体超时类型，不修改 ErrorDetail/FetchResult 的字段语义。
增加 14 项用例，覆盖本地真实 403/429/503、HTTP 403、四种超时、异常标签及三种 BOM；现有原始 bytes 保存用例增加请求次数为 1 的断言。
修复前新增测试的实际失败输出为 `before-fix.txt`，中间修复输出为 `intermediate-fix.txt`；这些是已解决问题的历史快照，最终通过结果以本次 fetch-tests.json / pytest.xml 为准。

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

**已实现的验收命令：**

```bash
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked pytest -q tests/unit/test_httpx_fetcher.py tests/integration/test_fetch_http_local.py
uv run --locked python scripts/verify_b02.py --live --save-html
```

## 可选真实网站 smoke

这里验证目标机器对公网 HTML 的下载能力，不作为离线单元测试必过项：

```bash
uv run --locked python scripts/b02-live-smoke.py
# 指定其它站点：
uv run --locked python scripts/b02-live-smoke.py --url https://example.org/ --timeout 10 --save-html
```

默认目标为 example.org 与 Python 官方文档；JSON 会保存至 `reports/B02/live-smoke.json`。使用 `--save-html` 时原始内容存入 Git 忽略的 `reports/B02/raw/`，不要把大 HTML 数据盲目推送 GitHub。输出记录最终 URL、下载字节、编码、状态、错误和 SHA-256。

本次已在目标宿主机运行上述两条下载，均为 LIVE_PASS；保留的历史 CI 仍是 77 项，本机最新结果为 91 项。后续重新运行时据实更新网络结论。

注意：**宿主机本地 CLI 的 HTTPX 默认遵循 `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` 环境变量，Docker 容器的 host 网络 override 不会自动给宿主机 Python 进程配置代理。** B01 实际经历了代理问题，所以 B02 对目标网站的联网 smoke 必须独立确认，而不能依据 SearXNG 可用就宣称网页可读。

## B02 通过条件

- 固定本地 HTTP 和 Mock 测试实际运行通过。
- 403/404/429/非 HTML/异常编码/超时/跳转/响应过大分类无混淆。
- 测试可验证 bytes 仅下载一次，后续解析器可以在不重新请求的前提下使用。
- 记录环境与自动测试证据；若公网读取无法进行，标为可选 LIVE_BLOCKED，不隐瞒事实。

本批不把 CLI `read` 接成完整正文读取；按照计划 B04 实现统一 Core 和 CLI。下一批 B03 在本模块基础上接三个解析器。

HTTPX 行为复核依据：[异步客户端与流式 bytes](https://www.python-httpx.org/async/)、[四种超时](https://www.python-httpx.org/advanced/timeouts/)、[文本编码](https://www.python-httpx.org/advanced/text-encodings/)。本机通过结论来自上述实际运行证据。
