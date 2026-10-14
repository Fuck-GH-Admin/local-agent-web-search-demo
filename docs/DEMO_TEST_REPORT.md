# Local Agent Web Search Demo — B07 接口与 B08 最终测试报告

**技术采集和内容复核已完成，存在已解释的外站可用性限制；G5：PENDING_USER_SIGNOFF。** 本报告不声明所有网站通过。用户既有 G2/G3/G4 签认有效，新增 B07 接口审核随本次 G5 提供。准确性基准按用户要求留到 Demo 完成后。

## 范围与环境

2026-10-14 在目标 Ubuntu 26.04.1 LTS 实测本地 SearXNG、HTTPX、三解析器、共享 Core、CLI/API/WebUI 和官方 DeepSeek Agent。运行 Python 3.12.13、uv 0.12.5、Chrome 153.0.8010.52（真实有界面浏览器，经 Xvfb）；Node 22.23.2 仅用于 CI/浏览器验收工具，应用无 Node 运行依赖。

应用源码 `85d65d625fff677a769964321fbbbdd91da70882`；B08 页面和模型采集源码 `a14df8a7e026c2c01e34f886cf754b8dc72c0d1e`；新增受控 HTTP 故障验收脚本/CI 源码 `e48a8f272edef020a619722e88f8c74dba8b503f`。后两次提交没有改变应用 Core/解析器。原始采集保留其实际源码归属，不用后来的报告提交替换。

依赖：HTTPX 0.28.1、httpcore 1.0.9、Trafilatura 2.3.1、readability-lxml 0.9、Selectolax 0.4.13、OpenAI SDK 3.29.0、FastAPI 0.143.0、pytest 9.1.1。SearXNG 镜像 digest `sha256:9b61996edcc679fb6665290f95fda15389a14eda6060e41a25c63ab2758f2436`。六个上游完整 SHA、license 哈希、锁文件 SHA 见 [环境记录](../reports/B08/validation/environment.json)；依赖未解锁更新。

SearXNG 位于 loopback 8080，使用宿主代理；普通网页下载继承环境代理。模型控制的 read 使用独立公网 DNS/IP 固定、原域名 TLS 与逐跳检查，直连、不继承环境代理，未关闭 TLS 校验。模型为官方 `deepseek-flash`、Chat Completions、thinking disabled、tool_choice auto；Key 只存在本机私有进程内存，未写入仓库/CI。

## 测试与实际结果

| 检查 | 实际状态 | 证据与边界 |
|---|---|---|
| 完整本机 pytest | PASS，347/347，9.67s，0失败/跳过 | [机器快照](../reports/B08/observations.json)，本机独立 checks 目录 JUnit |
| B04 CLI / B05 CLI-API / B06模拟 / B07 SDK普通入口 | PASS，3 / 5 / 4 / 4 场景 | 同一快照，实际子进程退出0；原历史输出归档后恢复原bytes |
| G2/G3/B06/G4 历史绑定 | PASS，3 / 19 / 11 / 10 项 | 核对原 Git blob、PNG、锁文件与本机 G4 原轨迹；未改写已签材料 |
| B07 普通 CLI/API/WebUI | 技术PASS | [实机接口报告](../reports/B07/interfaces/validation/review.md)：真实CLI与UI各3模型回合、2搜索/2读取、2引用，共同正文SHA相同 |
| B07 实际浏览器与保护 | PASS，9浏览器检查/7接口保护 | 5张捕获时脱敏PNG已逐张查看；390px、错误恢复、缺配置、跨源拒绝、受控HTML文本安全；固定安全输出不冒充真实模型 |
| 本轮中英文真实 SearXNG | LIVE_PASS，各5结果 | [搜索指标](../reports/B08/validation/search-live.json)，Brave仍有上游限流/不响应 |
| 真实页面 / 三解析器内容复核 | REVIEWED；6成功页、5成功域名 | [24条复核](../reports/B08/validation/quality-review.md)，含GNU两次下载失败的6条blocked |
| B08 新真实 Agent 闭环 | DONE，3模型回合，2搜索/2读取，2引用，0未核引用 | [脱敏轨迹指标](../reports/B08/validation/agent-live.json)，内容复核REVIEWED_WITH_NOTES |
| 429 / 403 / 超时 | PASS，3/3实际CLI | [故障证据](../reports/B08/validation/negative-http.json)，本地HTTP服务可控故障；非真实公网或模型服务故障 |
| 安全实机重跑 | PARTIAL，两轮均10/11，原整体FAIL保留 | [安全刷新记录](../reports/B08/validation/security-refresh.json)，GNU正向获取失败；DNS/IP/重定向保护与sentinel零请求通过 |
| 源码云端 CI | PASS，347/347，24步骤，HTTP故障3/3 | [最终验证源码日志/工件](../reports/B08/validation/ci-validation-source.json)，Actions #38562639454；[采集源码CI](../reports/B08/validation/ci-source.json)也通过，交付头另行核验 |
| 性能/内存 | OBSERVED | 实际单机观测，不设无证据性能阈值 |
| 正式 G5 用户签认 | PENDING_USER_SIGNOFF | 完整报告、例外与新增接口证据需要用户审核；机器不能自签 |

原 `observations.json` 是生成时的机器快照，保留 `G5`、正文人工评审和模型重跑 `NOT_RUN`；后续实际复核与重跑以独立 [最终技术汇总](../reports/B08/validation/acceptance.json)、正文复核和新 Agent 文件为准，不修改原快照伪造当时状态。云端 CI 为离线、无模型 Key、无付费调用，不能替代上述实机记录。

## 本轮正文质量

每站保存同一次下载的原 HTML，与三解析器完整 raw/text、标题、元数据对照，并保存 SHA 绑定。长文采用段落与差异对照辅助审阅，标签由内容判断填写，未按长度或锚点自动判 correct。

| 页面 | Trafilatura | Readability | Selectolax | 主要观察 |
|---|---|---|---|---|
| Python介绍文章 | correct | correct | correct | 主体齐全，前两者轻微重复标题 |
| Wikipedia文章 | correct | partial | noise | Readability只保留部分法律章节；Selectolax带维护/隐藏分类 |
| MDN技术文档 | correct | partial | correct | Readability漏引言和标题，其他两者主体齐全 |
| Kubernetes英文文档 | correct | correct | correct | 十项能力、限制与历史完整 |
| diagrams.net SPA | noise | no_content | no_content | noscript宣传/启用JS提示或空正文；没有动态应用内容 |
| Kubernetes中文补充 | partial | partial | correct | Trafilatura漏定义/限制/优势列表；Readability漏六项能力 |
| GNU中文初次+重试 | blocked×2 | blocked×2 | blocked×2 | 无HTML，解析器NOT_RUN，不能复用B03正文评价 |

共24条：10 correct / 4 partial / 2 noise / 2 no_content / 6 blocked。这是特定采样的抽取质量，不能换算为搜索准确率。新闻导航、短中文、畸形HTML等另外由六类固定fixture覆盖：本轮18输出与已签G2输入及内容字段一致（包括raw/标题/元数据，排除捕获日期字段），见 [固定输入对照](../reports/B08/validation/fixture-equivalence.json)。fixture不冒充真实新闻站点。

自动选择仍是启发式：中文选择Trafilatura部分正文、Wikipedia选择带噪声的Selectolax、SPA选择noscript。保留这些现状和优化候选，不把自动选中当质量合格。

## 故障、修复和未完成项

B07 本轮发现并修复预算类型/非有限值、空白提问、验证回显隐私、CLI输出权限、安全阶段元数据缺失与中文括号引用误判。新增8+9条回归，原失败JUnit/真实CLI/UI轨迹保留。来源提示明确禁止无依据版本推测；没有放宽URL来源或私网访问政策。

B08 采集器新增3条失败复现后修复：完整HTML与JSON同轮保存、每次独立目录避免覆盖、审批必须核对原Git blob。子脚本历史报告bytes恢复；CI全历史checkout用于审批绑定。修复前失败仍存本机raw。

GNU：普通HTTPX首次和重试均NETWORK_ERROR/ConnectError；安全读取两轮分别NETWORK_ERROR与TIMEOUT/ConnectTimeout。单独标准TLS握手曾成功，不能推断HTTP下载正常。连接路径根因尚未定位；没有绕过TLS或替换为旧正文。该站内容核验是**部分完成/blocked**，安全脚本整体FAIL也没有改为PASS。五个其他成功域名满足采样数，新增中文Kubernetes补齐实际中文覆盖，失败仍是可审核例外。

其他限制：Brave限流；SPA不渲染JS；选中正文可能遗漏或有噪声；送给模型最多6000字符。未实测模型服务401/429/超时、其他模型和Responses。网页受控403/429/超时不能替代这些未完成实验。未实施检索/答案准确性基准或ChatGPT同题盲评，也不声称达到80%。

## 新 Agent 内容与性能观察

实际Kubernetes问题从两次本地SearXNG搜索读取英文/中文官方页；英文工具文本6000字符足以支持定义、十项能力、不是PaaS等主要最终论断，两条引用均在本次成功读取来源中。模型未猜版本号。最终答案有两点备注：中文1927字符的不完整来自解析器遗漏，未触发6000字符上限；历史说明夹有来源中没有的英文短语，未新增事实，但应在后续输出复核消除。原完整回答只保留本机，不声称回答零瑕疵。

| 阶段 | 实际耗时 ms |
|---|---:|
| 独立英文 / 中文搜索 | 2303.168 / 733.166 |
| Agent搜索两次 | 2100.304 / 1524.763 |
| Agent英文 / 中文下载 | 1068.789 / 619.523 |
| Agent三模型响应 | 1673.127 / 997.343 / 5908.541 |
| Agent整体 | 14534.379 |
| B07最终CLI / 浏览器Agent整体 | 11125.068 / 8693.913 |

单站采集：三解析器时间按Trafilatura / Readability / Selectolax排列；包含当前下载重定向，均为本轮真实时间。

| 页面 | HTTP / 错误 | 下载字节 | 获取 ms | 三解析器 ms | 被选 |
|---|---|---:|---:|---|---|
| python-article | 200 | 33984 | 630.82 | 90.425 / 24.213 / 0.915 | selectolax |
| wikipedia-article | 200 | 236292 | 1499.089 | 90.977 / 82.421 / 6.583 | selectolax |
| mdn-documentation | 200 | 228570 | 845.807 | 37.604 / 55.627 / 3.714 | selectolax |
| gnu-chinese | NETWORK_ERROR | — | 15662.694 | NOT_RUN / NOT_RUN / NOT_RUN | 无 |
| kubernetes-documentation | 200 | 506514 | 511.321 | 74.477 / 135.452 / 6.237 | selectolax |
| diagrams-spa | 200 | 4134 | 325.757 | 97.091 / 1.58 / 0.175 | trafilatura |
| kubernetes-chinese | 200 | 591490 | 1935.268 | 194.759 / 183.805 / 6.49 | trafilatura |

GNU普通下载重试4363.4ms且失败。新Agent三个模型回合使用6278 prompt tokens、1082 completion tokens；累计各回合usage不能当独立上下文长度。API3次模型响应合计8579.011ms；搜索、解析、网络与调度使整体不同于单一模型时间，记录不用于统计性能排名。

内存：[观测记录](../reports/B08/validation/performance.json)。采集进程自身峰值107452 KiB；已完成请求后的应用RSS/HWM106260 KiB；SearXNG Docker在该次采样58.7 MiB、CPU0.20%、8进程。6次500ms间隔采样发生在Agent请求完成后，没有捕获CLI活动峰值，Docker不含全部宿主/代理开销；不是并发、吞吐或低端设备预算测试。

## 复现与后续候选

```bash
git fetch origin
git switch feat/b08-final-validation
uv sync --locked --all-extras
uv run --locked python scripts/b08-validation.py --live --save-private
uv run --locked python scripts/b08-negative-smoke.py
uv run --locked python scripts/b06-url-security-smoke.py --live --output reports/B08/raw/security-new.json
# 按docs/B07_INTERFACES_ACCEPTANCE.md配置本机模型环境（不要把Key写入报告）
uv run --locked python -m local_search_demo agent '读取Kubernetes官方概述，依据成功读取的正文解释其能力，并注明未获取的信息' --allow-live-read --thinking disabled --json --output reports/B08/raw/agent-new.json
# 查看原HTML/三输出后填写新复核表；机器采集不代替人工签认。
```

Agent与WebUI访问启用开关、预算、密钥仅服务端配置，见[B07入口验收](B07_INTERFACES_ACCEPTANCE.md)。仅在loopback启动本地未鉴权Demo。原始报告/图片位于Git忽略的raw目录；公开文件只包含脱敏指标、理由和哈希，5张截图在捕获时遮罩。当前已签G2/G3/G4证据不可覆盖。

后续候选：减少中文列表抽取遗漏；将质量风险纳入选择解释；识别SPA空壳；处理引擎限流；更清楚报告模型正文截断与抽取遗漏；定位GNU HTTPX连接异常。按用户安排，Demo最终签认后再讨论所选基准的问题集、参考答案和盲评。当前不改解析库、不新增动态渲染器、不提前开展基准。

**结论：B07接口实机技术验收完成，B08规定的回归、五域名采样、内容复核、真实Agent和资源观测已完成；GNU站点内容仍blocked，保留部分完成例外。正式G5待用户阅读此具体报告并明确签认，尚未合入main。**
