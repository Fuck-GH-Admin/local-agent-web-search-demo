# B03 — 三解析器比较与 G2 人工验收

**状态：本机自动化 PASS（109/109，含 18 项 B03）；18 组 Codex 内容复核完成；最终 G2 人工签认 PENDING。**

## 目标与边界

本批比较 Trafilatura、readability-lxml、Selectolax；统一接收 B02 下载的**同一份** HTML 字符串与最终 URL，不在解析器里发起任何网络请求。

各解析器产生独立的 `ParserResult`，包含原始输出、规范化文本、标题、正文字符数、耗时、错误与可选元数据。失败互相隔离，不能因为一个异常丢弃另外两个。

- **Trafilatura**：一次 `extract(output_format="json", with_metadata=True)` 获取正文和元数据，原始 JSON 保留于 `raw_output`；其自身的 fallback/readability 类路径可能与独立 readability-lxml 重叠，三个结果不是统计意义的独立成功。
- **Readability**：`Document.title()` 后执行 `summary()`，后者是 HTML；原始 HTML 和经 Selectolax 后处理的文字分别保留。
- **Selectolax**：使用 Lexbor DOM，删除 script/style/nav/aside/footer 等区域，按 `article → main → role=main → articleBody → content → body` 的透明选择规则提取；它不是有内建文章排序器的第四种通用算法。
- **比较层**：`compare_parsers(html, url=...)` 按同样输入独立执行，记录每个耗时和 FAIL/EMPTY/PASS；`compare_downloaded(B02 的 FetchedHTML)` 拒绝在失败下载上假装提取成功。

### 原始结果和质量的差异

`ParserResult.status=PASS` 仅表示该解析器**输出非空文本**，不是人工证明正文正确。`raw_output` 格式各不相同，不用原始 HTML 标签计入正文长度。一个 SPA 空壳正确返回 EMPTY 是有效负例。不能用字符数最多直接选“最佳解析器”；B04 才开始兜底选择规则。

## 历史 CI 自动验证（保留原始记录）

- GitHub Actions： [B03 93 项测试 + 对比报告工件](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38429154060)（Python 3.12.13），`93 passed in 6.22s`。
- 生成对比：[工件 b03-parser-comparison](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38429154060/artifacts/11830362359)，包含完整 `parser-comparison.json`、易读 `parser-comparison.md` 和未填写质量结论的 `manual-review.json`。
- [固定自动观察摘要](../reports/B03/auto-observations.json)：6 类样本 × 3 种解析器，15 组非空、3 组 SPA 正确为空，无脚本正文泄漏。
- **待核实差异**：技术文档中 Readability 混入 `Overview Installation API Changelog` 顶部导航；另外两种未出现。短中文样本中 Trafilatura 单次处理 >100ms，不能据单次执行得出总体性能结论。
- 记录的 PASS/EMPTY 只说明提取器执行状态，不表示人工质量判断已通过。当前 CI 对应新增的 G2 工作表格式校验。人工质量还需逐条查看文本、保留理由后签认。

## 执行与自动测试

```bash
git fetch origin
git switch feat/b03-parser-comparison
uv sync --locked --all-extras
uv run --locked pytest -q
uv run --locked python scripts/b03-compare-fixtures.py
# 根据 Markdown/JSON 填写 manual-review.json 全部 18 行并设 human_review_status=REVIEWED 后：
uv run --locked python scripts/b03-g2-check.py
```

输出：
- `reports/B03/parser-comparison.md`：便于人工阅读的各解析器全文及自动锚点观察。
- `reports/B03/parser-comparison.json`：六类 HTML × 三个 parser 的原始/规范化输出、预计正文锚点、导航噪声锚点、耗时与异常；**仅自动记录观测、不自动判定人工质量**。
- `reports/B03/manual-review.json`：模板默认 `UNREVIEWED`，需人手标注 `correct/partial/noise/no_content/blocked` 并写理由。不覆盖已经填好的复核文件。
- `reports/B03/pytest-summary.txt`：从 CI 或目标主机真实执行所得摘要，不能伪造。

六个固定 HTML fixture：正常文章、嘈杂新闻、技术文档、短中文、SPA 空壳、非法/残缺 HTML。每种跑全部三解析器。原始输入 SHA 来自 B00 锁定 manifest，确保横向可比。

**G2 必备**：
1. 所有三个 adapter 都被实际运行，输出不因一个失败而被覆盖；所有六类 fixture 都有记录。
2. 有代表性的文章正文锚点实际出现；SPA 脚本值不能被当正文。
3. 人工判定每组结果 `correct / partial / noise / no_content / blocked`，并解释缺段、误混导航、格式损坏等；有失败不意味着需要本轮删除某个解析器。
4. 核验报告中的标题、抽取输出、耗时，不把固定人工样本得分外推为普遍覆盖率。
5. 正式 G2 签认前更新 [跨批次待补验索引](./OPEN_VALIDATION_INDEX.md) 和 [实施台账](./IMPLEMENTATION_LEDGER.md)。

本阶段不选最终算法，也不完成 CLI `read`、WebUI 或 Agent；它们分别属于 B04/B05/B07。

**非阻断衔接**：`B02-LIVE-01` 已于 2026-10-14 用两个真实下载及 SHA 证据关闭；B03 真实网站泛化测试（`B03-LIVE-02`）仍 NOT_RUN，留待后续并保留索引。

## 2026-10-14 目标机完整补验与内容复核

用户要求 G2 一并执行，并指定阅读 `OPEN_VALIDATION_INDEX.md`。当前 B03 以普通 merge 合入 B02 完整补验提交 `64008dbf3549ca8451317197e8a9ebb381af1c16`，保留所有既有代码、证据和历史失败快照；主分支没有被强制重写。

- 实测解析实现提交：`e979b6fabd5544cd50b4134235c179bed035917e`，Python 3.12.13、锁文件不变。
- `uv sync --locked --all-extras`、`uv lock --check` 与 `uv pip check` 通过。
- 全量 pytest：**109 passed in 6.55s**，0 失败/跳过；18 项属于 B03，包含六类输入、原始格式、中文/残缺 HTML、SPA、异常隔离、工作表校验以及 B02 一次下载接三个解析器。
- 发现并修复启动导入隔离缺口：旧比较层提前导入所有 adapter，缺少 trafilatura 或 readability 依赖时整个模块无法导入；两项全新解释器回归修复前均失败，修复后缺失者独立 FAIL/PARSER_ERROR、另外两者仍返回正文。未修改 Schema 或质量标准。
- Readability 的 HTML 后处理依赖 Selectolax，这一共享依赖继续如实保留；不能把三个结果称为完全独立算法。首次测量可能包括延迟模块导入，无性能排名结论。
- 新 CI 报告写入独立的 `ci-generated/` 目录，工件从 UNREVIEWED 工作表开始，不将本次已填写的质量标签套到未来自动生成的报告。实际隔离检查见 `ci-artifact-isolation.json`。

### 逐项正文判断

Codex 已阅读全部六份原始 HTML，逐一对照 18 组 raw_output、text、title、chars、elapsed_ms，填写完整理由。这是 AI 辅助内容复核，不冒充用户已签认，也不是用自动锚点匹配赋值。

| 输入 | Trafilatura | Readability | Selectolax | 主要判断 |
|---|---|---|---|---|
| 正常文章 | correct | correct | correct | 标题与三段正文完整，实验室页眉/页脚排除；空行差异不算缺段 |
| 嘈杂新闻 | correct | correct | correct | 全文三段完整，导航/广告/页脚均排除 |
| 技术文档 | correct | noise | correct | 三者均保留代码和列表；Readability 多出 35 字导航及换行，总计 474 字，其他正文为 438 字 |
| 短中文 | correct | correct | correct | 标题和两段通知均正确，41 字，无乱码 |
| SPA 空壳 | no_content | no_content | no_content | 三者 EMPTY/0 字，没有把脚本值当正文；Trafilatura 标题为空，其他两者保留页面标题 |
| 残缺 HTML | correct | correct | correct | 三段、实体与强调文字均保留；Trafilatura 末尾词句粘连如实记录，Selectolax 的修复树并不等于原始结构完美 |

建议标签 **14 correct / 1 noise / 3 no_content**。G2 要求比较并解释真实差异，不要求每个 parser 在全部输入都完美；导航噪声保留为本次有效观察，不因此删库，也不提前替 B04 选择算法。

工作表位于 [`manual-review.json`](../reports/B03/manual-review.json)，完整可读理由见 [`quality-review.md`](../reports/B03/quality-review.md)。正文与原始结果见 [`parser-comparison.json`](../reports/B03/parser-comparison.json) 和 Markdown。

### 最终人工签认

当前 `agent_review_status=REVIEWED`，`human_review_status=NOT_RUN`、`human_signoff_status=PENDING`；没有代替用户填写签认。18 行标签与理由均完整，但 `b03-g2-check.py` 实际返回 2，唯一原因是人工状态未设 REVIEWED（见 `g2-check.txt`）。此状态是待签认，不是隐藏的解析或回归失败。

按索引 `B03-G2-01` 的“再人工签认，不得拿自动检查替代质量判断”，在用户复核并签认上述具体报告后，才将人工状态设 REVIEWED、重跑完整性检查，并同步本页、执行计划、索引和台账为 G2 PASS。签认前 B04 完整验收保持未开始。

### 本机证据

`reports/B03/` 中保存 `environment.json`、`dependency-checks.txt`、`parser-tests.json`、`pytest.xml`、`pytest-summary.txt`、`comparison-command.txt`、完整对比、质量工作表、复核 Markdown、工作表检查输出与导入修复前失败快照。原始网页不上传；本批比较只使用已提交的合成 fixture，不作真实网站覆盖率结论。

### 本次云端回归与工件核验

报告提交 `546b3af789fc5884ea78de18ed2ba4ccecc9f797` 已推送到 B03 分支；[GitHub Actions #38485766242](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38485766242) 和同 SHA 的 #38485758925 均 SUCCESS。下载实际日志确认 **109 passed in 7.50s**。下载工件 #11859067857 核对 18 组输入 SHA、正文、标题和状态与本机复核快照逐项一致；新工件中的人工表仍全部 UNREVIEWED。原始 API 状态及摘要见 `reports/B03/ci-offline.json`，不能将该 CI 成功当作人工签认。
