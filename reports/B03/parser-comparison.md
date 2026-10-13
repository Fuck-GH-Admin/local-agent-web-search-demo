# B03 固定样本解析器对比（G2 人工验收待完成）

来源：六份合成 HTML；本报告耗时仅是单次实验，非性能基准。

完整 raw_output 及元数据见 parser-comparison.json。

## static_article (article)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | PASS | 539 | 79.292 | B00_ARTICLE_CORE: True | — |
| readability | PASS | 542 | 12.901 | B00_ARTICLE_CORE: True | — |
| selectolax | PASS | 542 | 0.28 | B00_ARTICLE_CORE: True | — |

### trafilatura — PASS

~~~~text
A local experiment
B00_ARTICLE_CORE: A shared HTML download lets several text extractors inspect exactly the same evidence. This article is synthetic and makes no claims about a real website.
Each experiment records the source, errors, timings, and the text actually returned. An empty result remains empty, and a failed download is never promoted to an extracted article.
The initial batch prepares reproducible dependencies and fixed inputs. Search services, extraction adapters, and model calls are verified separately in later batches.
~~~~

### readability — PASS

~~~~text
A local experiment

B00_ARTICLE_CORE: A shared HTML download lets several text extractors inspect exactly the same evidence. This article is synthetic and makes no claims about a real website.

Each experiment records the source, errors, timings, and the text actually returned. An empty result remains empty, and a failed download is never promoted to an extracted article.

The initial batch prepares reproducible dependencies and fixed inputs. Search services, extraction adapters, and model calls are verified separately in later batches.
~~~~

### selectolax — PASS

~~~~text
A local experiment

B00_ARTICLE_CORE: A shared HTML download lets several text extractors inspect exactly the same evidence. This article is synthetic and makes no claims about a real website.

Each experiment records the source, errors, timings, and the text actually returned. An empty result remains empty, and a failed download is never promoted to an extracted article.

The initial batch prepares reproducible dependencies and fixed inputs. Search services, extraction adapters, and model calls are verified separately in later batches.
~~~~

## news_navigation (news_navigation)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | PASS | 483 | 2.343 | B00_NEWS_CORE: True | B00_NAV_NOISE: False, B00_AD_NOISE: False, B00_FOOTER_NOISE: False |
| readability | PASS | 485 | 1.215 | B00_NEWS_CORE: True | B00_NAV_NOISE: False, B00_AD_NOISE: False, B00_FOOTER_NOISE: False |
| selectolax | PASS | 485 | 0.12 | B00_NEWS_CORE: True | B00_NAV_NOISE: False, B00_AD_NOISE: False, B00_FOOTER_NOISE: False |

### trafilatura — PASS

~~~~text
Library opens a reading room
B00_NEWS_CORE: The fictional town library opened a quiet reading room on Tuesday, with desks for visitors and shelves for donated books.
Staff explained that the room would support group study during the day. The example includes navigation and advertisements so later extraction tests can distinguish the article from surrounding noise.
This text is a handcrafted fixture. The event, location, and people are invented for an offline software experiment.
~~~~

### readability — PASS

~~~~text
Library opens a reading room
B00_NEWS_CORE: The fictional town library opened a quiet reading room on Tuesday, with desks for visitors and shelves for donated books.

Staff explained that the room would support group study during the day. The example includes navigation and advertisements so later extraction tests can distinguish the article from surrounding noise.

This text is a handcrafted fixture. The event, location, and people are invented for an offline software experiment.
~~~~

### selectolax — PASS

~~~~text
Library opens a reading room
B00_NEWS_CORE: The fictional town library opened a quiet reading room on Tuesday, with desks for visitors and shelves for donated books.

Staff explained that the room would support group study during the day. The example includes navigation and advertisements so later extraction tests can distinguish the article from surrounding noise.

This text is a handcrafted fixture. The event, location, and people are invented for an offline software experiment.
~~~~

## technical_documentation (technical_docs)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | PASS | 438 | 2.318 | B00_DOC_CORE: True, B00_CODE_ANCHOR: True | — |
| readability | PASS | 474 | 0.871 | B00_DOC_CORE: True, B00_CODE_ANCHOR: True | — |
| selectolax | PASS | 438 | 0.106 | B00_DOC_CORE: True, B00_CODE_ANCHOR: True | — |

### trafilatura — PASS

~~~~text
Demo setup reference
B00_DOC_CORE: Create an isolated Python environment before installing the locked dependencies. This sample contains headings, inline code, and a multiline code block.
Example command
python -m local_search_demo --help
print("B00_CODE_ANCHOR")
The environment command inventories local imports. It does not deploy a search engine or contact a model provider.
- Keep upstream source separate.
- Retain failure evidence.
~~~~

### readability — PASS

~~~~text
Overview Installation API Changelog
Demo setup reference

B00_DOC_CORE: Create an isolated Python environment before installing the locked dependencies. This sample contains headings, inline code, and a multiline code block.

Example command
python -m local_search_demo --help
print("B00_CODE_ANCHOR")

The environment command inventories local imports. It does not deploy a search engine or contact a model provider.

Keep upstream source separate.
Retain failure evidence.
~~~~

### selectolax — PASS

~~~~text
Demo setup reference

B00_DOC_CORE: Create an isolated Python environment before installing the locked dependencies. This sample contains headings, inline code, and a multiline code block.

Example command
python -m local_search_demo --help
print("B00_CODE_ANCHOR")

The environment command inventories local imports. It does not deploy a search engine or contact a model provider.

Keep upstream source separate.
Retain failure evidence.
~~~~

## short_chinese (short_chinese)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | PASS | 41 | 99.451 | 短中文正文锚点: True | — |
| readability | PASS | 41 | 0.767 | 短中文正文锚点: True | — |
| selectolax | PASS | 41 | 0.106 | 短中文正文锚点: True | — |

### trafilatura — PASS

~~~~text
简短通知
短中文正文锚点：今天阅览室开放，请保持安静。
时间：上午九点至下午五点。
~~~~

### readability — PASS

~~~~text
简短通知
短中文正文锚点：今天阅览室开放，请保持安静。
时间：上午九点至下午五点。
~~~~

### selectolax — PASS

~~~~text
简短通知
短中文正文锚点：今天阅览室开放，请保持安静。
时间：上午九点至下午五点。
~~~~

## spa_empty (spa_empty)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | EMPTY | 0 | 3.709 | — | B00_SCRIPT_ONLY_NOT_BODY: False |
| readability | EMPTY | 0 | 0.567 | — | B00_SCRIPT_ONLY_NOT_BODY: False |
| selectolax | EMPTY | 0 | 0.096 | — | B00_SCRIPT_ONLY_NOT_BODY: False |

### trafilatura — EMPTY

~~~~text
(empty)
~~~~

### readability — EMPTY

~~~~text
(empty)
~~~~

### selectolax — EMPTY

~~~~text
(empty)
~~~~

## malformed (malformed)

| 解析器 | 状态 | 字符 | 耗时 (ms) | 正文锚点 | 噪声锚点 |
|---|---|---:|---:|---|---|
| trafilatura | PASS | 306 | 1.677 | B00_MALFORMED_CORE: True | — |
| readability | PASS | 307 | 0.809 | B00_MALFORMED_CORE: True | — |
| selectolax | PASS | 307 | 0.09 | B00_MALFORMED_CORE: True | — |

### trafilatura — PASS

~~~~text
Broken markup
B00_MALFORMED_CORE: This hand-authored document deliberately leaves elements unclosed.
The text should remain readable when an HTML5 parser repairs the document tree. Broken markup is a test input, not a reason to invent missing content.
A final paragraph & a visible entity.Unclosed emphasis
~~~~

### readability — PASS

~~~~text
Broken markup
B00_MALFORMED_CORE: This hand-authored document deliberately leaves elements unclosed.
The text should remain readable when an HTML5 parser repairs the document tree. Broken markup is a test input, not a reason to invent missing content.
A final paragraph & a visible entity.
Unclosed emphasis
~~~~

### selectolax — PASS

~~~~text
Broken markup
B00_MALFORMED_CORE: This hand-authored document deliberately leaves elements unclosed.
The text should remain readable when an HTML5 parser repairs the document tree. Broken markup is a test input, not a reason to invent missing content.
A final paragraph & a visible entity.
Unclosed emphasis
~~~~

## 人工待做

逐条查看 18 组文字，在 manual-review.json 标注 correct / partial / noise / no_content / blocked。
每一组必须给出理由；此处 PASS 只是正文非空，不等于质量正确。
