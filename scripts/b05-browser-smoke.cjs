/* Optional G3 host QA driver. Playwright is external QA tooling, not an app dependency.
 * Uses a real headed Chrome on an Xvfb display, real forms, HTTP and screenshots.
 * Requires running WebUI :8765, fixture origin :8766, SearXNG :8080, Chrome and Xvfb.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const { spawn, execFileSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const assert = require("node:assert/strict");
const { chromium } = require(process.env.B05_PLAYWRIGHT_PATH || "playwright");
const root = path.resolve(__dirname, "..");
const out = path.join(root, "reports/B05");
const raw = path.join(out, "raw");
const images = path.join(out, "screenshots");
const base = "http://127.0.0.1:8765";
const fixture = "http://127.0.0.1:8766";
const hash = (v) => createHash("sha256").update(v || "").digest("hex");
const save = (name, value, directory = out) => fs.writeFileSync(path.join(directory, name), JSON.stringify(value, null, 2) + "\n");
for (const directory of [out, raw, images]) fs.mkdirSync(directory, { recursive: true });
const report = {
  batch: "B05", kind: "host_real_headed_browser_QA", started_utc: new Date().toISOString(),
  implementation_commit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
  operator: "Codex via Playwright; screenshots separately inspected by Codex",
  g3_status: "AWAITING_USER_REVIEW", checks: [], observations: [], screenshots: [],
  page_errors: [], console_messages: [], network: [],
};
function check(name, detail) { report.checks.push({ name, pass: true, detail }); console.log("PASS " + name); }
function readSummary(data) {
  return {
    mode: data.mode, url: data.url, fetch: data.fetch,
    selected_parser: data.selected_parser, selected_text_sha256: hash(data.selected_text),
    selected_chars: (data.selected_text || "").length, selection_reason: data.selection_reason,
    selection_evidence: data.selection_evidence, total_elapsed_ms: data.total_elapsed_ms,
    parsers: data.parsers.map((p) => ({ name: p.name, status: p.status, title: p.title,
      chars: p.chars, elapsed_ms: p.elapsed_ms, error: p.error, metadata: p.metadata,
      text_sha256: hash(p.text), raw_output_sha256: hash(p.raw_output) })),
  };
}
async function main() {
  let browser, xvfb;
  try {
    xvfb = spawn("Xvfb", ["-displayfd", "1", "-screen", "0", "1600x1200x24", "-nolisten", "tcp"], { stdio: ["ignore", "pipe", "pipe"] });
    xvfb.stderr.on("data", (chunk) => fs.appendFileSync(path.join(raw, "xvfb.log"), chunk));
    const display = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(Error("Xvfb display allocation timed out")), 10000);
      xvfb.once("error", reject);
      xvfb.stdout.once("data", (chunk) => { clearTimeout(timeout); resolve(":" + chunk.toString().trim()); });
    });
    browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: false,
      env: { ...process.env, DISPLAY: display }, args: ["--no-sandbox"] });
    report.browser = { version: browser.version(), headed: true, display_backend: "Xvfb", QA_library: "Playwright" };
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "zh-CN" });
    const page = await context.newPage();
    page.on("pageerror", (e) => report.page_errors.push({ name: e.name, message: e.message }));
    page.on("console", (m) => report.console_messages.push({ type: m.type(), text: m.text(), location: m.location() }));
    page.on("response", (r) => report.network.push({ url: r.url(), method: r.request().method(), status: r.status() }));
    async function shot(name, locator) {
      const filename = name + ".png";
      if (locator) await locator.screenshot({ path: path.join(images, filename) });
      else await page.screenshot({ path: path.join(images, filename), fullPage: true });
      report.screenshots.push({ file: "reports/B05/screenshots/" + filename, sha256: hash(fs.readFileSync(path.join(images, filename))) });
    }
    async function submit(formId, endpoint) {
      const pending = page.waitForResponse((r) => r.url() === base + endpoint && r.request().method() === "POST", { timeout: 25000 });
      await page.locator("#" + formId + ' button[type="submit"]').click();
      const response = await pending;
      const data = await response.json();
      await page.waitForFunction((id) => !document.querySelector("#" + id + ' button[type="submit"]').disabled, formId);
      assert.equal(response.status(), 200);
      return data;
    }
    async function read(name, url) {
      await page.locator("#tab-read").click();
      await page.locator("#read-url").fill(url);
      const data = await submit("read-form", "/api/read");
      save(name + ".json", data, raw);
      const cards = page.locator(".parser-card");
      assert.equal(await cards.count(), 3);
      for (let i = 0; i < 3; i++) {
        const card = cards.nth(i), p = data.parsers[i];
        assert.ok((await card.locator("h3").textContent()).startsWith(p.name));
        assert.equal(await card.locator(":scope > pre").textContent(), p.text || "(无正文)");
        assert.equal(await card.locator("details pre").textContent(), p.raw_output || "(无原始输出)");
        assert.ok((await card.locator("h3 .pill").textContent()) === p.status);
      }
      if (data.selected_text) assert.equal(await page.locator("#read-results .summary pre").textContent(), data.selected_text);
      else assert.ok((await page.locator("#read-results .summary").textContent()).includes("未得到可用正文"));
      const dom = await page.locator("#read-results").innerText();
      assert.ok(dom.includes("请求 URL：" + data.fetch.url_requested));
      assert.ok(dom.includes("最终 URL：" + (data.fetch.url_final || "—")));
      if (data.fetch.error) assert.ok(dom.includes(data.fetch.error.kind));
      report.observations.push({ case: name, observed_utc: new Date().toISOString(), status_text: await page.locator("#read-status").innerText(), ...readSummary(data) });
      check(name + "_DOM_matches_HTTP_result", "All three text/raw/status fields, selected body and fetch metadata rendered from actual response");
      await shot(name);
      return data;
    }
    await page.goto(base, { waitUntil: "networkidle" });
    assert.equal(await page.title(), "Local Search · 验证控制台");
    await shot("desktop-home");
    await page.locator("#tab-search").focus();
    await page.keyboard.press("ArrowRight"); assert.equal(await page.locator("#tab-read").getAttribute("aria-selected"), "true");
    await page.keyboard.press("ArrowRight"); assert.equal(await page.locator("#tab-agent").getAttribute("aria-selected"), "true");
    await page.keyboard.press("Home"); assert.equal(await page.locator("#tab-search").getAttribute("aria-selected"), "true");
    check("tabs_and_keyboard", "Three real tabs switch with click/ArrowRight/Home");
    for (const [name, query, language] of [["search-en", "python asyncio", "en-US"], ["search-zh", "无人机 电磁干扰", "zh-CN"]]) {
      await page.locator("#tab-search").click();
      await page.locator("#search-query").fill(query);
      await page.locator("#search-language").selectOption(language);
      await page.locator("#search-limit").selectOption("5");
      const data = await submit("search-form", "/api/search"); save(name + ".json", data, raw);
      const count = await page.locator("#search-results article.result-card").count();
      assert.equal(count, data.search.items.length);
      assert.ok(count > 0 && data.search.status === "PASS", "Real keyword query must return useful results");
      const dom = await page.locator("#search-results").innerText();
      for (const item of data.search.items) { assert.ok(dom.includes(item.title)); assert.ok(dom.includes(item.url)); for (const engine of item.engines) assert.ok(dom.includes(engine)); }
      report.observations.push({ case: name, query, language, observed_utc: new Date().toISOString(), search: data.search });
      check(name + "_live_results", count + " actual SearXNG results rendered with titles, URLs and engines");
      await shot(name);
    }
    const article = await read("read-public-article", "https://www.python.org/doc/essays/blurb/");
    assert.equal(article.fetch.status, "PASS"); assert.ok(article.selected_text);
    const doc = await read("read-public-docs", "https://docs.python.org/3/library/asyncio.html");
    assert.equal(doc.fetch.status, "PASS"); assert.ok(doc.selected_text);
    for (const detail of await page.locator(".parser-card details").all()) await detail.locator("summary").click();
    assert.equal(await page.locator(".parser-card details[open]").count(), 3);
    check("three_raw_outputs_expand", "All three actual raw outputs can be opened in the browser");
    await shot("parser-raw-expanded", page.locator(".parser-grid"));
    const spa = await read("read-spa", fixture + "/spa");
    assert.equal(spa.selected_text, null); assert.ok(spa.parsers.every((p) => p.status === "EMPTY"));
    const missing = await read("read-404", fixture + "/missing");
    assert.equal(missing.fetch.http_status, 404); assert.ok(missing.parsers.every((p) => p.status === "NOT_RUN"));
    assert.ok((await page.locator("#read-status").getAttribute("class")).includes("error"));
    await context.setOffline(true);
    await page.locator("#read-url").fill(fixture + "/article");
    await page.locator('#read-form button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector("#read-status").classList.contains("error") && !document.querySelector('#read-form button[type="submit"]').disabled);
    report.observations.push({ case: "browser-offline", status_text: await page.locator("#read-status").innerText() });
    check("transport_failure_reenables_form", "Actual browser offline request rejected visibly; submit enabled again");
    await shot("browser-offline"); await context.setOffline(false);
    const recovered = await read("read-recovered", fixture + "/article"); assert.ok(recovered.selected_text);
    check("read_after_failure", "Same browser form successfully re-submitted after 404 and transport failure");
    const redirect = await read("read-redirect", fixture + "/redirect");
    assert.equal(redirect.fetch.url_final, fixture + "/article"); assert.equal(redirect.fetch.redirect_history.length, 1);
    await page.locator("#tab-search").click(); await page.locator("#search-query").fill("   ");
    const invalid = await submit("search-form", "/api/search"); assert.equal(invalid.search.errors[0].kind, "INVALID_QUERY");
    assert.ok((await page.locator("#search-results").innerText()).includes("INVALID_QUERY"));
    save("search-invalid.json", invalid, raw); check("search_error_visible", "Whitespace query displays Core INVALID_QUERY and re-enables submit"); await shot("search-invalid");
    await page.locator("#tab-agent").click();
    assert.ok((await page.locator("#panel-agent").innerText()).includes("尚未接入模型"));
    const agent = await page.evaluate(async () => { const r = await fetch("/api/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: "G3 actual endpoint check" }) }); return { status: r.status, data: await r.json() }; });
    assert.equal(agent.status, 501); assert.equal(agent.data.status, "NOT_IMPLEMENTED");
    report.observations.push({ case: "agent-placeholder", ...agent }); check("agent_501_placeholder", "Actual browser POST returns 501; panel supplies no model answer or trace"); await shot("agent-placeholder");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator("#tab-read").click();
    await read("mobile-read", fixture + "/article");
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth, parser_columns: getComputedStyle(document.querySelector(".parser-grid")).gridTemplateColumns }));
    assert.ok(dimensions.page <= dimensions.viewport, "Narrow page must not overflow horizontally");
    check("narrow_viewport", dimensions); await shot("mobile-parsers", page.locator(".parser-grid"));
    await page.locator("#tab-search").click(); await shot("mobile-search");
    assert.equal(report.page_errors.length, 0); check("no_unhandled_JS_errors", "No pageerror events during all real browser actions");
    report.status = "PASS";
    await context.close();
  } catch (error) {
    report.status = "FAIL"; report.failure = { message: error.message, stack: error.stack };
    process.exitCode = 1; console.error(error.message);
  } finally {
    if (browser) await browser.close(); if (xvfb) xvfb.kill();
    report.finished_utc = new Date().toISOString(); save("browser-observations.json", report);
    console.log(JSON.stringify({ status: report.status, checks: report.checks.length, screenshots: report.screenshots.length, page_errors: report.page_errors.length, g3_status: report.g3_status }));
  }
}
main();
