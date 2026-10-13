# B03 — 三解析器比较与 G2 人工验收

**状态：自动化自检 PASS（93/93，后续附加 G2 检查回归将再次核验）；G2 人工验收 NOT_RUN。**

## 目标与边界

本批比较 Trafilatura、readability-lxml、Selectolax；统一接收 B02 下载的**同一份** HTML 字符串与最终 URL，不在解析器里发起任何网络请求。

各解析器产生独立的 `ParserResult`，包含原始输出、规范化文本、标题、正文字符数、耗时、错误与可选元数据。失败互相隔离，不能因为一个异常丢弃另外两个。

- **Trafilatura**：一次 `extract(output_format="json", with_metadata=True)` 获取正文和元数据，原始 JSON 保留于 `raw_output`；其自身的 fallback/readability 类路径可能与独立 readability-lxml 重叠，三个结果不是统计意义的独立成功。
- **Readability**：`Document.title()` 后执行 `summary()`，后者是 HTML；原始 HTML 和经 Selectolax 后处理的文字分别保留。
- **Selectolax**：使用 Lexbor DOM，删除 script/style/nav/aside/footer 等区域，按 `article → main → role=main → articleBody → content → body` 的透明选择规则提取；它不是有内建文章排序器的第四种通用算法。
- **比较层**：`compare_parsers(html, url=...)` 按同样输入独立执行，记录每个耗时和 FAIL/EMPTY/PASS；`compare_downloaded(B02 的 FetchedHTML)` 拒绝在失败下载上假装提取成功。

### 原始结果和质量的差异

`ParserResult.status=PASS` 仅表示该解析器**输出非空文本**，不是人工证明正文正确。`raw_output` 格式各不相同，不用原始 HTML 标签计入正文长度。一个 SPA 空壳正确返回 EMPTY 是有效负例。不能用字符数最多直接选“最佳解析器”；B04 才开始兜底选择规则。

## 已发生的实际自动验证

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

**非阻断衔接**：B02 目标机公网下载仍未核验（`B02-LIVE-01`），B03 真正网站泛化测试（`B03-LIVE-02`）留待后续，均在索引中保留。
