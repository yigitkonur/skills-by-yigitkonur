# Derailment Test: run-agent-browser on "HN Data Extraction & Search"

Date: 2026-03-11
Skill under test: run-agent-browser
Test task: Navigate to Hacker News, extract top 5 story titles, search hn.algolia.com for "browser automation", verify results — exercising the full observe→act→verify loop including data extraction.
Method: Follow SKILL.md steps 1–6 exactly as written, recording every friction point.

---

## Pre-scan summary

| Property | Value |
|---|---|
| SKILL.md line count | 197 |
| Workflow steps | 6 (establish session, navigate, inspect, interact, verify, clean up) |
| Reference files | 13 (commands, installation, session-management, workflows, authentication, snapshot-refs, stealth-automation, safety, advanced, troubleshooting, video-recording, profiling, proxy-support) |
| Template files | 5 (ai-agent-workflow.sh, form-automation.sh, authenticated-session.sh, e2e-test-workflow.sh, capture-workflow.sh) |
| Branching points | 3 (session choice, selector priority, recovery paths) |
| External dependencies | agent-browser CLI (npm package), Chromium |
| Trigger boundary | terminal-driven browser automation; not for playwright-cli or static research |

---

## Friction points

### Phase 1: Establish session and baseline

**F-01 — `allowed-tools` uses bare `agent-browser` but npx is common entry point** (P1, M5)
SKILL.md's frontmatter declares `allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)` but all code examples in SKILL.md and every reference file use bare `agent-browser` commands without `npx` prefix. An executor who installed via `npx` (the "Alternative: no install" path from installation.md) would need to mentally translate every single command. The installation reference mentions `npx agent-browser` as an alternative but SKILL.md never acknowledges this divergence.
Fix: Add a note after the first code block in §1 stating: "All examples use globally installed `agent-browser`. If using `npx agent-browser`, prefix every command accordingly. Global install is recommended for multi-command workflows."

**F-02 — No prerequisite verification step in SKILL.md** (P1, S1)
SKILL.md jumps straight into `agent-browser tab` without verifying installation. The `references/installation.md` has a "Verify Installation" section but SKILL.md never routes there before step 1. An executor who hasn't installed agent-browser gets `command not found` with no recovery guidance in the main document.
Fix: Add a prerequisite block before §1: "Verify `agent-browser --version` prints a version. If not installed, see `references/installation.md`."

### Phase 2: Navigate or focus the correct page

Clean pass. The verify-after-navigation pattern (`tab`, `get url`, `get title`, `snapshot -i`) worked exactly as documented. The four-command verification block is clear and unambiguous.

### Phase 3: Inspect before interacting

**F-03 — `snapshot -i` flat output makes element identification ambiguous on content-heavy pages** (P1, M4)
On Hacker News, `snapshot -i` returned 200+ link elements in a flat list with no visual grouping or hierarchy. Story titles, domain labels, usernames, timestamps, and navigation links were all intermixed as `link "text" [ref=eN]`. The skill says to use `@refs from snapshot -i` as first priority but provides no guidance on how to identify which refs correspond to which semantic purpose when the page has many similar elements.
Fix: Add after the selector priority list: "On content-rich pages where `snapshot -i` returns many similar elements, use `snapshot -i -s CSS_SELECTOR` to scope to a specific container, or `snapshot -i --json` and parse the refs dictionary to filter by role/name. For pages with 50+ interactive elements, scoped snapshots are strongly preferred."

**F-04 — `snapshot -i` omits non-interactive text content critical for extraction** (P1, M4)
On both HN front page and hn.algolia.com search results, story titles rendered as `<span>` or `<div>` text (not wrapped in `<a>` tags) were invisible in `snapshot -i` output. The executor could see domain links and metadata links but not the actual story title text. The skill's principle "DOM evidence as source of truth" requires seeing the DOM, but `snapshot -i` hides non-interactive content.
Fix: Add to §3 after "Use `snapshot -i` first": "Note: `snapshot -i` shows only interactive elements (links, buttons, inputs). Non-interactive text (headings, paragraphs, labels not inside `<a>` or `<button>`) is invisible. For data extraction, supplement with `get text CSS_SELECTOR` for specific containers or `snapshot` (without `-i`) for the full accessibility tree."

**F-05 — `snapshot -i --json` schema undocumented; workflows.md contradicts reality** (P0, S2)
SKILL.md §3 says: "Use `snapshot -i --json` when you need structured extraction or machine-readable branching logic." The `references/workflows.md` §2 provides an example: `agent-browser snapshot -i --json | jq '.elements[] | select(.role == "button")'`. But the actual JSON output has the schema `{success, data: {origin, refs, snapshot}, error}` where `refs` is a `{refId: {name, role}}` dictionary and `snapshot` is the text string. There is no `.elements[]` array. The documented jq command fails silently (returns nothing).
Fix: In `references/workflows.md` §2, replace the jq example with the actual schema:
```bash
# JSON snapshot structure: {success, data: {origin, refs, snapshot}, error}
agent-browser snapshot -i --json | jq '.data.refs | to_entries[] | select(.value.role == "button") | {ref: .key, name: .value.name}'
```
Also add a brief schema note to SKILL.md §3 after the `--json` bullet: "JSON output schema: `{success, data: {origin, refs: {refId: {name, role}}, snapshot: string}, error}`."

### Phase 4: Interact one state change at a time

**F-06 — No guidance on extracting data from multiple matching elements** (P1, M4)
When using `get text ".Story_title"` to extract story titles, agent-browser threw a "strict mode violation" because the CSS selector matched 30 elements. The skill lists `get text REF_OR_SELECTOR` as a verification tool but never explains that CSS selectors must resolve to a single element. The `references/commands.md` shows `get text @e1` (single ref) and `get text body` (single element) but never addresses multi-element scenarios.
Fix: Add to §5 (verify section) or to a new "Data extraction" subsection: "CSS selectors passed to `get text`, `get value`, and `is visible` must resolve to a single element. If multiple elements match, the command fails with a strict mode error. For multi-element extraction, use `get count CSS_SELECTOR` to check cardinality, then either: (a) scope with a more specific selector, (b) use `find first/nth/last CSS_SELECTOR get text`, or (c) use `eval --stdin` with DOM queries for batch extraction."

**F-07 — `eval` safety classification unclear for read-only operations** (P1, M1)
`references/safety.md` lists `eval` as "High" risk requiring "explicit approval." But using `eval` for read-only DOM queries (e.g., `document.querySelectorAll(...).map(...)`) carries no more risk than `get text`. The skill doesn't distinguish read-only eval from mutation eval. An executor following literally would avoid eval entirely for data extraction, even though it's the only practical way to extract structured data from multiple elements.
Fix: Add to `references/safety.md` after the risk table: "**Read-only `eval` for data extraction** (e.g., `document.querySelectorAll(...).map(el => el.textContent)`) is safe for the same contexts where `get text` is safe. The 'High' risk classification applies to `eval` that mutates DOM, triggers navigation, accesses credentials, or calls external APIs."

### Phase 5: Verify the result before moving on

**F-08 — `diff snapshot` not explained for SPA pages** (P2, M4)
SKILL.md §5 lists `diff snapshot` as a verification method but doesn't explain its behavior on SPA pages where the URL and DOM both changed via JavaScript (not navigation). On hn.algolia.com, filling the search box triggered a live DOM update without navigation. The executor doesn't know whether `diff snapshot` would capture this or require a previous `snapshot` call as baseline.
Fix: Add after the `diff snapshot` bullet: "For SPA pages that update via JavaScript (no full navigation), `diff snapshot` compares against the last `snapshot` taken. Always take an explicit `snapshot -i` before the action to establish a baseline for diff."

### Phase 6: Clean up deliberately

Clean pass. `agent-browser close` worked as expected.

---

## What worked well

1. **The 4-command verification block** (`tab`, `get url`, `get title`, `snapshot -i`) is excellent. It's unambiguous, quick, and catches focus/navigation issues immediately. I used it naturally at every transition.

2. **`open` command auto-detection** — `agent-browser open https://news.ycombinator.com` worked instantly with implicit wait and returned a clean status line showing title + URL.

3. **Ref-based interaction is genuinely fast** — once I had refs from `snapshot -i`, `fill @e3 "browser automation"` was a single command with no selector ambiguity.

4. **Recovery path clarity** — the "Ref not found or wrong element" recovery in SKILL.md is actionable: re-snapshot and retry.

5. **Session reuse** — staying in the same session across pages (HN → hn.algolia.com) worked seamlessly without any configuration.

6. **Template files** — well-structured shell scripts that demonstrate real patterns. The `authenticated-session.sh` discovery mode is particularly clever.

7. **`eval --stdin` heredoc pattern** — the `references/advanced.md` and `references/commands.md` correctly document the `<<'EVALEOF'` pattern for complex JS, which solved my extraction problem.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 1 | F-05 |
| P1 | 6 | F-01, F-02, F-03, F-04, F-06, F-07 |
| P2 | 1 | F-08 |

## Derailment density map

| Phase | Steps | Friction | Density |
|---|---|---|---|
| 1. Establish session | 4 commands | F-01, F-02 | 0.50 |
| 2. Navigate | 5 commands | — | 0.00 |
| 3. Inspect | 3 commands | F-03, F-04, F-05 | 1.00 |
| 4. Interact | 3 commands | F-06, F-07 | 0.67 |
| 5. Verify | 3 commands | F-08 | 0.33 |
| 6. Clean up | 1 command | — | 0.00 |

**Hotspot:** Phase 3 (Inspect) has the highest derailment density. The snapshot system is well-designed but insufficiently documented for data extraction and structured parsing.

## Metrics

| Metric | Value |
|---|---|
| Total steps attempted | 19 |
| Clean passes | 11 |
| P0 (blocks progress) | 1 |
| P1 (causes confusion) | 6 |
| P2 (minor annoyance) | 1 |
| Derailment density | 0.42 |
| Clean pass rate | 58% |
| Cluster size (max) | 3 (Phase 3) |
