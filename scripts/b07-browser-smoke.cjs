/* Explicit host QA: actual Chrome/forms/API; model credentials stay server-side.
 * Playwright is external QA tooling, not a dependency of the Demo.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const {spawn, execFileSync} = require("node:child_process");
const {createHash} = require("node:crypto");
const assert = require("node:assert/strict");
const {chromium} = require(process.env.B07_PLAYWRIGHT_PATH || "playwright");
const root = path.resolve(__dirname, "..");
const raw = path.join(root, "reports/B07/interfaces/raw");
const published = path.join(root, "reports/B07/interfaces/validation/screenshots");
for (const dir of [raw, published]) fs.mkdirSync(dir, {recursive: true});
const base = process.env.B07_QA_BASE_URL || "http://127.0.0.1:8877";
const missing = "http://127.0.0.1:8879";
const fixture = "http://127.0.0.1:8880";
const hash = (value) => createHash("sha256").update(value).digest("hex");
const saveRaw = (name, data) => fs.writeFileSync(path.join(raw, name), JSON.stringify(data, null, 2) + "\n", {mode: 0o600});
const report = {batch: "B07", kind: "headed_Chrome_real_Agent_UI", started_utc: new Date().toISOString(),
  implementation_commit: execFileSync("git", ["rev-parse", "HEAD"], {cwd: root, encoding: "utf8"}).trim(),
  checks: [], screenshots: [], page_errors: [], real_model_scenarios: [], fixture_scenarios: []};
const check = (name, evidence) => {report.checks.push({name, pass: true, evidence}); console.log("PASS " + name);};
async function main() {
  let browser, xvfb;
  try {
    xvfb = spawn("Xvfb", ["-displayfd", "1", "-screen", "0", "1600x1200x24", "-nolisten", "tcp"], {stdio: ["ignore", "pipe", "ignore"]});
    const display = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(Error("Xvfb timed out")), 10000);
      xvfb.once("error", reject);
      xvfb.stdout.once("data", (data) => {clearTimeout(timer); resolve(":" + data.toString().trim());});
    });
    browser = await chromium.launch({executablePath: "/usr/bin/google-chrome", headless: false,
      env: {...process.env, DISPLAY: display}, args: ["--no-sandbox"]});
    report.browser = {version: browser.version(), headed: true, display_backend: "Xvfb"};
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, locale: "zh-CN"});
    const page = await context.newPage();
    page.on("pageerror", (error) => report.page_errors.push(error.message));
    async function shot(name, redacted = true) {
      await page.screenshot({path: path.join(raw, name + "-original.png"), fullPage: true});
      const target = path.join(published, name + ".png");
      await page.screenshot({path: target, fullPage: true,
        mask: redacted ? [page.locator("#agent-question"), page.locator("#agent-results pre"),
          page.locator("#agent-results a"), page.locator("#agent-results details"), page.locator("#agent-results .pills")] : [],
        maskColor: "#27334b"});
      report.screenshots.push({file: path.relative(root, target), sha256: hash(fs.readFileSync(target)),
        privacy: redacted ? "question/answer/source/results/identifiers masked at capture" : "no private model content"});
    }
    async function submit(name, question, allow = false) {
      await page.locator("#agent-question").fill(question);
      await page.locator("#agent-live-read").setChecked(allow);
      const response = page.waitForResponse((r) => r.url().endsWith("/api/agent") && r.request().method() === "POST", {timeout: 130000});
      await page.locator('#agent-form button[type="submit"]').click();
      const actual = await response;
      const data = await actual.json();
      saveRaw(name + ".json", data);
      await page.waitForFunction(() => !document.querySelector('#agent-form button[type="submit"]').disabled);
      return {status: actual.status(), data};
    }
    await page.goto(base, {waitUntil: "networkidle"});
    await page.locator("#tab-search").focus();
    await page.keyboard.press("End");
    assert.equal(await page.locator("#tab-agent").getAttribute("aria-selected"), "true");
    check("Agent_tab_keyboard_and_form", "Actual tab and keyboard navigation reveal the Agent form");
    const control = await submit("ui-control", "3+4 等于几？只回答数字。");
    assert.equal(control.status, 200); assert.equal(control.data.agent.status, "DONE");
    assert.equal(control.data.agent.answer.trim(), "7"); assert.equal(control.data.agent.tool_calls.length, 0);
    assert.ok((await page.locator("#agent-results").innerText()).includes(control.data.agent.answer));
    report.real_model_scenarios.push({name: "ui-control", status: "DONE", tools: 0, model_calls: control.data.agent.model_calls.length});
    check("real_UI_no_tool_control", "Actual model answer rendered from HTTP response; no tool calls");
    await shot("agent-control");
    const live = await submit("ui-live", "请搜索并阅读 Python asyncio 官方文档，根据网页简要说明用途和两个高层 API 能力，并引用你实际读取的来源。", true);
    assert.equal(live.status, 200); assert.equal(live.data.agent.status, "DONE");
    const trace = live.data.agent;
    assert.ok(trace.tool_calls.some((c) => c.name === "search_web" && c.status === "PASS"));
    assert.ok(trace.tool_calls.some((c) => c.name === "read_webpage" && c.status === "PASS" && c.result.selected_text));
    assert.ok(trace.cited_urls.length > 0); assert.equal(trace.unverified_citations.length, 0);
    const dom = await page.locator("#agent-results").innerText();
    assert.ok(dom.includes(trace.answer));
    for (const c of trace.tool_calls) {assert.ok(dom.includes(c.name)); assert.ok(dom.includes(c.call_id));}
    for (const url of trace.cited_urls) assert.ok(dom.includes(url));
    for (const details of await page.locator("#agent-results details").all()) await details.locator("summary").click();
    assert.equal(await page.locator("#agent-results details[open]").count(), trace.tool_calls.length);
    report.real_model_scenarios.push({name: "ui-live", status: "DONE", tools: trace.tool_calls.length,
      model_calls: trace.model_calls.length, verified_citations: trace.cited_urls.length, elapsed_ms: live.data.total_elapsed_ms});
    check("real_UI_search_read_cited_answer", "Actual response answer, tool IDs, tool results and citations agree with rendered DOM");
    await shot("agent-live-desktop");
    await page.setViewportSize({width: 390, height: 844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    check("Agent_narrow_viewport", "390px viewport with expanded tool results has no horizontal page overflow");
    await shot("agent-live-mobile");
    const blank = await submit("ui-invalid", "   "); assert.equal(blank.status, 422);
    assert.ok((await page.locator("#agent-status").getAttribute("class")).includes("error"));
    check("validation_failure_visible_and_form_recovers", "Actual HTTP 422 appears visibly and submit is re-enabled; no paid request");
    await shot("agent-validation-error");
    await context.setOffline(true);
    await page.locator("#agent-question").fill("offline QA");
    await page.locator('#agent-form button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector("#agent-status").classList.contains("error") && !document.querySelector('#agent-form button[type="submit"]').disabled);
    check("browser_network_failure_recovers", "Actual browser offline fetch fails visibly and form becomes usable again");
    await context.setOffline(false);
    await page.goto(missing, {waitUntil: "networkidle"}); await page.locator("#tab-agent").click();
    const notConfigured = await submit("ui-unconfigured", "configuration QA"); assert.equal(notConfigured.status, 503);
    assert.ok((await page.locator("#agent-status").innerText()).includes("MODEL_NOT_CONFIGURED"));
    check("missing_model_visible", "Actual unconfigured server reports HTTP 503 without credentials or fake answer");
    await shot("agent-unconfigured");
    await page.goto(fixture, {waitUntil: "networkidle"}); await page.locator("#tab-agent").click();
    const safety = await submit("ui-text-safety", "fixture text safety"); assert.equal(safety.status, 200);
    assert.ok((await page.locator("#agent-results").innerText()).includes("<img src=x"));
    assert.equal(await page.locator("#agent-results img").count(), 0);
    assert.equal(await page.evaluate(() => window.qaInjected), undefined);
    report.fixture_scenarios.push({name: "UI_text_safety", real_model: false, status: "PASS"});
    check("untrusted_answer_is_text", "Explicit ScriptedModelProvider fixture reaches real UI through API; markup remains text");
    assert.equal(report.page_errors.length, 0); check("no_unhandled_JS_errors", "No pageerror during complete browser→API→Core→response story");
    await context.close(); report.status = "PASS";
  } catch (error) {report.status = "FAIL"; report.failure = error.message; process.exitCode = 1; console.error(error.message);}
  finally {
    if (browser) await browser.close(); if (xvfb) xvfb.kill();
    report.finished_utc = new Date().toISOString();
    saveRaw("browser-observations.json", report);
    console.log(JSON.stringify({status: report.status, checks: report.checks.length, screenshots: report.screenshots.length, failure: report.failure}));
  }
}
main();
