# skills-by-yigitkonur

Skills for AI coding agents — review, research, UI audit, design extraction, browser automation, debug workflows, config files, publish. The everyday loadout. **22 skills** organized under the 12-verb naming registry (see [NAMING.md](NAMING.md)).

> the b-side pack lives at **[skills-by-yigitkonur-secondary](https://github.com/yigitkonur/skills-by-yigitkonur-secondary)** — framework builders, mcp variants, niche tools. mrbeast2 energy, less popular sibling, still goes hard. cherry-pick from there when the job calls.

## Install

Install **the full pack**:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

Install **a single skill** — substitute `<skill-name>`:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

Per-skill one-liners are listed under each row below.

---

## 🏗️ Build apps & code

Write application code with a framework or SDK.

- **[build-skill](skills/build-skill/)** — Claude skill creation and research methodology.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skill`

> the rest of the build-* family lives in the [b-side pack](https://github.com/yigitkonur/skills-by-yigitkonur-secondary). chrome / effect-ts / kernel / langchain / macos / raycast / tinacms / mcp variants — all there. cherry-pick what you need.

---

## ⚙️ Config & instruction files

Generate or refresh config / instruction files that another tool consumes.

- **[init-agent-config](skills/init-agent-config/)** — AGENTS.md / CLAUDE.md / REVIEW.md hierarchies; folder-scoped guidance; native review adapters.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-agent-config`

- **[init-makefiles](skills/init-makefiles/)** — Scaffold safe scenario Makefiles (Vercel default; Cloudflare Pages opt-in), R2 bulk upload via rclone, AGENTS sync, optional deploy CI.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-makefiles`

- **[update-agent-config](skills/update-agent-config/)** — Audit AGENTS.md / CLAUDE.md / REVIEW.md for drift after refactors; refresh refs, recount frequency tables, fill gap folders.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/update-agent-config`

---

## 🔍 Audit (read-only inspection)

Inspect an artifact; produce findings, no fixes.

- **[audit-completion](skills/audit-completion/)** — Audit task / session / plan / branch completion claims; remediate to terminal status.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-completion`

- **[audit-ux-laws](skills/audit-ux-laws/)** — Audit UI against the 30 Laws of UX (Fitts's, Hick's, Miller's, Jakob's, Gestalt, choice overload, cognitive load) with CRITICAL/MINOR severity and concrete code fixes.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-ux-laws`

- **[audit-ui-and-save-files](skills/audit-ui-and-save-files/)** — Visual UI audit across pages and viewports with browser screenshots, writing per-bug findings to `css-issues/[YY-MM-DD]/[context]/[device]/NN-slug.md` and ending with an approval-gated fix-subagent dispatch plan.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-ui-and-save-files`
- **[audit-ux-and-save-files](skills/audit-ux-and-save-files/)** — Usability audit from real personas walking their journeys with browser screenshots, writing per-issue findings to `ux-findings/[YY-MM-DD]/[persona]/[journey]/NN-slug.md` and ending with a prioritized recommendations report (reports, does not fix).
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-ux-and-save-files`

> the agentic-cli / agentic-mcp / skill-by-derailment audits moved to the [b-side pack](https://github.com/yigitkonur/skills-by-yigitkonur-secondary) — they're project-shaped (you usually want them inside one repo, not globally chatting at every prompt). install per-project from there.

---

## 📝 Review (PR / diff / feedback)

Evaluate a code change for merge-readiness; produce reviewer feedback.

- **[run-review](skills/run-review/)** — Single entry-point with four modes. Mode A: do a PR / branch review. Mode B: open your branch as a self-review PR. Mode C: triage received feedback (human, bot, markdown, multi-reviewer). Mode D: delegate to `codex review` CLI.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-review`

---

## ✅ Test (pass / fail)

Binary verification.

- **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** — MCP server testing with mcpc 0.2.x.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-by-mcpc-cli`

---

## 🐛 Debug

Investigate runtime bugs.

- **[debug-runtime](skills/debug-runtime/)** — Language-agnostic systematic debugging; four phases + Iron Law.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/debug-runtime`

---

## 🔄 Convert & create

Transform an artifact A → B, or generate a portable spec from existing artifacts.

- **[convert-url-to-nextjs](skills/convert-url-to-nextjs/)** — Rebuild a deployed site as a Next.js project AS-IS pixel-faithful from a live URL — for the "we lost the frontend repo" recovery scenario. L0+L1 unique-type crawl + back-to-back agent-browser verification.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/convert-url-to-nextjs`

- **[create-design-md](skills/create-design-md/)** — Produce a `design.md` spec (Google Labs DESIGN.md format) plus per-asset `references/[context]/NN-asset.{md,json}` references tree from a live URL, codebase, or HTML snapshot.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/create-design-md`

---

## 🛠️ Run external tools

Drive a CLI, API, browser, or other live tool during the session.

- **[run-agent-browser](skills/run-agent-browser/)** — Browser automation with agent-browser CLI.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-browser`

- **[run-babysitter](skills/run-babysitter/)** — Autonomous per-repo maintenance loop: triage commits + issues + persistent memory, file one deduplicated GitHub issue per cycle.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-babysitter`

- **[run-github-scout](skills/run-github-scout/)** — Adaptive GitHub repo discovery and shortlisting for concrete needs.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-github-scout`

- **[run-railway](skills/run-railway/)** — Railway CLI commands, workflows, and version-drift routing.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-railway`

- **[run-repo-cleanup](skills/run-repo-cleanup/)** — Sweep dirty tree + unpushed commits + N worktrees into focused private-fork PRs with self-review bodies.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-repo-cleanup`

- **[run-research](skills/run-research/)** — Single-question technical research with source-backed synthesis.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research`

- **[run-research-and-save-files](skills/run-research-and-save-files/)** — Wave-based corpus research that persists evidence to disk. Filesystem is the context channel between waves. Replaces the old `run-corpus-research` + `run-industry-research`.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research-and-save-files`

- **[run-research-and-save-files-by-codex](skills/run-research-and-save-files-by-codex/)** — Same shape as `run-research-and-save-files`, but every web-research task is delegated to parallel `codex exec` subprocesses. Claude orchestrates; codex executes. Effort routing: low/medium per wave, high only for synthesis waves.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research-and-save-files-by-codex`

- **[search-it-bulk-by-codex](skills/search-it-bulk-by-codex/)** — Bulk Codex-native web search with parseable answer files.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/search-it-bulk-by-codex`

> the codex orchestration fleet (`run-codex-1` / `run-codex-2` / `run-codex-exec`) and `run-issue-tree` were retired. `run-codex-review` moved to the [b-side pack](https://github.com/yigitkonur/skills-by-yigitkonur-secondary) as `run-codex-review-loop`. `run-linear-cli` lives there too. `plan-tradeoff` was pulled — use `debug-runtime`'s phase-0 framing when you need to think through a problem.

---

## 📦 Publish

Release to a registry.

- **[publish-npm-package](skills/publish-npm-package/)** — npm package releases via GitHub Actions with trusted publishing, provenance, semantic-release, changesets, release-please.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/publish-npm-package`

---

## the b-side pack (project-shaped)

these skills exist but are pinned to specific projects rather than globally installed — usually because they only earn their context window cost inside a matching codebase. install them locally where they belong:

| skill | where it earns its keep |
|---|---|
| [audit-agentic-cli](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/audit-agentic-cli) | every cli project in `~/dev` (lean-statusline, cli-sessionr, api-to-md, etc.) |
| [audit-agentic-mcp](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/audit-agentic-mcp) | every mcp project in `~/dev` (mcp-ads-*, mcp-d4s, mcp-ga4, mcp-gsc, my-mcp, mcp-researchpowerpack) |
| [audit-skill-by-derailment](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/audit-skill-by-derailment) | inside the yigitkonur skills repos (`skills-by-yigitkonur`, `private-skills-by-yigitkonur`, `skill-registry`) — used to stress-test SKILL.md files |
| [build-clean-mcp-architecture](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-clean-mcp-architecture) | marketing / ads mcps — `mcp-ads-google`, `mcp-ads-meta`, `mcp-d4s` |
| [build-effect-ts-v3](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-effect-ts-v3) | `api-to-md` and `mcp-researchpowerpack` (effect-ts native) |
| [build-kernel-ts-sdk](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-kernel-ts-sdk) | `saas-wope-ai` (wope ai) only |
| [build-macos-app](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-macos-app) | `AgentIndex` and `lets-talk` |
| [build-mcp-use-server](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-mcp-use-server) | every mcp project in `~/dev` |
| [build-raycast-script-command](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-raycast-script-command) | `~/scripts` if it exists — otherwise skip |
| [build-tinacms-nextjs](https://github.com/yigitkonur/skills-by-yigitkonur-secondary/tree/main/skills/build-tinacms-nextjs) | `saas-wope-ai`, `website-event-factory`, `website-zeo` |

to install one locally:

```bash
cd /path/to/project
npx -y skills add -y yigitkonur/skills-by-yigitkonur-secondary/skills/<skill>
```

(skip the `-g` flag — that's the whole point.)

---

## Notes

- Each installed skill adds to the context window. Install only what you need.
- For the verb taxonomy and naming conventions, read [NAMING.md](NAMING.md).
- For the canonical skill structure and contribution checklist, read [CONTRIBUTING.md](CONTRIBUTING.md).
- The spec this pack follows: [agentskills.io/specification](https://agentskills.io/specification). Discovery paths per Anthropic: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).
- If you see duplicate skill triggers, that's a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills must use a verb from the [12-verb registry](NAMING.md) and pass `python3 scripts/validate-skills.py`.

## License

MIT
