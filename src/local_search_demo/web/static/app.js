/* B05 browser presentation only. All search/read logic stays in Python Core.
 * Untrusted titles, snippets and extracted HTML are always rendered as text.
 */
"use strict";

const $ = (id) => document.getElementById(id);
const text = (value) => value === undefined || value === null ? "—" : String(value);

function node(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = text(value);
  return element;
}
function safeExternalLink(url, label) {
  const anchor = node("a", "", label);
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "https:" || parsed.protocol === "http:") {
      anchor.href = parsed.href;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
    }
  } catch (_error) { /* leave unsafe URLs unlinked */ }
  return anchor;
}
function metadata(parent, pairs) {
  const row = node("div", "pills");
  for (const [name, value] of pairs) {
    const pill = node("span", "pill", name + ": " + text(value));
    row.append(pill);
  }
  parent.append(row);
}
function setStatus(kind, message, error = false) {
  const el = $(kind + "-status");
  el.textContent = message;
  el.classList.toggle("error", error);
}
function clearResults(kind) { $(kind + "-results").replaceChildren(); }
function statusCode(data) { return data && data.status ? String(data.status) : "NOT_RUN"; }

async function send(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  let data;
  try { data = await response.json(); }
  catch (_error) { throw Error("服务器响应不是 JSON（HTTP " + response.status + "）"); }
  if (!response.ok) {
    throw Error("HTTP " + response.status + " / " + (data.detail
      ? JSON.stringify(data.detail) : data.message || "请求失败"));
  }
  return data;
}
function errorText(items) {
  if (!items || !items.length) return "";
  return items.map((e) => (e.kind || "ERROR") + "：" + (e.message || "未知错误")).join("；");
}
function renderSearch(record) {
  const target = $("search-results");
  const search = record.search || {};
  const items = search.items || [];
  for (const item of items) {
    const card = node("article", "result-card");
    const heading = node("h3");
    heading.append(safeExternalLink(item.url, item.title || "(无标题)"));
    card.append(heading);
    const uri = node("div", "micro");
    uri.append(safeExternalLink(item.url, item.url));
    card.append(uri);
    if (item.snippet) card.append(node("p", "", item.snippet));
    metadata(card, [["排名", item.rank], ["引擎", (item.engines || []).join(" / ") || "未知"]]);
    target.append(card);
  }
  if (!items.length) target.append(node("div", "result-card", "本次请求没有获得可显示的 URL 结果。"));
  if ((search.errors || []).length) {
    target.append(node("div", "result-card", "上游提示：" + errorText(search.errors)));
  }
  setStatus("search", "状态 " + statusCode(search) + " · " + items.length +
    " 条结果 · " + text(search.elapsed_ms) + " ms · HTTP " + text(search.http_status),
    statusCode(search) !== "PASS" && statusCode(search) !== "EMPTY");
}
function renderRead(record) {
  const target = $("read-results");
  const fetchInfo = record.fetch || {};
  const fetchCard = node("section", "result-card");
  fetchCard.append(node("h3", "", "01 / 下载观察"));
  const requested = node("div", "micro", "请求 URL：" + text(fetchInfo.url_requested));
  const final = node("div", "micro", "最终 URL：" + text(fetchInfo.url_final));
  fetchCard.append(requested, final);
  metadata(fetchCard, [
    ["状态", fetchInfo.status], ["HTTP", fetchInfo.http_status],
    ["字节", fetchInfo.bytes], ["编码", fetchInfo.encoding],
    ["类型", fetchInfo.content_type], ["耗时", text(fetchInfo.elapsed_ms) + " ms"],
  ]);
  if ((fetchInfo.redirect_history || []).length) {
    fetchCard.append(node("p", "", "重定向路径：" + fetchInfo.redirect_history.join(" → ")));
  }
  if (fetchInfo.error) fetchCard.append(node("p", "", errorText([fetchInfo.error])));
  target.append(fetchCard);

  const chosenCard = node("section", "summary");
  chosenCard.append(node("h3", "", "02 / 候选正文 · " +
    text(record.selected_parser || "未选出")));
  chosenCard.append(node("p", "", record.selection_reason || "无候选选择依据"));
  if (record.selected_text) chosenCard.append(node("pre", "", record.selected_text));
  else chosenCard.append(node("p", "", "未得到可用正文，原始下载和三解析器状态仍保留在下方。"));
  target.append(chosenCard);

  const head = node("h3", "", "03 / 解析器独立输出");
  target.append(head);
  const grid = node("div", "parser-grid");
  const evidence = record.selection_evidence || [];
  for (const item of (record.parsers || [])) {
    const card = node("article", "result-card parser-card");
    const heading = node("h3", "", item.name);
    const pill = node("span", "pill " + (item.status === "PASS" ? "ok" : "fail"), item.status);
    heading.append(pill);
    card.append(heading);
    metadata(card, [["字符", item.chars], ["耗时", text(item.elapsed_ms) + " ms"]]);
    if (item.title) card.append(node("p", "", "标题：" + item.title));
    if (item.error) card.append(node("p", "", errorText([item.error])));
    const evaluation = evidence.find((entry) => entry.name === item.name);
    if (evaluation) card.append(node("p", "", "评分：" + text(evaluation.score) +
      " · " + text(evaluation.reason)));
    card.append(node("pre", "", item.text || "(无正文)"));
    const raw = node("details");
    const rawLabel = node("summary", "", "查看解析器原始输出");
    raw.append(rawLabel, node("pre", "", item.raw_output || "(无原始输出)"));
    card.append(raw);
    grid.append(card);
  }
  target.append(grid);
  setStatus("read", "下载 " + statusCode(fetchInfo) + " · " +
    (record.parsers || []).length + " 个解析器 · 当前候选：" +
    text(record.selected_parser || "无") + " · 全程 " + text(record.total_elapsed_ms) + " ms",
    statusCode(fetchInfo) === "FAIL");
}
function renderAgent(record) {
  const target = $("agent-results");
  const agent = record.agent || {};
  const summary = node("section", "summary");
  summary.append(node("h3", "", "模型最终回答 · " + text(agent.status)));
  summary.append(node("pre", "", agent.answer || "(模型没有返回完整回答)"));
  if (agent.error) summary.append(node("p", "", errorText([agent.error])));
  metadata(summary, [
    ["模型", agent.model], ["回合", agent.rounds],
    ["工具调用", (agent.tool_calls || []).length],
    ["总耗时", text(record.total_elapsed_ms) + " ms"],
  ]);
  target.append(summary);
  const calls = agent.tool_calls || [];
  for (const [i, call] of calls.entries()) {
    const card = node("article", "result-card");
    card.append(node("h3", "", "工具 " + (i + 1) + " · " + text(call.name)));
    metadata(card, [["状态", call.status], ["耗时", text(call.elapsed_ms) + " ms"],
      ["Call ID", call.call_id]]);
    if (call.error) card.append(node("p", "", errorText([call.error])));
    const details = node("details");
    details.append(node("summary", "", "查看参数和工具结果"));
    details.append(node("pre", "", JSON.stringify({
      arguments: call.arguments, result: call.result,
    }, null, 2)));
    card.append(details);
    target.append(card);
  }
  if (agent.cited_urls && agent.cited_urls.length) {
    const card = node("section", "result-card");
    card.append(node("h3", "", "已核验引用"));
    for (const url of agent.cited_urls) {
      const line = node("p");
      line.append(safeExternalLink(url, url));
      card.append(line);
    }
    target.append(card);
  }
  if (agent.unverified_citations && agent.unverified_citations.length) {
    target.append(node("section", "result-card",
      "未核验的链接引用：" + agent.unverified_citations.join("；")));
  }
  setStatus("agent", "模型状态 " + text(agent.status) +
    " · 工具 " + calls.length + " 次 · 回合 " + text(agent.rounds),
    agent.status !== "DONE");
}
function setupTabs() {
  const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
  function select(tab) {
    for (const button of tabs) {
      const active = button === tab;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      $(button.getAttribute("aria-controls")).hidden = !active;
    }
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = tabs.length - 1;
      else return;
      event.preventDefault();
      select(tabs[next]);
      tabs[next].focus();
    });
  });
}
function bindForm(formId, kind, endpoint, buildPayload, render) {
  $(formId).addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $(formId).querySelector('button[type="submit"]');
    button.disabled = true;
    clearResults(kind);
    setStatus(kind, "正在请求本地 Core…");
    try {
      const data = await send(endpoint, buildPayload());
      render(data);
    } catch (error) {
      setStatus(kind, error.message || "请求失败", true);
    } finally {
      button.disabled = false;
    }
  });
}
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  bindForm("search-form", "search", "/api/search", () => ({
    query: $("search-query").value,
    limit: Number($("search-limit").value),
    language: $("search-language").value || null,
  }), renderSearch);
  bindForm("read-form", "read", "/api/read", () => ({url: $("read-url").value}), renderRead);
  bindForm("agent-form", "agent", "/api/agent", () => ({
    question: $("agent-question").value,
    tool_choice: $("agent-choice").value,
    allow_live_read: $("agent-live-read").checked,
  }), renderAgent);
});
