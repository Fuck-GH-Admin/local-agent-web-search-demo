# B00 本机技术验收

执行日期：2026-10-13。范围：执行计划 B00/G0。工作分支：`b00/environment-baseline`。
起点：`e90892ed9d278978fff3a583f96ec271d9c45ea5`。实测实现提交：`eb8c626c582ec515aa0cb96060d77f33aa4e6a5c`；证据在后续本地提交保存，见实施台账。

**结论：B00 实施完成，本机 G0 技术检查 PASS。** 人工阶段签认尚未发生；该结论来自实际本机命令和独立虚拟环境重建，不代表用户已签认。B01–B08 均为 NOT_RUN，本轮没有进入下一批。

## 实测环境与依赖

Linux x86_64，CPython 3.12.13，uv 0.12.5。完整系统与包信息见 `reports/B00/environment.json`。

| 组件 | 实际安装版本 |
| --- | --- |
| HTTPX（网页获取层） | 0.28.1 |
| HTTPX2（OpenAI SDK 的传递依赖） | 2.13.1 |
| Trafilatura | 2.3.1 |
| readability-lxml | 0.9 |
| Selectolax | 0.4.13 |
| OpenAI SDK | 3.29.0 |
| FastAPI | 0.143.0 |
| Uvicorn | 0.54.0 |
| Pydantic | 2.14.1 |
| pytest | 9.1.1 |

`uv.lock` 与带 SHA-256 的 `requirements.lock` 锁定实际依赖；构建后端 setuptools 80.9.0、wheel 0.45.1 也明确固定。
另一虚拟环境使用导出的哈希锁安装，未重新挑选包版本；Python 版本、完整已安装包版本表、依赖锁哈希逐项相等。
Python 的其他版本和 Windows 没有实测，不据此宣称跨端兼容。

## 六份上游与实际阅读

全部为 GitHub 完整 clone，Selectolax 使用递归 clone。工作目录 `.references/upstream/` 已被 Git 忽略。
每份 SHA、远端 URL、许可证文件哈希和子模块记录位于 `upstream-lock.json`；clone 原始结果位于 `reports/B00/upstream-clones.json`。

| 上游 | 固定 HEAD（前 12 位，完整值见锁） | 许可证文件标识 |
| --- | --- | --- |
| SearXNG | 22c64b8d394b | AGPL-3.0-or-later |
| HTTPX | b5addb64f016 | BSD-3-Clause |
| Trafilatura | e2f85c965662 | Apache-2.0 |
| Selectolax | c68e5986ea54 | MIT |
| python-readability | 3e7a8321383b | Apache-2.0 |
| openai-python | 1f05e33eaca6 | Apache-2.0 |

Selectolax 的 Lexbor 子模块：`f4cbbcd91359a0ec9499e3ce7e263de629482d61`，已初始化且与主仓库指针一致。
表中许可证标识是本地文件事实记录；没有开展分发合规验收。

阅读了原仓库全部三份文档，以及六份本地上游 README、顶层许可证，并复核以下文档/源码位置：

- SearXNG：`docs/dev/search_api.rst` 确认 JSON format 必须启用，未启用可返回 403。
- HTTPX：`httpx/_client.py`、`httpx/_config.py` 定位 AsyncClient 与 Timeout。
- Trafilatura：`trafilatura/core.py` 定位 extract/bare_extraction；README 明确其包含 readability 类型回退。
- python-readability：README 的调用范例与 `readability/readability.py` 的 title/summary；summary 返回 HTML。
- Selectolax：README 的 LexborHTMLParser 示例及递归 clone 说明。
- openai-python：README、`pyproject.toml`、`src/openai/_base_client.py`；本次固定版本为 3.29.0，源码传输依赖为 HTTPX2。

据此把 SDK 依赖范围调整到 3.x，并实际导入 HTTPX 与 HTTPX2 两套模块。未修改六个上游仓库，也没有将上游源码当作本项目模块导入。

## 交付与检查

| B00 要求 | 本机结果 | 证据 |
| --- | --- | --- |
| 从 main 建工作分支、建立台账 | PASS | Git 分支、`IMPLEMENTATION_LEDGER.md` |
| 忽略源码参考目录、虚拟环境和凭据 | PASS | `.gitignore`、Git 忽略检查 |
| 六份源码、完整 SHA、Selectolax 子模块 | PASS | `upstream-lock.json`、clone 输出、restore 检查 |
| 可安装包、虚拟环境与依赖锁 | PASS | `pyproject.toml`、两种锁、环境报告、依赖完整性检查 |
| 六个统一模型与 JSON 序列化 | PASS | `src/local_search_demo/schemas.py`、嵌套 Unicode/失败记录回归 |
| 六类 HTML 与搜索 JSON 样本 | PASS | 6 个 HTML、5 个 JSON、独立 manifest 和哈希检查 |
| 模块/console 入口帮助 | PASS | `test-summary.txt` 与从其他目录启动的测试 |
| 最小 pytest 可发现并运行 | PASS | **32 passed**；`pytest.xml`、`test-summary.txt` |
| 独立环境重建 | PASS | **32 passed**；`rebuild-summary.txt`、`rebuild-check.json`、重建环境报告 |
| SearXNG 部署、真实搜索、解析质量、真实模型 | NOT_RUN | 属于 B01–B08 |
| 用户人工阶段签认 | NOT_RUN | 本轮只保存实际本机技术证据，不代替用户签认 |

核心协议字段沿用执行计划第 3 节。新增 SearchItem、ErrorDetail、ToolCall 辅助模型；新增下载编码与 HTML 文件路径用于后续记录；没有删除或重新解释既定主字段。
未执行的阶段保持 null，候选列表为空也不会自动判定成功。基础骨架预留 search/fetch/parsers/pipeline/agent 包及 deploy/web 目录；不提前实现后续批次算法。

32 项测试覆盖固定输入完整性、六类 HTML 含 SPA 负例、嵌套记录 JSON 往返与中文、未执行字段、非法指标/未知字段、依赖符号导入、环境报告不收集令牌、两个入口及未来命令明确返回 NOT_IMPLEMENTED。
样本预期锚点是后续解析验收用输入，所有解析质量评价仍为 NOT_RUN。

## 复现命令与证据

README 给出了依赖、上游、入口、pytest 的完整重建步骤。主要命令：

```bash
python3 scripts/restore_upstreams.py
uv sync --locked --all-extras
.venv/bin/python scripts/verify_b00.py
bash scripts/rebuild_environment.sh .venv-fresh
```

`verify_b00.py` 会生成环境报告、逐命令状态、文本输出和 pytest JUnit XML。
`rebuild_environment.sh` 要求目标目录不存在，并使用 `--require-hashes` 安装全部依赖，再以 `--no-deps --no-build-isolation` 安装本项目。
本次实际重建目录为 `.venv-rebuild/`，输出已保存到 `reports/B00/rebuild-summary.txt`，全量包表比较见 `rebuild-check.json`。
实现提交后再次在两个环境复核，均为 32 PASS；第二环境的提交后输出保存于 `rebuild-verification.txt`，两份 environment.json 的 revision 均指向上述实现提交。最初重建日志保留提交前的实际输出。
本轮代码和证据仅本地提交，远端没有更新。

## 后续与未解决项

没有阻断 B00 的技术问题，也没有网络豁免或伪造 SHA。后续批次需按原计划开展。
SearXNG 镜像 digest 在 B01 实际部署时记录；此时没有拉取镜像，不填写虚构 digest。
进入 B01 前应由用户复核本批 G0 证据并作阶段确认。本轮任务范围止于 B00。
