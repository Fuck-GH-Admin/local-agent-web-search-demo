# B08 本轮正文复核

内容复核：REVIEWED（Codex）；最终用户签认：PENDING_USER_SIGNOFF。访问时间以每条记录 UTC 为准，采集源码 `a14df8a7e026c2c01e34f886cf754b8dc72c0d1e`。

本轮6次成功下载，覆盖5个成功的不同域名；GNU初次及重试失败，另记6条 blocked。18条实际解析输出 + 6条未执行状态，共24条。质量分布：10 correct / 4 partial / 2 noise / 2 no_content / 6 blocked。正文/raw/标题/元数据与本轮原 HTML 对照，不从旧B03复制标签；这些标签不是搜索准确率。

| 页面 / 轮次 | 解析器 | 状态 / 字符 | 质量 | 具体理由 |
|---|---|---|---|---|
| python-article / initial | trafilatura | PASS / 1727 | correct | 完整保留语言定义、标准库与模块复用、异常和调试等主体段落；仅重复文章标题，不影响正文理解。 |
| python-article / initial | readability | PASS / 1729 | correct | 与本轮原 article 内容核对，定义、跨平台及开发效率段落齐全；正文开头重复标题是轻微格式问题。 |
| python-article / initial | selectolax | PASS / 1694 | correct | 选 article 容器且剔除页面导航；定义、扩展接口和源代码获取等原文段落完整，标题与页面一致。 |
| wikipedia-article / initial | trafilatura | PASS / 26287 | correct | 保留引言、历史、八类技术、各国法律与反爬段落和参考文献；去掉维护告示与 See also，主要正文没有缺失。 |
| wikipedia-article / initial | readability | PASS / 8746 | partial | 仅留下法律部分的开头和美国、欧盟段落；引言、历史、技术、澳洲印度、反爬和文献缺失，无法代表整篇文章。 |
| wikipedia-article / initial | selectolax | PASS / 28989 | noise | 主要正文齐全，但混入多处维护告示、编辑链接、页面旧版 URL 和全部隐藏分类；尾部不是文章主体，有明确导航维护噪声。 |
| mdn-documentation / initial | trafilatura | PASS / 11017 | correct | 原文介绍、永久临时特殊跳转、状态码表、HTML/JS优先级、服务器配置及循环说明完整保留。 |
| mdn-documentation / initial | readability | PASS / 10131 | partial | 多数表格、代码和解释仍在，但丢失跳转定义和用途介绍，以及多个章节标题；需保留部分缺失结论。 |
| mdn-documentation / initial | selectolax | PASS / 11364 | correct | 介绍、全部主要标题、状态码表和配置示例保留；末尾贡献/修改日期是少量行政信息，主体完整。 |
| gnu-chinese / initial | trafilatura | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| gnu-chinese / initial | readability | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| gnu-chinese / initial | selectolax | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| kubernetes-documentation / initial | trafilatura | PASS / 9520 | correct | 平台定义、十项能力、不是PaaS及部署历史等主要正文齐全；保留的参考下一步链接不构成主体遗漏。 |
| kubernetes-documentation / initial | readability | PASS / 9467 | correct | 平台定义、十项能力、限制与历史齐全；移除下一步推荐和反馈尾注，未删除重要正文段落。 |
| kubernetes-documentation / initial | selectolax | PASS / 9925 | correct | main 范围内所有正文标题及能力列表保留；反馈和下一步链接是轻微尾部信息，未影响正文完整性。 |
| diagrams-spa / initial | trafilatura | PASS / 329 | noise | 仅抽取 noscript 中的软件宣传和启用 JavaScript 提示；原 HTML 是动态应用空壳，没有图表编辑应用正文。 |
| diagrams-spa / initial | readability | EMPTY / 0 | no_content | 输出为空 body、字符数为零；下载成功但静态 HTML 没有动态应用内容，正确保留 EMPTY 而非伪造正文。 |
| diagrams-spa / initial | selectolax | EMPTY / 0 | no_content | 没有可用静态正文容器，输出 EMPTY、raw/text 为 null；HTTP 200 不能当作获得动态应用正文。 |
| gnu-chinese / gnu-retry | trafilatura | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| gnu-chinese / gnu-retry | readability | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| gnu-chinese / gnu-retry | selectolax | NOT_RUN / None | blocked | 本轮HTTPX下载为NETWORK_ERROR/ConnectError，未得到原始HTML，三个解析器均NOT_RUN；没有正文可评价，不沿用历史标签。 |
| kubernetes-chinese / chinese-supplement | trafilatura | PASS / 1927 | partial | 缺失开头的平台定义、Kubernetes不是什么的具体清单以及容器优势列表；文本止于列表引导语，1927字符不能代表全文。 |
| kubernetes-chinese / chinese-supplement | readability | PASS / 2954 | partial | 保留定义、限制和历史，但删除服务发现、存储、自动部署、自愈等六项核心能力列表；2954字符仍有重要遗漏。 |
| kubernetes-chinese / chinese-supplement | selectolax | PASS / 3752 | correct | 原 main 的定义、六项能力、限制和完整部署历史/容器优势均保留；移除脚本，仅残留少量反馈与修改日期。 |

[完整哈希绑定和访问时刻](quality-review.json)。原 HTML/正文仅保存在本机 `reports/B08/raw/pages-*/`，文件0600、目录0700。

英文Kubernetes自动选择 Selectolax正确；中文选择 Trafilatura部分缺失；Wikipedia选择 Selectolax有噪声；SPA选择Trafilatura仅获得noscript。选择理由是启发式观察，不能自动升级为质量PASS。
