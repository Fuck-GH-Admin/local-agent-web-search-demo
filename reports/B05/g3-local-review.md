# B05 / G3 本机浏览器验收记录

**技术与实机检查：PASS；最终 G3 用户审核：PENDING。**

执行与截图复核：Codex。浏览器由 Playwright 驱动真实 Chrome，随后使用 view_image 逐张阅读 16 张 PNG；尚未冒充用户已签认。

执行系统：Ubuntu 26.04.1 LTS / x86_64；Python 3.12.13、uv 0.12.5、Node v22.23.2。
浏览器：Google Chrome 153.0.8010.52，有界面模式，Xvfb 虚拟显示；Playwright 1.62.1 是本机已有的独立 QA 工具。
应用实现提交：`4e5f56331f02dfd04864782f12198c9fd6c41f2c`；QA 脚本内容 SHA-256 见 environment.json 和 browser-observations.json。
实机操作时间：`2026-10-14T09:31:06.693000+08:00` 至 `2026-10-14T09:31:16.500000+08:00`（Asia/Shanghai）。
SearXNG：`http://127.0.0.1:8080`；WebUI：`http://127.0.0.1:8765`；合成控制源：`http://127.0.0.1:8766`。

## 自动回归与服务

- [x] `uv sync --locked --all-extras`，退出 0；锁文件与包兼容检查通过。
- [x] 全量 pytest：**133 passed in 8.42s**，0 失败/跳过；`pytest.xml` 和 `pytest-cases.json`。
- [x] `b05-api-parity.py`：**5/5 PASS**，文章/SPA/404/搜索的 CLI/API Core 字段严格一致；`api-tests.json`。原始 CI 版本保存为 `ci-api-tests.json`。
- [x] JS 语法与 wheel 资源通过；`wheel-check.json` 确认三个静态文件随分发包打包。
- [x] WebUI `/health` 与 SearXNG `/healthz` 均实际 200；仅 loopback 监听，见 `loopback-listeners.txt`。

## G3 实际浏览器逐项核验

| 项目 | 实机结论 | 证据 |
|---|---|---|
| 三页签与键盘 | 点击、ArrowRight、Home 实际切换；aria-selected / 面板状态正确 | [首页](screenshots/desktop-home.png)、browser-observations.json |
| 英文搜索 python asyncio | 实际 HTTP 200、PASS、5 条；标题、URL、摘要和来源引擎可见 | [英文搜索](screenshots/search-en.png) |
| 中文搜索 无人机 电磁干扰 | 实际 HTTP 200、PASS、5 条；上游错误也可见 | [中文搜索](screenshots/search-zh.png) |
| 普通文章 | python.org 的 What is Python? Executive Summary；HTTP 200、33984 bytes、UTF-8；三解析器均 PASS，候选 selectolax | [文章读取](screenshots/read-public-article.png)、live-cli-ui-parity.json |
| 技术文档 | docs.python.org asyncio；HTTP 200、25411 bytes、UTF-8；三解析器均 PASS，候选 selectolax | [文档读取](screenshots/read-public-docs.png) |
| 原始结果 | 三个 raw_output 通过真实 details 控件展开，HTML/JSON 以文字显示 | [三原始输出](screenshots/parser-raw-expanded.png) |
| SPA 空壳 | HTTP 获取成功、三个 EMPTY、0 字，无候选正文；脚本值未成为正文 | [SPA](screenshots/read-spa.png) |
| 404 | HTTP_ERROR 清晰显示、三个 NOT_RUN、无候选正文；没有伪造成功 | [404](screenshots/read-404.png) |
| 浏览器断网 | 实际请求失败显示 Failed to fetch，提交按钮恢复可用 | [断网](screenshots/browser-offline.png) |
| 失败后重试 | 同一表单恢复联网后正常读取 fixture，HTTP 200 与候选正文可见 | [恢复](screenshots/read-recovered.png) |
| 跳转 | 请求 /redirect 最终 /article，302 路径可见，正文与三结果保留 | [跳转](screenshots/read-redirect.png) |
| 搜索错误 | 空白字符触发 Core INVALID_QUERY，错误文本与失败状态可见 | [无效查询](screenshots/search-invalid.png) |
| Agent | 面板明确尚未接入模型；浏览器实际 POST /api/agent 为 501 / NOT_IMPLEMENTED，无回答或工具轨迹 | [Agent](screenshots/agent-placeholder.png) |
| 窄视口 | 390×844：表单改为竖向、三解析器单列；document.scrollWidth=390，未超出视口 | [窄屏读取](screenshots/mobile-read.png)、[单列解析器](screenshots/mobile-parsers.png)、[窄屏搜索](screenshots/mobile-search.png) |

浏览器自动观察 **17/17 PASS**。各次读取都逐项断言浏览器 DOM 的三解析器 text/raw/status、选中正文和请求/最终 URL 与实际 HTTP 返回相同；截图复核补充确认字体、布局、面板与错误确实可读。

## CLI 与 WebUI 的实测对照

普通文章与技术文档的两组 **核心字段严格相同**：下载元数据、三解析器原始/规范化输出和元数据、候选选择、选中正文、评分及理由一致，只排除 ID/时间戳/耗时。完整正文 SHA-256 与实测时刻见 `live-cli-ui-parity.json`。

两条真实搜索各自的 CLI/WebUI 均成功返回 5 条；两次请求相隔约一分钟，URL 排序和引擎错误提示发生变化，**未将这两条记成核心字段完全一致**。英文共同 URL 3 条，中文 4 条；Brave 限流/暂停、Wikidata 超时/暂停的提示如实保留。固定输入的 CLI/API 5/5 严格一致检查独立通过，所以不把实际搜索源变化改写为软件入口差异。

## 控制台与显示观察

未捕获 JS 异常（pageerror）：**0**。console 中有三条实际网络提示，全部保留在 browser-observations.json：

1. `/favicon.ico` HTTP 404：默认图标未提供，不影响表单或内容显示。
2. `/api/read` ERR_INTERNET_DISCONNECTED：本次主动断网负例，界面已显示失败并允许重试。
3. `/api/agent` HTTP 501：明确未实现的负例。

未发现阻断 G3 的展示或交互问题。技术文档的正文行分割和不同解析器长度差异仍由 Core 原样展示，候选评分只是启发式；本批不宣称最优算法或网页覆盖率。

## 复现本次主机 QA

应用与合成控制源分别在两个终端启动：

```bash
.venv/bin/python -m uvicorn local_search_demo.web.api:app --host 127.0.0.1 --port 8765
.venv/bin/python scripts/b05-browser-fixtures.py
```

第三个终端使用已有的 Playwright QA 包（或独立工具环境安装的包）：

```bash
# B05_PLAYWRIGHT_PATH 指向独立 Playwright 包目录，不写入应用依赖锁。
B05_PLAYWRIGHT_PATH=/path/to/playwright node scripts/b05-browser-smoke.cjs
```

要求本机已有 Chrome、Xvfb 和真实可用的 SearXNG。QA 驱动只操作本地 WebUI；真实目标 HTML 仍由应用 HTTPX 获取。本次内置浏览器工具首轮因缺显示服务失败，改用 Xvfb 的真实 Chrome 后完成全部操作，无 CI 截图或生成图片。

## 最终用户审核

正式 G3 **AWAITING_USER_REVIEW**：本机执行与截图复核已完成，等待用户审核这份具体证据。依据 docs/B05_ACCEPTANCE.md 的“由用户审核后将状态写为 G3 PASS”，确认后才更新 B05-G3-01 为 PASS。没有因已有 G2 签认而代替本次 G3 签认。

`B04-LIVE-01` 已用本次两个真实 CLI read 的 fetch/三解析器/正文/决策证据关闭，报告为 `reports/B04/live-read.json`。`B03-LIVE-02` 的真实网页质量泛化专项仍待独立复核，可参考本次两页输出，但不能据 UI/CLI 相等直接推断正文提取准确率；`B06-URL-SEC-01` 与 B07-G4-01 继续保留。

公开交付只含非敏感元数据、校验、PNG 与复核结论；完整网页/CLI/浏览器响应保存在 Git 忽略的 raw/，没有提交凭据、Cookie 或私人 URL。

## 新提交云端回归：账户计费阻断

实机证据提交 `d059b8028a2661703cc27bbc62c1c8dbd4cc6f02` 已成功上传。新的 [Actions #38497254054](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38497254054) 与 #38497249637 均在启动阶段被 GitHub 拒绝；runner 未分配、steps 为空、日志 ZIP 为空，没有执行任何新测试。GitHub failure annotation 明确说明账户付款失败或支出限额需提高，不能把此结果写为新提交 CI PASS。

原始诊断与提示存于 `ci-startup-blocked.json`，跨批次索引新增 B05-CI-01 BLOCKED。GitHub 账户负责人处理 Billing & plans 后可补跑；Codex 没有修改账户付费设置、预算或 workflow 来绕过该限制。本机 133/133、CLI/API 5/5 和真实浏览器 17/17 的证据独立保留；G3 仍等待用户审核具体实机记录。
