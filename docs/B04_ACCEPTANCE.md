# B04 — 统一 Core、回退策略与 CLI

**当前状态：自动化自检 PASS（124/124 + CLI 3 场景）；目标机公网 read 尚未补验。**

## 本批范围与数据流

1. `read_webpage(url)` 仅执行**一次 HTTPX 下载**，取得 B02 的原始 HTML bytes 和解码文本。
2. `compare_downloaded()` 将同一 HTML 交给 B03 三个独立解析器，各自产生原始结果、规范化正文、耗时、状态及错误。
3. `choose_result()` 基于可解释的启发式，为有正文候选打分，排除 EMPTY / FAIL、重视 DOM 结构和解析器之间的一致性，降低 body 兜底、明显异常长文本的权重。
4. `read_downloaded()` / `read_webpage()` 将原三份输出、被选正文、选择理由和全候选评分共同返回；**绝不只保存最终正文**。
5. CLI `search` 保持 B01 行为，`read` 正式接入 Core，`agent` 保持 NOT_IMPLEMENTED（B07）。

首次实现不声称自动评分是真实正文质量：B03 G2 中 Readability 技术文档混入 35 字导航的例子就是选择策略应保留候选证据的原因。本批不加入新模型/浏览器/PDF、也不为追求通过率随意删库。

### 共享契约扩展

对已有 `ReadResult` / `ExperimentRecord` 增加两项**可选**字段：
- `selected_text`：候选最终正文；没有正文时 `null`。
- `selection_evidence`：每个解析器的 `name/status/eligible/score/reason`，以解释选择和淘汰原因。

旧数据可以继续反序列化，不改变 B00–B03 字段含义。

## 命令示例

```bash
uv sync --locked --all-extras
uv run --locked pytest -q

# 真实公网测试（需要目标主机 HTTPX 可以直接使用的网络/代理）
uv run --locked python -m local_search_demo read "https://example.org/" --json
uv run --locked python -m local_search_demo read "https://docs.python.org/3/library/asyncio.html" --json --output reports/B04/read-python.json

# 真实 CLI + 本地临时 HTTP fixture 测试：不依赖外网或 SearXNG
uv run --locked python scripts/b04-cli-smoke.py
```

**输出**：`reports/B04/cli-smoke.json` 保存三种合成条件（文章、JS 空壳、404）的完整读取链路，含解析器输出、选择理由、计时、HTTP 状态与测试退出码。CI 会把结果作为构建工件保存。

可使用 `--save-html reports/B04/raw/page.html` 额外保留同一批次实际下载的 HTML bytes。原始 HTML 存在 Git 忽略目录，不建议把网页内容、登录后的私人数据或凭据上传仓库；JSON 也应审阅后再发布。

## 已核验的实际自动化证据

- [GitHub Actions #38489137689](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38489137689) 成功：Python 3.12.13，`124 passed in 9.03s`。
- 同次运行的 `scripts/b04-cli-smoke.py` 报告 **PASS / 3 个场景**，实际网络请求均为本机 HTTP：文章 1 次、SPA 1 次、404 1 次。正常文章被选 `selectolax`，三份原始解析结果同时保留；SPA 三项 EMPTY / 不选正文；404 三项 NOT_RUN / 不选正文。
- CI 完整输出工件 #11860464007（原工作流名为 `b03-parser-comparison`，内含 `B04/cli-smoke.json`）。已直接下载检查工件的实际 JSON 内容，而非只读取 CI success 标记。
- [B04 CI 固定证据](../reports/B04/ci-offline.json) 记录对应源码 SHA 与非联网测试边界。
- **B04 当前没有公网网页读取或人工准确率结论**；B03-LIVE-02 留在索引继续跟踪。

## 自动化验收

- pytest 覆盖六类固定 HTML 的候选评估、Readability 导航噪声降权、SPA 空壳不得伪造正文、三解析器全部失败/部分失败、原文件 bytes 仅下载一次、真实 localhost CLI 读取/404、全部 B00–B03 回归。
- `scripts/b04-cli-smoke.py` 使用临时 loopback HTTP 真实执行 CLI 三次，核验各路径退出码、三解析器完整字段及**每个正常 URL 恰好一次请求**。
- CLI / JSON 输出包含相同实验信息，不论选择或失败均可复查。
- 已附 CI 链接和数量；本机外网测试与真实网页主观质量仍需按跨批次索引另做。

## B04 通过条件

按原执行计划，B04 是**自动化自检关卡**，不单独要求 G2 式的人工签认。通过必须同时满足：
1. 最新代码的全量 pytest 实际 PASS，旧 B00–B03 测试不退化。
2. CLI `read` 对下载成功、SPA 空壳、HTTP 错误均真实执行并有 JSON 证据。
3. 不因正文为空或下载失败而返回虚构的成功内容。
4. 实际原始三解析器结果均保留、评分结果与淘汰理由可读、选中正文来自该次某个真实解析结果。
5. 更新 `OPEN_VALIDATION_INDEX.md` 保留非阻断的真实网站质量泛化问题，若新发现未通过检查须追加到索引。

### 风险与后续索引

- **B03-LIVE-02 / B04-LIVE-01**：真实网页质量对比及本机完整公网 read 仍 NOT_RUN，B08 的五网页质量观察仍需完成；不能把 synthetic fixtures 和测试评分推广为互联网覆盖率。
- **B06/07 URL 安全**：目前 `read` 是本机显式 CLI 输入。将来在 B06/B07 由模型控制 URL 时必须加入 URL/网络目标访问策略，避免模型/网页诱导读取本地、内网或元数据服务。属于正式 Agent 联调前的阻断安全项，不能把 CLI Demo 的任意 URL 测试行为不加过滤地暴露给模型。
- **模型**：B04 不连接模型，因此 Agent tool-call 全链路仍属于 B06/B07。

详细待办见 [跨批次待补验索引](./OPEN_VALIDATION_INDEX.md)。
