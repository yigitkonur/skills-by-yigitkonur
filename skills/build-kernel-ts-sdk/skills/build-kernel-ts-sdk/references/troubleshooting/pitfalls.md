# Pitfalls

The 16 production pitfalls in priority order. Read top-to-bottom before shipping any non-trivial Kernel-TS work.

## 1. `browser.close()` is not cleanup

**Symptom:** Browser keeps running, costs continue accruing, `kernel.browsers.list()` still shows the session.

**Cause:** Playwright/Puppeteer `browser.close()` (and Stagehand `stagehand.close()`) only severs the local CDP connection. The Kernel browser VM keeps running until `timeout_seconds` elapses.

**Fix:** Always call `kernel.browsers.deleteByID(session.session_id)` in a `finally`. Pair every `create` with `deleteByID`.

## 2. The 60-second default timeout is too aggressive

**Symptom:** Browser deletes mid-task with no obvious error. Subsequent CDP calls fail with connection-closed.

**Cause:** Default `timeout_seconds: 60`. Any pause (CAPTCHA solve, slow network, human handoff) eats the budget.

**Fix:** Set `timeout_seconds: 300` minimum for real automation, up to `259200` (72h). The clock counts down only while the browser is idle (no CDP / live-view connection).

## 3. Standby starts the timeout countdown — don't expect open-but-idle to be free

**Symptom:** A long-idle session is suddenly gone.

**Cause:** After 5 seconds of no CDP / live-view connection, the browser enters standby (zero compute cost). The `timeout_seconds` countdown to deletion **begins at standby entry**; when a connection reattaches, the countdown resets. GPU browsers do not standby — they keep running and bill compute the whole time.

**Fix:** Keep one connection open for "long idle" sessions, OR make `timeout_seconds` long enough to outlast the expected gap. For GPU browsers, accept the higher floor cost or terminate explicitly.

## 4. Headful vs headless trade-off

**Symptom:** Live view URL is `undefined` / replays don't start / GPU flag rejected.

**Cause:** Headless browsers have ~1 GB image, ~8× cheaper, faster boot — but **no live view, no replays, no GPU**.

**Fix:** Pick headful (default) when you need live view, replays, or GPU. Pick headless for fast scripted scrapes that don't need any of those.

## 5. Stealth is not a silver bullet

**Symptom:** Even with `stealth: true`, the site flags the browser as a bot.

**Cause:** Stealth adds a default ISP proxy and an automatic CAPTCHA solver. It does not defeat every detector — sophisticated sites combine IP reputation, fingerprinting, and behavioral heuristics.

**Fix:** Layer signals — pair stealth with a residential proxy (`proxy_id`), a long-lived profile (browsing history builds trust), and human-like input via `kernel.browsers.computer.*` instead of raw CDP clicks.

## 6. CDP latency vs `playwright.execute`

**Symptom:** A bulk extraction over many pages is slow even though each page loads quickly.

**Cause:** Every CDP call is a network round-trip from your service to the Kernel browser VM. Tight inner loops add up.

**Fix:** For hot paths, switch to `kernel.browsers.playwright.execute(id, { code })` — the script runs in the browser VM with `page`, `context`, `browser` in scope, no CDP overhead. Reserve raw CDP for long-lived interactive sessions.

## 7. Sync invocation cap is ~100 seconds

**Symptom:** `invocations.create` (sync) errors out around the 100-second mark.

**Cause:** Sync invocations block on the HTTP request lifetime. Real cap is around 100 seconds.

**Fix:** Set `async: true` and `async_timeout_seconds` (10–3600). Consume `invocations.follow(id)` for status. Switching after the fact requires a re-deploy.

## 8. Default-context-only

**Symptom:** Cookies, profile state, or extensions are not visible from inside Playwright.

**Cause:** Kernel browsers ship with one default context and one open page. Calling `browser.newContext()` or `context.newPage()` creates fresh ones that do **not** inherit profile, cookies, or extensions.

**Fix:** Always `browser.contexts()[0].pages()[0]`. Never `newContext` / `newPage` on a Kernel browser.

## 9. Bun + Playwright warning

**Symptom:** Stdout warning about Bun + Playwright CDP flakiness on every run.

**Cause:** The SDK detects Bun and warns because Bun has known CDP issues with Playwright.

**Fix:** Use Node 20+ if possible. If Bun is required, set `KERNEL_SUPPRESS_BUN_WARNING=true` and accept the risk.

## 10. Project scoping is header-driven

**Symptom:** An org-wide API key sees browsers / apps from other projects.

**Cause:** Org-wide API keys are not project-scoped by default. OAuth (CLI) is always org-wide.

**Fix:** Pass `X-Kernel-Project-Id` on every request — the SDK does not auto-read any project env var. Wire it via `defaultHeaders: { 'X-Kernel-Project-Id': process.env.KERNEL_PROJECT }` in the constructor, or per-request `headers`.

## 11. `browsers.delete` (singular) is deprecated

**Symptom:** TypeScript flags `browsers.delete` as `@deprecated`.

**Cause:** The plural-shaped `delete({ persistent_id })` belongs to the deprecated persistence model (replaced by Profiles).

**Fix:** Use `kernel.browsers.deleteByID(session_id)` instead.

## 12. Replay download timing

**Symptom:** `replays.download` returns nothing or a partial file.

**Cause:** Replays finalize asynchronously after `replays.stop`. The download endpoint can be hit before the file is fully written.

**Fix:** Poll `kernel.browsers.fs.listFiles` for the replay artifact, or wait a few seconds after `stop` before downloading. For large replays, expect multi-second finalization.

## 13. `type: 'module'` required for TS app deploys

**Symptom:** `kernel deploy app.ts` fails with module-resolution errors.

**Cause:** TypeScript apps run as ESM in Kernel's build environment. `package.json` must declare `"type": "module"`.

**Fix:** Add `"type": "module"` to `package.json`. If you have CommonJS-only dependencies, refactor or pin compatible versions.

## 14. Idle pool-cost model

**Symptom:** Confusion about pool billing — "is the idle pool charging me?"

**Cause:** Per kernel.sh/docs/info/pricing, idle browsers in a pool incur **no disk charges**; you pay compute only when a browser is actively in use (i.e. acquired). Pools do require the Start-Up plan or higher (Developer/Hobbyist tiers cap reserved browsers at 0).

**Fix:** Don't oversize pools "just in case" — there is no idle disk cost, but the `size` cap consumes plan quota. Read `kernel.browserPools.retrieve` for `available_count`/`acquired_count` and tune accordingly. Use `flush()` to reset after a config change.

## 15. Payload max 4.5 MB JSON-encoded

**Symptom:** `invocations.create` rejects a fat payload, or `output` is truncated.

**Cause:** `payload` and `output` are JSON-encoded strings, max **4.5 MB** each (per kernel.sh/docs/apps/invoke).

**Fix:** Move multi-MB artifacts (screenshots, archives, harvested HTML) through `kernel.browsers.fs.*` (write inside the action, read out from the caller via `session_id`) or PUT them to your own object store and pass a URL. For payloads under 4.5 MB, JSON-encode directly.

## 16. Cleanup is your responsibility

**Symptom:** Phantom browsers left running after invocations crash; bills creep up.

**Cause:** Kernel deletes browsers when (a) `timeout_seconds` elapses idle, (b) `deleteByID` is called, or (c) an invocation tagged via `invocation_id` is reaped via `invocations.update({status:'failed'})` / `invocations.deleteBrowsers`. Free-standing browsers ignore the parent's lifecycle.

**Fix:** Tag every `browsers.create` inside an action with `invocation_id: ctx.invocation_id`. From outside an action, wrap `create` with a `try/finally` calling `deleteByID`. For belt-and-suspenders: a periodic cleanup job that lists `browsers.list()` and deletes anything older than expected.

## Where to look next

- File I/O and replay-specific issues: `references/troubleshooting/files-and-replays.md`
- Auth state and profile errors: `references/troubleshooting/auth-and-profile-errors.md`
- Picking the right control surface to avoid latency: `references/patterns/browser-control-surfaces.md`
