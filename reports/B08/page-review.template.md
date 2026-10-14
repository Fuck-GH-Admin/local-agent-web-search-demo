# B08 本轮真实网页正文质量人工复核表

**状态：NOT_RUN。** 必须先执行 `uv run --locked python scripts/b08-validation.py --live --save-private`，再查看 `reports/B08/raw/` 中本轮实际抓取的完整正文及三解析器原始输出。不能沿用 B03 的人工质量标签。

评价选项：`correct` / `partial` / `noise` / `no_content` / `blocked`。每行需要具体可复核的原因（建议不少于 20 字）；不能把锚点命中或文本长度当作充分证据。

| case_id | 网页类别 | 解析器 | 人工质量 | 具体理由 |
|---|---|---|---|---|
| `python-article` | Python 介绍文章 | trafilatura | NOT_RUN | 未审阅 |
| `python-article` | Python 介绍文章 | readability | NOT_RUN | 未审阅 |
| `python-article` | Python 介绍文章 | selectolax | NOT_RUN | 未审阅 |
| `wikipedia-article` | 百科文章 | trafilatura | NOT_RUN | 未审阅 |
| `wikipedia-article` | 百科文章 | readability | NOT_RUN | 未审阅 |
| `wikipedia-article` | 百科文章 | selectolax | NOT_RUN | 未审阅 |
| `mdn-documentation` | MDN 技术文档 | trafilatura | NOT_RUN | 未审阅 |
| `mdn-documentation` | MDN 技术文档 | readability | NOT_RUN | 未审阅 |
| `mdn-documentation` | MDN 技术文档 | selectolax | NOT_RUN | 未审阅 |
| `gnu-chinese` | GNU 中文页面 | trafilatura | NOT_RUN | 未审阅 |
| `gnu-chinese` | GNU 中文页面 | readability | NOT_RUN | 未审阅 |
| `gnu-chinese` | GNU 中文页面 | selectolax | NOT_RUN | 未审阅 |
| `kubernetes-documentation` | Kubernetes 文档 | trafilatura | NOT_RUN | 未审阅 |
| `kubernetes-documentation` | Kubernetes 文档 | readability | NOT_RUN | 未审阅 |
| `kubernetes-documentation` | Kubernetes 文档 | selectolax | NOT_RUN | 未审阅 |
| `diagrams-spa` | 动态 SPA 空壳 | trafilatura | NOT_RUN | 未审阅 |
| `diagrams-spa` | 动态 SPA 空壳 | readability | NOT_RUN | 未审阅 |
| `diagrams-spa` | 动态 SPA 空壳 | selectolax | NOT_RUN | 未审阅 |

审核人：
访问时间：
相应 `reports/B08/observations.json` 哈希：
实机截图/原始文本本机路径（不提交含私密页面的原文）：
尚未完成或受阻事项：
总验收签认：**NOT_RUN**

**验收规则**：至少五个不同域名、每站三解析器全部有实际输出或失败状态，每一行有原因，再结合 Agent/G5 其它证据决定本批是否 PASS。
