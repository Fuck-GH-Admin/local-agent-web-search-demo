# B05 / G3 Ubuntu 本机浏览器验收记录（模板）

> **状态：NOT_RUN。** 此文件仅供本地 Agent / 用户执行并填写，不得将空白模板当成通过证据。

执行机器（可脱敏）：  
Python / uv 版本：  
浏览器及版本：  
Git commit SHA：  
测试时间与时区：  
SearXNG 地址：127.0.0.1:8080 或自行填写非敏感地址  
WebUI 地址：127.0.0.1:8765  

## 准备与自动回归

- [ ] `uv sync --locked --all-extras`，退出码：
- [ ] `uv run --locked pytest -q`，结果：
- [ ] `uv run --locked python scripts/b05-api-parity.py`，`api-tests.json` 中 5/5 PASS：
- [ ] `uv run --locked uvicorn local_search_demo.web.api:app --host 127.0.0.1 --port 8765`，服务可达：

## G3 实际浏览器逐项核验

- [ ] 访问 `http://127.0.0.1:8765/`，三个页签可切换；键盘左右键可操作标签。
- [ ] 关键词 `python asyncio` 真实搜索展示 URL、摘要、来源引擎，并核对 CLI `search`；结果或错误截图：
- [ ] 关键词 `无人机 电磁干扰` 真实搜索，记录引擎状态/错误及时间；截图：
- [ ] 网页读取真实文章地址：___；展示 HTTP/原始与最终 URL、解析器文本及选择理由；与 CLI 对比；截图：
- [ ] 技术文档地址：___；三解析器可展开原始输出，不用“字符最多”冒充准确率；截图：
- [ ] 模拟空正文与失效 URL（可用 fixture 服务/404）：界面未编造正文，且出错后能继续使用；截图：
- [ ] Agent 页签明确不可用；`POST /api/agent` 返回 501，无虚假工具 trace；截图：
- [ ] 桌面与窄视口均可阅读，浏览器控制台 JS 错误为零或逐项记录；截图：
- [ ] 检查公开监听（仅 127.0.0.1），没有将开发站暴露给 LAN/公网：
- [ ] 检查截图/报告无 API Key、Cookie、私人 URL 或其它敏感信息：

## 对照差异与缺陷

CLI/API 具体不一致字段（若无写“无”）：  
前端显示问题：  
网络/代理问题：  
未完成的事项及原因：  
复现操作：  

## 结论

G3：**NOT_RUN**（由实机测试者完成后改为 PASS / FAIL / BLOCKED）  
执行与复核人：  
签认来源（本会话或 commit）：  
证据文件路径（截图、报告）：  

> 签认后同时更新 `docs/OPEN_VALIDATION_INDEX.md` 的 `B05-G3-01`、`docs/B05_ACCEPTANCE.md` 和 `docs/IMPLEMENTATION_LEDGER.md`；保留所有未通过和补验记录。
