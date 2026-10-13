# 本地开发机准备与远程协作调试（B00–B08）

> 2026-10-13 增补。适用于 Linux/Ubuntu 首轮可行性验证，目标是**最少安装、可复现、能回传实测证据**。这里描述的是准备工作，不代表已经在用户机器上执行。
>
> 本项目开发分支：`feat/b00-foundation`。本机诊断与 G0 验收结果必须在本机真实执行才可信。

## 1. 结论：安装什么？什么时候安装？

| 优先级 | 本地依赖 | 用途 / 是否必须 | 验证命令 |
|---|---|---|---|
| **B00 必须** | Git | 获取我方分支、克隆六个上游项目，上传验收证据 | `git --version` |
| **B00 必须** | Python **3.11+**（推荐 3.12）、venv、pip | Python Core、CLI、pytest 和包管理，隔离系统环境 | `python3 --version`；`python3 -m venv --help` |
| **B00 必须** | 可联网的 GitHub / PyPI | 克隆源码、下载 Python 依赖（已有内网镜像亦可） | `python scripts/local-diagnostics.py --network` |
| **B00 必须** | 独立虚拟环境及项目依赖 | `pip install -e '.[dev]'`；实际导入测试与 G0 | `python scripts/b00-g0-check.py` |
| **B01 必须** | Docker Engine + **Docker Compose v2** 插件 | 自建 SearXNG、管理服务并采集容器日志 | `docker info`; `docker compose version` |
| **B01 推荐** | curl | 搜索 JSON API 联网烟测；也便于排错 | `curl --version` |
| **B01 可选** | jq | 美化阅读 JSON | `jq --version` |
| **B06/B07 才需** | 可调用工具的模型/API 地址 | Agent 实际 Function Calling；要验证目标提供商的 API 模式 | 在 B07 用本地测试命令检验 |
| **目前不需** | Chrome / Chromium / Playwright / Node.js / GPU / Redis / PostgreSQL / PDF/OCR 工具 | 不属于此次可行性验证范围 | 不安装 |

说明：
- Python 包内已有 HTTPX、Trafilatura、readability-lxml、Selectolax、OpenAI SDK、FastAPI、Uvicorn、Pydantic、pytest 等依赖声明。**不要全局 pip install**；在 venv 安装即可。Python 3.11 只是最低版本，Linux 的系统 `python3` 可能更老，先检查实际版本。
- Docker 的安装按本机 Ubuntu 发行版使用官方 Docker Engine / Compose v2 文档；B00 **不要求** Docker 已运行（B01 才用）。无需提前安装 SearXNG。
- SDK 本身无需搜索 API，但**模型提供商可能计费**；正式真实模型测试到 B07 才需要密钥。不应提前把真实 API Key 写进仓库。
- 开发机不需要 NVIDIA 显卡；这个 Demo 不进行本地大模型训练或浏览器渲染。
- 故障定位中 Docker socket 权限与 daemon 未启动不同：`docker --version` 通过不代表 `docker info` 通过。

## 2. 建议在本机执行的准备命令

以 Linux/Ubuntu 为例，不对系统 Python 进行覆盖安装。先确保 `python3` 是 3.11+；否则选择机器上已有的 `python3.11` / `python3.12`。

```bash
# 第一次：clone 我方开发分支（不要直接基于 main 测 B00）
git clone --branch feat/b00-foundation --single-branch \
  https://github.com/Fuck-GH-Admin/local-agent-web-search-demo.git
cd local-agent-web-search-demo

python3 --version
git --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

# 六份参考源码：存放在被 .gitignore 排除的目录，永远不要 git add。
bash scripts/clone-upstream.sh

# 环境检测，网络检查为显式选择；不会访问模型/API Key。
python scripts/local-diagnostics.py --network

# 正式 G0 验收（检查源码 SHA、已安装包、真实 import、
# pip check、pytest、CLI 行为）
python scripts/b00-g0-check.py
```

**若旧版本系统的 `python3` 小于 3.11**：不要强行修改系统默认解释器；改用明确的可用 Python 版本创建 venv。  
**若网路/代理未配置好**：先运行 `python scripts/local-diagnostics.py --network` 识别 GitHub/PyPI/容器镜像仓库的 DNS/HTTPS 失败，不要根据 Python 错误猜测是应用逻辑问题。

`scripts/clone-upstream.sh` 在再次执行时会保留现有 clone（**不会自动 fetch 更新已有版本**）。在记录 SHA 后固定测试用版本，避免今天/明天源码无声漂移；不要把六个上游仓库 commit 进主项目。

## 3. 为后续调试准备的诊断信息

`python scripts/local-diagnostics.py` 是轻量、只读的环境预检：

- Python、OS、架构、CPU 数量、总内存、工作目录剩余空间；
- Git/Docker/Compose/curl 的存在与版本、Docker daemon 是否可访问；
- 关键 Python 包版本、六份 upstream clone SHA、当前 Git 分支/commit；
- 本地 8080（搜索）与 8765（WebUI）端口是否已有监听；
- **仅检查** HTTP_PROXY/HTTPS_PROXY/NO_PROXY 变量是否设置，**绝不记录值**；
- 只有加 `--network` 才做对固定公开域名的 DNS/HTTPS 连接检查：github.com、pypi.org、registry-1.docker.io。

存档位置：`reports/local/preflight.json`，此目录已被 `.gitignore` 排除。不会自动上传 GitHub；请先检查内容再决定是否分享。

**解读注意**：端口正在监听 ≠ 服务健康；curl 能连通 HTTPS ≠ 搜索上游可返回结果；DNS 正常 ≠ Docker 容器内网络正常。B01 对 SearXNG JSON 要做自己的真实烟测。

B00 G0 的更严格验收脚本 `scripts/b00-g0-check.py` 会额外实际运行 `pip check`、依赖 import、pytest 和 CLI，输出：
- `reports/B00/g0-local-check.json`
- 仅 G0 PASS 时写入 `reports/B00/requirements-resolved.txt`

与其他生成文件一样，这些报告必须按“本机实际执行”标记。当前分支中先前的 `reports/B00/verification.json` 仅证明云端临时容器的离线执行，**不能代表用户本机已经通过 G0**。

## 4. 如何把本地证据回传给我（最重要）

**我通过 GitHub 连接器能够读取你提交到私有仓库的文件、commit 和 CI，但不能直接操作你的 Linux 主机，也不能自动读取你的本地日志。**

建议最简单的交接流程：

1. 在本地运行诊断和 G0，打开生成的 JSON，确认没有你不想分享的机器信息；诊断脚本默认不收集密钥。
2. 如果要让我分析，将 `reports/local/preflight.json` **人工检查后**复制为 `reports/B00/local-preflight-summary.json`。
3. 只选这些报告进行 git add，再 push 当前工作分支；不要盲目 `git add .`：

```bash
cp reports/local/preflight.json reports/B00/local-preflight-summary.json
git add reports/B00/local-preflight-summary.json reports/B00/g0-local-check.json
# 如果 G0 PASS，且检查后确认版本列表可公开给仓库成员，再加：
# git add reports/B00/requirements-resolved.txt
git diff --cached --stat
git diff --cached                       # 上传前人工检查
git commit -m "test(B00): attach local G0 evidence"
git push origin feat/b00-foundation
```

也可以只上传报告文件到对话，不必先提交代码；但**GitHub 提交更方便跨会话追踪**。不需要把 `.env`、真实 Key、代理凭据、Cookie、原始模型请求头或整段家庭网络配置上传。

若本机 G0 仍阻塞，请保留 FAIL/BLOCKED 的原始原因，不改写为 PASS。提交后即可用报告确定问题属于：系统环境、DNS/HTTPS、容器运行权限、Python 依赖、GitHub clone、测试用例还是模型端。

## 5. 从 B01 到 B08 的本机调试辅助（按需开启）

- **B01**：启动 SearXNG；查看 `docker compose ps`、`docker compose logs --tail=100`、JSON 查询返回的 HTTP 状态及 `unresponsive_engines`。检查容器内部的联网与代理，**主机能上网不等于容器能上网**。
- **B02–B04**：每次网络抓取保留 URL、最终 URL、HTTP 状态、Content-Type、下载/解析耗时、解析器单独结果；不要上传大批原始 HTML，优先提供失败网页及精简片段。
- **B05**：记录 WebUI 的请求路径、HTTP 状态和与 CLI 相同的 Core JSON 输出；浏览器只用于**展示我们的本地界面**，不用于远端网页抓取。
- **B06–B07**：准备一个明确支持 `tools` 的 OpenAI 兼容模型；将 `base_url`、`model`、`api_mode` 和是否支持多次工具调用作为测试参数记录。Key 仅放本机环境/未跟踪的配置中。
- **B08**：可补充一次 `docker stats --no-stream` 及进程/内存占用快照；**只记录实际结果**，不假设 2C2G 必然足够。

## 6. 是否需要专门配置“让我远程操作你的电脑”？

**不需要。** 第一版推荐“GitHub 管代码 + 本机跑真实环境 + JSON 日志回传”。这样无需开放 SSH、反向隧道或在机器上常驻 Agent。

如果之后本机验收频繁，我们可以再考虑 **GitHub Actions 离线 CI**，用于每次 push 自动运行固定的 pytest。它能帮助我检查回归，却不能证明你的家庭网络、Docker/SearXNG 上游或本机运行表现。自托管 Runner 不属于 B00 必需项。

## 7. G0 本机验收状态

截至编写本文，`feat/b00-foundation` 上的基础代码/离线测试已完成，但**尚未收到用户本机 G0 检查结果**。之前的 `10 passed` 来自其他运行环境；六个上游 clone/本机完整依赖验证仍应标为待补验。通过后再在 `docs/IMPLEMENTATION_LEDGER.md` 中更新结果。
