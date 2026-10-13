# B03/G2 逐项内容复核（用户已签认，G2 PASS）

复核者：Codex（AI）；2026-10-14。已阅读六份原始 HTML 和 18 组 raw/text/title/耗时；标签不是按锚点匹配生成。

完整回归 109 项全部通过。结论：固定样本比较满足 G2 技术与内容记录要求；用户已明确回复“我签认，你可以继续”，记录时间 `2026-10-14T07:58:02.972072+08:00`（Asia/Shanghai）。18 行工作表检查退出 0，G2 PASS；签认证据见 [g2-signoff.json](g2-signoff.json)。

正文正确 14 组，夹带导航噪声 1 组，正确无正文 3 组。此计数描述这次合成样本，不是全网成功率。

| 样本 | 解析器 | 已签认质量 | 字符 | 单次耗时 ms | 标题 | 理由 |
|---|---|---|---:|---:|---|---|
| static_article | trafilatura | correct | 539 | 79.292 | A local experiment | 对照输入的 h1 和三段正文逐段阅读：共享下载、真实结果记录、分批验证的信息均完整保留；标题 A local experiment 一致。raw_output 是 JSON，text 无实验室页眉及 Contact 页脚；539 字与其他两种的差别来自空行，不是少段。 |
| static_article | readability | correct | 542 | 12.901 | A local experiment | summary HTML 保留 article 的 h1 和全部三段，规范化 text 与原文含义和顺序一致；标题正确。页眉 Example laboratory 与联系页脚已排除，542 字含段间空行，无 HTML 标签或乱码。 |
| static_article | selectolax | correct | 542 | 0.28 | A local experiment | 选中 article；完整保留标题与三段关于共享下载、记录证据、分批验证的正文。原始 article HTML 与规范化文本对应，542 字，去除 header/footer 后没有周边噪声或段落丢失。 |
| news_navigation | trafilatura | correct | 483 | 2.343 | Library opens a reading room | 逐段核对阅读室开设、学习用途、合成样本说明三段均完整，标题与 h1 一致；483 字主要与空行规则有关。原始 JSON 和 text 都未混入 Home/News/Sport/Subscribe 导航、虚构商品广告、Privacy/Terms 页脚。 |
| news_navigation | readability | correct | 485 | 1.215 | Library opens a reading room | summary HTML 聚焦 article，三个新闻段落按原顺序完整保留，标题 Library opens a reading room 正确；485 字的规范化文本无导航、购买广告、推荐或页脚，正文内容与输入一致。 |
| news_navigation | selectolax | correct | 485 | 0.12 | Library opens a reading room | 选中 article 并删除 nav/aside/footer；标题和三段正文完整，原始 HTML 与文本对应。B00_NAV_NOISE、广告商品描述与页脚 Privacy/Terms 均不在正文，485 字，无重复段落或乱码。 |
| technical_documentation | trafilatura | correct | 438 | 2.318 | Demo setup reference | 对照整个 main：h1、环境准备段、Example command 小标题、两行代码、环境命令说明及两个列表项均保留。标题正确，两行代码顺序与引号可读，列表转为带短横的行；438 字正文无 Overview/Installation/API/Changelog 导航。 |
| technical_documentation | readability | noise | 474 | 0.871 | Demo setup reference | 标题与全部 main 正文均正确，包括两行代码和两个列表项；但是 raw summary HTML 保留 nav，text 第一行明确含 Overview Installation API Changelog（35 个导航字符）。474 字包含少量导航噪声，标为 noise，不声称正文全部错误；这是需要保留的解析器差异，不能凭正文锚点命中认定干净。 |
| technical_documentation | selectolax | correct | 438 | 0.106 | Demo setup reference | 选中 main，正文 h1、小标题、两段说明、两行代码与两个列表项齐全；标题正确，438 字 text 无顶层导航。列表项目符号在纯文本中省略但两条内容未丢失，代码行未合并。 |
| short_chinese | trafilatura | correct | 41 | 99.451 | 简短通知 | 逐字核对通知标题、今天开放/保持安静、上午九点至下午五点三行都保留；标题 简短通知 正确，41 字，与另外两种正文一致，中文标点无替换字符。单次耗时较高只记观测，不影响内容标签。 |
| short_chinese | readability | correct | 41 | 0.767 | 简短通知 | 原始 summary HTML 保留 h1 与两段短通知，规范化三行与输入一致，41 字；开放说明与完整时间信息均可读，标题正确，无乱码、导航或凭空增加的内容。 |
| short_chinese | selectolax | correct | 41 | 0.106 | 简短通知 | 选中 article，标题及两段通知全部保留；41 字正文含今天开放、保持安静和上午九点至下午五点，字符和标点正确，没有因正文短而删去时间段。 |
| spa_empty | trafilatura | no_content | 0 | 3.709 | （空） | 原始输入只有空 app div 和 script，实际没有静态可见正文。提取器 raw/text/title 均为 null，EMPTY、0 字；未把 window.fixture 中的脚本字符串当正文。缺失页面标题如实记录，不影响空正文判断。 |
| spa_empty | readability | no_content | 0 | 0.567 | Application shell | 页面标题 Application shell 正确保留，但 summary 仅生成空 app p 容器；规范化 text 为 null、EMPTY、0 字。没有渲染脚本或将 B00_SCRIPT_ONLY_NOT_BODY 当作可见内容，符合静态空壳负例。 |
| spa_empty | selectolax | no_content | 0 | 0.096 | Application shell | 标题 Application shell 正确；删除 script 后既无 article/main 内容也无可见 body 文本，selected_selector/raw/text 均为空，EMPTY、0 字。没有捏造正文，也没有从脚本值提取内容。 |
| malformed | trafilatura | correct | 306 | 1.677 | Broken markup | 标题 Broken markup、三段正文和末尾 Unclosed emphasis 都保留，实体 &amp; 正确解码为 &，无补造文本或乱码。306 字中 visible entity.Unclosed emphasis 缺少分隔，属于可见格式瑕疵；内容完整，保留 correct 标签并单独记录粘连风险。 |
| malformed | readability | correct | 307 | 0.809 | Broken markup | summary HTML 修复未闭合标签，title 正确；三段内容、实体 & 及末尾强调文字齐全，307 字 text 把 Unclosed emphasis 分到下一行。未出现大段重复、源码标签或虚构补文；修复后结构和文本可读。 |
| malformed | selectolax | correct | 307 | 0.09 | Broken markup | Lexbor 将未闭合 h1 的后续元素包进同一 h1，raw HTML 如实保留该修复树；纯文本仍按行输出标题、三段和末尾强调文字，307 字，& 实体正确。正文信息完整，未将结构修复误称原始结构完美。 |

技术文档 Readability 的导航占 35 个字符（结果总计 474 字符），正文仍完整；保留 noise 标签和原始 HTML，不在本批删库或替 B04 选算法。残缺 HTML 的 Trafilatura 有一处词句粘连，正文信息未丢失。

Trafilatura 首个文章 79.292 ms，短中文 99.451 ms；此次顺序执行未控制暖机/缓存，首次还可能包含模块导入。其他 16 组单次为 0.09–12.901 ms，不能据此作总体性能或算法排名。

`parser-comparison.json` 是本次自动观测快照，生成时的 manual_G2_status=NOT_RUN 不代表后续签认；最终质量与签认以 manual-review.json、验收文档和索引为准。

最终签认依据：[待补验索引](../../docs/OPEN_VALIDATION_INDEX.md)、[B03 验收标准](../../docs/B03_ACCEPTANCE.md)。用户签认已记录，G2 PASS；B03-LIVE-02 真实网站泛化继续 NOT_RUN。

云端回归：[Actions #38485766242](https://github.com/Fuck-GH-Admin/local-agent-web-search-demo/actions/runs/38485766242)，109 passed in 7.50s。实际工件与本机 18 组正文、标题和状态一致；此云端检查不代替人工签认。
