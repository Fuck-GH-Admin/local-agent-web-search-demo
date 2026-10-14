# B06-URL-SEC-01 — 模型网页读取访问策略验收

**本机与 self-hosted CI PASS（2026-10-14）。** 本项完成 DNS/连接绑定及跳转访问检查；B07 真实模型 G4 尚未执行。

## 实现与实际调用路径

`AgentToolDispatcher(mode="live") → create_public_http_client → PublicURLTransport → B04 read_webpage → 三解析器`。

- 模型只能读取本次搜索返回的 URL；复用 Runner 时清空上次搜索来源。模型参数不能指定 SearXNG 地址、fixture 模式、代理、resolver 或 transport。
- 初始 URL 拒绝非 HTTP(S)、userinfo、localhost/本地域名、异形数字 IP、歧义字符和非常规端口；HTTP 仅 80，HTTPS 仅 443。
- 域名的全部 A/AAAA 地址必须允许公网访问；混合公网/内网回答同样拒绝。拒绝私网、loopback、链路本地、元数据、CGNAT、组播、保留地址；额外拒绝 IPv4-mapped、NAT64/6to4/Teredo、site-local、文档/特殊用途范围和 Azure 平台服务 IP。
- 解析只发生一次，HTTP transport 使用已验证的 IP 字面值连接，避免检查和连接之间再次解析原域名。Host 与 TLS SNI 仍使用原域名，证书验证保持开启。
- 每次重定向再次进入同一策略，包含同域名重新解析；最多 5 次跳转。拒绝发生在下一目标请求之前，不先请求再检查最终 URL。
- 模型读取使用独立客户端，禁用环境代理和连接复用，避免代理重新解析及同 IP 不同域名复用错误 TLS 会话；SearXNG 继续使用受信的本地服务客户端。
- 失败返回 `URL_DENIED`、`DNS_ERROR`、`TIMEOUT` 等结构化错误，全部 parser 为 NOT_RUN，不生成正文。

这是模型工具入口的约束；B04 的明确人工 CLI 输入与本地 fixture 路径保留原有行为。需要公网代理的部署不能默默放行此策略，当前模型读取走直连；没有升级成通用生产网络授权系统。

## 实测证据

- 全量 **259/259** pytest，通过既有 B00–B06 与新增网络边界回归。新 URL 安全文件 103 项，工具循环 23 项；定向测试计 126 项。
- 覆盖 IPv4/IPv6、DNS 全答案检查/NXDOMAIN/超时/重绑定、同域与跨域跳转、IPv4 异形表示、userinfo/端口、跳转上限、public literal、请求方法、来源隔离与代理环境。测试观察实际请求是否发出，而不只检查 URL 字符串。
- HTTPX 的实际 HTTP core 测试观察两次相同 IP、不同原域名的 TCP/TLS 调用：连接只收到固定 IP，两个 SNI 分别保留原域名，SSL `CERT_REQUIRED/check_hostname` 均开启；不复用错误的虚拟主机会话。
- `scripts/b06-url-security-smoke.py --live` 的 **11/11** 检查通过：受保护的生产 transport 直连 Python 与 GNU 官网均 HTTP 200；实际 SearXNG `python asyncio` 返回的 Python 官方 URL 经 live Dispatcher 读取成功。
- 两个实机拒绝检查使用真实监听的 loopback HTTP 服务和默认 HTTP delegate，分别拒绝 IP 字面值及解析到 loopback 的域名；该服务实际收到 **0** 个请求。跳转与 DNS 变更的对抗响应由受控 transport 提供，不冒充真实恶意公网站点。
- B06 原有四种脚本模型轨迹、B04 三场景、B05 五组 CLI/API 对照、依赖、JS 与 wheel 检查均通过。

证据目录 [`reports/B06/url-security/`](../reports/B06/url-security/) 包含 JUnit、完整命令输出、11 项实际烟测、环境/源码哈希和后续真实 CI 状态；`reports/B06/tool-loop-tests.json` 是本次四组脚本模型结果。

开发中发现的两类问题保留原始失败记录：空 userinfo 被 HTTPX 规范化掉（`before-empty-userinfo-fix.txt`）；旧分类放行 `192.88.99.1` 与 `fec0::1`（`before-special-ranges.json`）。修复后均有回归。

## 复现

```bash
uv sync --locked --all-extras
uv run --locked pytest -q tests/unit/test_public_network.py tests/unit/test_agent_loop.py
uv run --locked python scripts/b06-url-security-smoke.py
# 显式联网，要求本地 SearXNG 已运行：
uv run --locked python scripts/b06-url-security-smoke.py --live --output reports/B06/url-security/live-new.json
```

CI 只运行可重复的受控网络检查与实机 loopback 拒绝，不在 CI 重新访问选定网页，也不复用旧人工标签。B07 仍须用真实模型取得 search→read→answer 的 G4 证据。

## 上游依据

自定义 transport 包装遵循 [HTTPX 官方接口](https://www.python-httpx.org/advanced/transports/)，固定 IP 后的原域名验证使用 [HTTP core SNI 扩展](https://www.encode.io/httpcore/extensions/#sni_hostname)。特殊地址对照 [Python ipaddress 文档](https://docs.python.org/3/library/ipaddress.html)、[IANA IPv4](https://www.iana.org/assignments/iana-ipv4-special-registry/)、[IANA IPv6](https://www.iana.org/assignments/iana-ipv6-special-registry/) 和 [Azure 平台地址说明](https://learn.microsoft.com/en-us/azure/virtual-network/what-is-ip-address-168-63-129-16)。保守拒绝范围是本 Demo 策略，不声称所有特殊地址都属于私网。

## 实际 CI 与工件核验

[Actions #38515437204](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38515437204)，实现提交 `f432b8c68b1beb540a0ae74c7596084a27203bdd`，实际 runner `ghrunner-local-agent-web-search-demo`；19 个步骤全部 SUCCESS，日志确认 **259 passed in 9.44s**。下载工件 #11871173508，JUnit 无失败/跳过，安全 smoke 8/8、两个实际 loopback 计数均 0，B04 3/3、B05 5/5、B06 四轨迹 PASS；B03 自动生成的 18 行工作表仍 UNREVIEWED。`reports/B06/url-security/ci-source-implementation.json` 保存 API/步骤/工件哈希证据。此 CI 不代替本机 11 项中的实际公网读取或六网站质量复核。
