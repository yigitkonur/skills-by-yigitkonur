# Handoff — skills pack reorganization

## Current objective

The reorganization is **functionally complete**. The next agent's job is to verify the new skills in real use (no in-prod testing happened in this session) and to clear the small follow-up list below.

## Current state

- **Main repo** `yigitkonur/skills-by-yigitkonur` @ `main` at commit `34ea17e`. **19 skills**, validator clean. Pushed.
- **Secondary repo** `yigitkonur/skills-by-yigitkonur-secondary` @ `main` at commit `bd810a3`. **19 b-side skills**. Pushed.
- **`~/.agents`** lock parity clean: 24 lock entries + 1 symlink on disk (`cua-driver`) = 25 total. Zero stale, zero missing.
- **Per-project installs** landed in 17 projects. See "Project install map" below.

### Pack composition after reorg (19 main + 19 secondary)

```
main (everyday loadout)        secondary (b-side, niche / project-shaped)
audit-completion               audit-agentic-cli                  *
audit-ui-and-save-files NEW    audit-agentic-mcp                  *
build-skill                    audit-skill-by-derailment          *
convert-url-to-nextjs ENH      build-chrome-extension
create-design-md NEW           build-clean-mcp-architecture       *
debug-runtime                  build-effect-ts-v3                 *
init-agent-config              build-kernel-ts-sdk                *
init-makefiles                 build-langchain-ts-app
publish-npm-package            build-macos-app                    *
run-agent-browser REWRITE      build-mcp-server-sdk-v1
run-github-scout               build-mcp-server-sdk-v2
run-railway                    build-mcp-use-agent
run-repo-cleanup               build-mcp-use-client
run-research                   build-mcp-use-server               *
run-research-and-save-files NEW  build-raycast-script-command   * (unpinned — no ~/scripts)
run-research-and-save-files-by-codex NEW   build-tinacms-nextjs   *
run-review NEW                 convert-mcp-sdk-v1-to-v2
test-by-mcpc-cli               run-codex-review-loop  (renamed from run-codex-review)
update-agent-config            run-linear-cli
                               # * = also pinned per-project
```

**Retired entirely**: `run-codex-1`, `run-codex-2`, `run-codex-exec`, `run-issue-tree`, `plan-tradeoff` (5 skills).

## What has already been done

1. **5 parallel subagent rewrites** in `/tmp/skills-wt-{1..5}-*` worktrees, each on a `merge/*` branch, all merged into main.
2. **Opus rewrite of `run-agent-browser`** in `/tmp/skills-wt-6-agent-browser`, transcript-first with cleaned `allowed-tools`, references 13→4, also merged.
3. **Secondary repo created** via `gh repo create yigitkonur/skills-by-yigitkonur-secondary --public`, populated with 19 b-side skills, MrBeast2-style README.
4. **Main repo deletions**: 24 skills `git rm`'d (19 moved to secondary + 5 retired entirely).
5. **Per-project installs**: 17 projects pinned with their domain-specific skills (see map below).
6. **~/.agents cleanup**: 32 stale skills removed, lock file purged of 15 dangling entries.
7. **Honest audit pass**: found and fixed 60+ dangling refs to retired `plan-tradeoff` in `debug-runtime`; stale `run-codex-2` / `run-corpus-research` / `run-industry-research` / `run-issue-tree` / `audit-ui` / `extract-saas-design` refs in 9 skills; convention violations (stray `README.md` next to canonical `INSTALL.md`); secondary repo H1 heading mismatch on the renamed skill; `NAMING.md`/`AGENTS.md` retirement tombstones.

## Project install map (17 projects)

| Project | Pinned skills |
|---|---|
| `saas-wope-ai` | build-kernel-ts-sdk, build-tinacms-nextjs, build-mcp-use-server |
| `api-to-md` | audit-agentic-cli, build-effect-ts-v3 |
| `mcp-researchpowerpack` | audit-agentic-mcp, build-effect-ts-v3, build-mcp-use-server |
| `AgentIndex` | build-macos-app |
| `lets-talk` | build-macos-app |
| `website-event-factory` | build-tinacms-nextjs |
| `website-zeo` | build-tinacms-nextjs (note: existing lock had `nextjs-tinacms` from a different source — see Unknowns) |
| `mcp-ads-google` | audit-agentic-mcp, build-clean-mcp-architecture, build-mcp-use-server |
| `mcp-ads-meta` | audit-agentic-mcp, build-clean-mcp-architecture, build-mcp-use-server |
| `mcp-d4s` | audit-agentic-mcp, build-clean-mcp-architecture, build-mcp-use-server |
| `private-skills-by-yigitkonur` | audit-skill-by-derailment |
| `skill-registry` | audit-skill-by-derailment |
| `cli-sessionr` | audit-agentic-cli, build-mcp-use-server |
| `lean-statusline` | audit-agentic-cli |
| `cyrus` | audit-agentic-cli, build-mcp-use-server |
| `genius-cli` | audit-agentic-cli |
| `codex-lb` | audit-agentic-cli |
| `mcp-ga4`, `mcp-gsc`, `my-mcp` | audit-agentic-mcp, build-mcp-use-server |

## Key files, commands, branches

- **Repos**:
  - `/Users/yigitkonur/dev/skills-by-yigitkonur` (main, `main`)
  - `/Users/yigitkonur/dev/skills-by-yigitkonur-secondary` (secondary, `main`)
- **Validator**: `python3 scripts/validate-skills.py` — run after any edit, must exit 0.
- **Install (global)**: `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<name>` (or `-secondary/skills/<name>`).
- **Install (project)**: `cd /path/to/project && npx -y skills add -y yigitkonur/skills-by-yigitkonur-secondary/skills/<name>` (no `-g`).
- **Refresh installed content** (no-op-safe): `rm -rf ~/.agents/skills/<name> && npx -y skills add -y -g <source>`. The `npx skills update` command did **not** reliably pull new content during this session; force-reinstall is the working path.
- **Conventions**:
  - Skill layout is **flat**: `skills/<name>/SKILL.md` (NOT the older doubly-nested `skills/<name>/skills/<name>/SKILL.md` — that was retired in PR #69, commit `6b6b7bf`).
  - Per-skill metadata file is **`INSTALL.md`**, not `README.md` (this was an audit-discovered convention violation).
- **No open PRs, no open issues**. Both repos pushed direct-to-main.

## Known blockers, risks, unknowns

| # | Item | Severity |
|---|------|----------|
| 1 | `skills-by-yigitkonur` cannot host a per-project install of `audit-skill-by-derailment` — its own `skills/` IS the source. Currently flagged Cannot-Install; coverage exists via `private-skills-by-yigitkonur` + `skill-registry`. | Low — by design |
| 2 | `build-raycast-script-command` unpinned because `~/scripts` does not exist. | Low |
| 3 | **13 project repos have untracked `skills-lock.json` + `skills/<symlink>` files** from per-project installs (saas-wope-ai, api-to-md, AgentIndex, website-event-factory, mcp-ads-google, mcp-ads-meta, cli-sessionr, lean-statusline, cyrus, genius-cli, codex-lb, mcp-ga4, mcp-gsc, plus the new ones added in audit pass: skill-registry, saas-wope-ai, cyrus, cli-sessionr). User judgement required — commit, gitignore, or leave. | Medium — needs decision |
| 4 | `website-zeo` lockfile shows `nextjs-tinacms` (different source). Possibly pre-existing install from elsewhere. The `build-tinacms-nextjs` install command was issued and reported success, but the lock didn't update with that name. Worth a manual check. | Medium |
| 5 | `run-agent-browser` references three `agent-browser` subcommands that may not exist in installed CLI 0.24.0: `snapshot -i -C`, `auth save/login/list/delete`, `device list`. Subagent 6 left them in references but didn't use them in any transcript. Confirm-or-strip pass needed. | Low |
| 6 | No skills tested in actual use. All validation was static (frontmatter, file structure, ref linkage, grep sweeps). No skill was triggered by Claude Code and walked through a real task. | Medium |

## Next agent's first action

Run a smoke test on the new `run-review` skill (most consequential merger — combined 3 old skills + a CLI mode). Pick a real recent PR and invoke `run-review` Mode A from a fresh Claude Code session. Check that mode selection actually happens (Mode A/B/C/D prompt), that the right reference files load, and that the codex-review hand-off path (Mode D) doesn't reference any deleted dispatcher script.

## Recommended next steps in order

1. **Smoke-test `run-review` Mode A** on a real PR (see above). 5 min.
2. **Smoke-test `run-agent-browser`** by triggering it with a literal browser task ("open google.com, snapshot, click the search box"). Verify the transcript-first guidance + state scratchpad actually steer behavior. 10 min.
3. **Decide on the 13 project-repo untracked files** (item 3 above) — likely: add `skills-lock.json` and `skills/*@` to each repo's `.gitignore`. Same pattern as the main pack repo's `.gitignore`. ~20 min.
4. **Confirm the flagged `agent-browser` subcommands** (item 5) — `npx agent-browser auth --help` and `npx agent-browser device --help`. If commands return "unknown", strip them from `skills/run-agent-browser/references/sessions-and-refs.md` and `safety.md`. 10 min.
5. **Resolve the `website-zeo` lock mismatch** (item 4) — read the existing `skills-lock.json` there and reconcile with intended install. 5 min.
6. **Consider whether `build-raycast-script-command` should be retired** if `~/scripts` is not on the roadmap; otherwise create the dir and install.

## Validation already done

- `python3 scripts/validate-skills.py` passes in both repos (19 skills each).
- Grep sweep for retired-skill cross-refs in `skills/`, `NAMING.md`, `AGENTS.md`, `CONTRIBUTING.md` — zero unannotated stale refs.
- `~/.agents` on-disk vs lock parity verified: 0 stale, 0 missing.
- Live CLI cross-check on `agent-browser --help` and `codex review --help` against the new skill bodies.
- `git status` clean in both checkouts after final pushes.

## Validation still needed

- **Real-use smoke tests** for all 6 rewritten/merged skills (run-research-and-save-files, run-research-and-save-files-by-codex, audit-ui-and-save-files, create-design-md, run-review, run-agent-browser).
- **Per-project installs functional check**: in at least one project per pinned skill, verify the skill actually loads and triggers from Claude Code when the project is opened.
- **Trigger-conflict check**: with 19 globals + per-project additions, confirm no two skills compete for the same user phrase. The skill registry already loads cleanly (per the latest system-reminder dump), so this is likely fine, but a real conversation should be the proof.
