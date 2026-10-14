# B03-LIVE-02 真实网站质量专项复核

复核日期：2026-10-14T05:08:21.443763+00:00；复核者：Codex。

六个不同网站、18 组解析结果，全部实际 HTTPX 下载 HTTP 200。每页只下载一次，三个解析器接收同一份 HTML；全文及原始输出保存在本机忽略的 raw/，提交报告绑定 HTML/正文/raw SHA。此次质量标签由逐项内容阅读给出，哈希检查不替代质量判断。

| 页面 | 类型 | Trafilatura | Readability | Selectolax |
|---|---|---|---|---|
| [python-article](https://www.python.org/doc/essays/blurb/) | 普通介绍文章 | correct | correct | correct |
| [wikipedia-article](https://en.wikipedia.org/wiki/Web_scraping) | 百科/导航密集 | correct | partial | noise |
| [mdn-documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Redirections) | 技术文档/代码 | correct | partial | correct |
| [gnu-chinese](https://www.gnu.org/philosophy/free-sw.zh-cn.html) | 中文长文章 | correct | correct | correct |
| [kubernetes-documentation](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/) | 技术文档/目录 | correct | correct | correct |
| [diagrams-spa](https://app.diagrams.net/) | 浏览器应用/SPA | noise | no_content | no_content |

## python-article

采集时刻 2026-10-14T04:58:31.162717+00:00；HTML SHA-256 `99c7324f90cacee9eca5c41b72ce79e4e477c5fabdd28f63a6fd2a93dd36a3b5`。

- **trafilatura：correct**，PASS / 1727 字 / 88.763 ms。对照原始 article 的两段介绍及末尾比较链接，正文完整，站点导航及脚本降级提示被排除。页内两处相同标题都进入文本，不是漏段；date=2026-01-01 无页面发布日期元数据支撑，不能作为可靠发表时间。
- **readability：correct**，PASS / 1729 字 / 27.124 ms。两段介绍和末尾链接均完整；原始 summary HTML 是 article。重复标题来自源页面 header/h1，文本中链接有额外换行但内容未丢，站点导航和脚本提示未混入。
- **selectolax：correct**，PASS / 1694 字 / 1.0 ms。article 选择器保留原始两段正文及末尾链接，去掉 header 中重复标题，正文只保留一个标题。链接拆行可读，未出现导航、脚本提示或乱码。

## wikipedia-article

采集时刻 2026-10-14T04:58:31.728947+00:00；HTML SHA-256 `b32d3fb99047a0c69771de660d9a0d7828fee4bb718023324fdfb865f069d3c6`。

- **trafilatura：correct**，PASS / 26287 字 / 101.215 ms。逐段对照 mw-parser-output，定义、History、各 Techniques、完整 Legal issues（含 Australia/India）和防抓取方法均保留；剔除维护告示及 See also 链接列表。参考文献仍占较大篇幅，带 edit 标记；主正文覆盖完整但不是纯净摘要。date=2005-09-17 不据此认定为本次更新时间。
- **readability：partial**，PASS / 8746 字 / 85.07 ms。raw summary HTML 只留下 Legal issues 开头至 European Union/CNIL 段落；全文输出虽非空（8746 字），缺失定义、History、Techniques、Australia/India 及防抓取章节。标题仍为整篇标题，不能把此片段当作完整网页正文。
- **selectolax：noise**，PASS / 28989 字 / 6.481 ms。main 选择器保留核心正文与全部参考文献，同时混入维护告示、编辑标记、See also 链接列表、Retrieved from 及 Hidden categories 分类尾部。全文覆盖足够，但维护/分类内容显著，链接碎行也增加阅读噪声，故不把字数最长等同最好。

## mdn-documentation

采集时刻 2026-10-14T04:58:32.397880+00:00；HTML SHA-256 `3c4a7c0634b1449b479f6044dbf10751a697a1d3634f346a360ba83bf1125514`。

- **trafilatura：correct**，PASS / 11017 字 / 40.294 ms。对照 main，导语、301/308/302/303/307/300/304 表格、三种跳转方式、优先级、用途、Apache/Nginx/IIS 配置和循环问题均保留。表格转为 Markdown；删掉重复目录列表、代码语言标签和反馈区。单次耗时不作性能排名。
- **readability：partial**，PASS / 10131 字 / 55.578 ms。导语及用途列表、主标题、Principle 与多数节标题被 summary 删除，正文从 HTTP 跳转机制开始；表格单元格和配置代码仍在，但丢失开篇解释及章节定位。保留了结尾循环说明，属于部分提取，不是整篇内容完全正确。
- **selectolax：correct**，PASS / 11364 字 / 3.764 ms。main 保留完整导语、章节、所有状态码表和配置代码；链接与单元格逐行导致表格格式变弱，代码语言标签及页末贡献/修改日期 UI 仍在，但主要内容完整且导航侧栏已除。记录少量 UI 噪声，不把它当无噪声输出。

## gnu-chinese

采集时刻 2026-10-14T04:58:33.908334+00:00；HTML SHA-256 `43204753a24cd29467b99b743c5f5aeae11e6feaeeeb03a90f6d6e4627b77a07`。

- **trafilatura：correct**，PASS / 8308 字 / 53.395 ms。对照 #content，全篇自由软件定义、四项自由、商业使用、边界细则、法律/合同、实践、软件之外、版本历史和脚注完整。目录/面包屑被删除，列表增加连字符，无中文乱码。
- **readability：correct**，PASS / 8283 字 / 19.427 ms。核心定义、四项自由及后续全部论述、版本历史和脚注内容保留；删除面包屑、目录和中间额外的授权联系提示段，以及脚注标题。联系提示属补充信息，本次核心论述不因此缺失；上述小范围省略已明确记录。
- **selectolax：correct**，PASS / 8617 字 / 1.452 ms。role=main 的 #content 正文与源页面去空白后逐字符相同，定义至脚注完整，无乱码；同时保留少量面包屑、翻译说明与目录，不能称为完全去噪。

## kubernetes-documentation

采集时刻 2026-10-14T04:58:35.159912+00:00；HTML SHA-256 `a47065e8ce4ff80a0c60dcdd07fbd65e30a7a66e621586d4b1a2a87143aad145`。

- **trafilatura：correct**，PASS / 9520 字 / 73.006 ms。Overview、能力列表、What Kubernetes is not、部署历史和容器优势均完整；删除下一步推荐链接及反馈 UI，末尾修改时间/提交说明仍保留。结构正文未缺段，日期是页面更新信息，不等同文章首次发表。
- **readability：correct**，PASS / 9467 字 / 139.719 ms。原始 td-content summary 保存 Overview 至容器优势列表全部正文及标题；下一步链接和反馈区删除，最后修改记录保留。链接拆行存在，但内容与 source main 完整对应。
- **selectolax：correct**，PASS / 9925 字 / 6.196 ms。main 正文完整，去空白后和源 main 全文相同；包括下一步链接及感谢反馈/问题提交 UI，约数百字页尾附加信息。核心内容可读，记录少量尾部噪声。

## diagrams-spa

采集时刻 2026-10-14T04:58:36.991496+00:00；HTML SHA-256 `5969a0c4a1196c165cc9a454b96c146371271c155cfb5e3705d8fbb7c9c7601b`。

- **trafilatura：noise**，PASS / 329 字 / 120.518 ms。329 字全部来自原始 noscript 的产品介绍及启用 JavaScript 提示；不是运行后的编辑器/用户图表内容。它是真实 HTML 静态文字，没有伪造动态内容，但不能把非空 PASS 当成 SPA 正文成功，按壳页噪声记录。
- **readability：no_content**，EMPTY / 0 字 / 1.544 ms。原始 summary 只剩空的编辑器 body，text=null、0 字；源 HTML 正文依赖 JavaScript，noscript 提示被过滤。没有执行浏览器或编造图表内容，正确呈现静态读取边界。
- **selectolax：no_content**，EMPTY / 0 字 / 0.164 ms。移除 script/style/noscript 后不存在可读主体，selected_selector=null、text=null、0 字，标题仍保留。没有把脚本变量当正文，也没有声称得到动态编辑器内容。

## 结论与限制

本项要求取得跨网站的独立三解析器质量观察，而不是要求所有算法全对。18 行均已复核：12 correct、2 partial、2 noise、2 no_content。保留缺段和噪声，不更换解析器或修改 B04 选择策略来美化结果。
这是有意选取的六页快照，不能外推全网准确率；耗时是一次运行且包含首次导入差异，不作性能排行榜。SPA 仍不执行浏览器；HTTP 200、非空和 CLI/UI 一致均不能替代质量正确。
B03 原 G2 用户签认记录保持原样，此专项不声称用户另行签认；本次只关闭 B03-LIVE-02，不把 B08 整体验收或 G5 写成完成。

复现：`uv run --locked python scripts/b03-live-quality.py --output-dir reports/B03/live-new`；逐项复核新快照后运行 `uv run --locked python scripts/b03-live-check.py --report-dir reports/B03/live-new`。原快照不覆盖。
