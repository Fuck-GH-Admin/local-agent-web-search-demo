> **首读：** [本机开发环境与调试协作说明](./LOCAL_DEV_ENVIRONMENT.md)，其中区分 B00 必装项与 B01 以后才需要的 Docker/模型环境。

# B00 本机复现与补验步骤

首轮平台：Linux，Python 3.11+；当前测试容器为 Python 3.13.5，但并不能代替用户 Linux 主机的实测。

```bash
# From repository root. Do NOT add upstream repos to git.
mkdir -p .references/upstream
bash scripts/clone-upstream.sh  # six git clones; needs Github access
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m local_search_demo doctor
python -m pytest -q
python -m local_search_demo --help
python scripts/local-diagnostics.py --network  # reports/local/preflight.json；只读、报告默认不上传
python scripts/b00-g0-check.py  # packages/imports/pip check/pytest/CLI -> reports/B00/g0-local-check.json
```

`doctor` 只检查安装/配置，不代表搜索或 Agent 已运行；`search` / `read` / `agent` 在 B00 明确返回 `not_implemented` 和退出码 3。

锁定步骤：在依赖完全安装后的**同一环境**运行 `python -m pip freeze > requirements-resolved.txt`，并记录 Python、OS、各上游源码 SHA。`requirements-resolved.txt` 属环境快照；是否改用更严格的锁文件由 B00 复验决定。不要锁定本次缺依赖容器中的残缺集合。

查看公开代码与设置来源请读 `docs/UPSTREAM_RESEARCH.md`。未进行网络请求，也未设置任何 API 密钥。

`b00-g0-check.py` 同时检查六份 clone SHA、九项必需包、真实 import、pip check、pytest、doctor、CLI 帮助，以及 `search` 未实现的预期退出码。**只有报告为 `PASS` 才能把 G0 改为通过**。若仍是 `BLOCKED_LOCAL`，保留原报告并根据 `missing_upstream`、`missing_packages` 补齐，不得以现有 10 个离线测试冒充整体通过。
