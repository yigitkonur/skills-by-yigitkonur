# Proposed Renames — review and edit in place before Phase C runs

**12-verb registry (new NAMING.md):** `build / init / update / convert / extract / run / audit / review / test / debug / publish / plan`

**Edit the `proposed` column directly.** Leave blank or write `keep` to skip the rename. Add a comment after the row if needed. Once you approve, the execution script reads this file line-by-line.

| # | Current | Proposed | Rationale |
|---|---|---|---|
| 1 | apply-clean-mcp-architecture | build-clean-mcp-architecture | `apply-` dropped. Skill places + refactors code to meet Clean Arch — `build-` covers code creation. Audit sub-mode is secondary. |
| 2 | ask-review | review-self | Single-skill verb `ask-` dropped. The skill opens a PR with a self-review body → `review-` + `self` object. |
| 3 | build-chrome-extension | **keep** | Already canonical. |
| 4 | build-effect-ts-v3 | **keep** | — |
| 5 | build-kernel-ts-sdk | **keep** | — |
| 6 | build-langchain-ts-app | **keep** | — |
| 7 | build-macos-app | **keep** | — |
| 8 | build-mcp-server-sdk-v1 | **keep** | — |
| 9 | build-mcp-server-sdk-v2 | **keep** | — |
| 10 | build-mcp-use-agent | **keep** | — |
| 11 | build-mcp-use-client | **keep** | — |
| 12 | build-mcp-use-server | **keep** | — |
| 13 | build-raycast-script-command | **keep** | — |
| 14 | build-tinacms-nextjs | **keep** | — |
| 15 | check-completion | audit-completion | `check-` dropped. Skill verifies claimed-done work read-only → `audit-`. |
| 16 | convert-mcp-server-sdk-v1-to-v2 | convert-mcp-sdk-v1-to-v2 | Shorten `mcp-server-sdk` → `mcp-sdk`; verb unchanged. |
| 17 | convert-url-to-nextjs | **keep** | — |
| 18 | do-debug | debug-runtime | `do-` dropped. Verb IS debug; object = runtime (what's being debugged). |
| 19 | do-review | review-pr | `do-` dropped. Verb IS review; object = the PR/branch diff. |
| 20 | do-think | plan-tradeoff | `do-` dropped. Verb IS plan; object = decision/tradeoff. |
| 21 | do-ui-audit | audit-ui | `do-` dropped. Verb IS audit; object = UI. |
| 22 | enhance-agent-config | update-agent-config | `enhance-` dropped. New `update-` verb; matches your original intent (was renamed `enhance-` only to fit prior registry). |
| 23 | enhance-skill-by-derailment | audit-skill-by-derailment | `enhance-` dropped. Skill tests skills for friction → audit produces findings. "by-derailment" kept per Object Rule (distinctive methodology). |
| 24 | evaluate-code-review | review-feedback | `evaluate-` dropped. Skill triages received review feedback → `review-` + `feedback`. |
| 25 | extract-saas-design | **keep** | — |
| 26 | init-agent-config | **keep** | Already canonical. |
| 27 | init-makefiles | **keep** | — |
| 28 | optimize-agentic-cli | audit-agentic-cli | `optimize-` dropped. Skill audits CLIs for agent-readiness — produces report → `audit-`. |
| 29 | optimize-agentic-mcp | audit-agentic-mcp | Same — audit, not modify. |
| 30 | orchestrate-codex | run-codex-1 | Numbered-alias temp pair with #44 — user will test both and pick later. |
| 31 | publish-npm-package | **keep** | — |
| 32 | run-agent-browser | **keep** | — |
| 33 | run-batch-codex-research | **keep** | — |
| 34 | run-codex-exec | **keep** | — |
| 35 | run-codex-review | **keep** | — |
| 36 | run-corpus-research | **keep** | — |
| 37 | run-github-scout | **keep** | — |
| 38 | run-industry-research | **keep** | — |
| 39 | run-issue-tree | **keep** | — |
| 40 | run-repo-cleanup | **keep** | — |
| 41 | run-research | **keep** | — |
| 42 | synthesize-skills | build-skill | `synthesize-` dropped. Skill produces a new SKILL.md artifact → `build-`. Object singular: each invocation builds one. |
| 43 | test-by-mcpc-cli | **keep** | — |
| 44 | use-codex | run-codex-2 | Numbered-alias temp pair with #30 — keep both for now, user picks the winner later. |
| 45 | use-linear-cli | run-linear-cli | `use-` → `run-`. |
| 46 | use-railway | run-railway | `use-` → `run-`. |

## Summary

- **Renames: ~22**  (rows where `proposed` ≠ current and ≠ `keep`)
- **Kept: ~24**  (rows marked `keep`)
- **New verbs that now have ≥1 skill:** `update-` (1 — `update-agent-config`), `audit-` (8 — completion, agentic-cli, agentic-mcp, skill-by-derailment, ui, plus 3 from optimize-/check-/do- renames), `debug-` (1), `plan-` (1).
- **Verbs that get zero skills after renames:** none. All 12 verbs land at least one skill — the registry isn't aspirational.

## Possible duplicates to resolve

- **#30 `run-codex-fleet` vs #44 `run-codex`** — same target tool. If their descriptions are identical (likely — both currently route to "five modes" verbatim), drop one. Pick:
  - keep `run-codex` (shorter, matches `use-codex` install path); deprecate `run-codex-fleet`
  - OR keep both if they have distinct flows after reading the SKILL.md bodies

## Open follow-ups for execution

- After applying renames, grep all SKILL.md bodies for cross-references to old names (e.g. `do-debug`, `enhance-agent-config`) — update them.
- Update INSTALL.md install URLs to the new name.
- Update root README.md table rows.

## When you're done editing this file

Leave a checkbox at the top:

- [ ] Approved — execute Phase C

When checked, the script applies the map.
