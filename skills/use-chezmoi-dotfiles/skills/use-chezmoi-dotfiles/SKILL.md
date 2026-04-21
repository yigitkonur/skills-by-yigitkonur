---
name: use-chezmoi-dotfiles
description: Use skill if you are editing yigitkonur's chezmoi-backed dotfiles on macOS — AI configs, MCP servers, skills, zsh, Homebrew, macOS defaults via `sync`/`skill`/`mcp-manage`/`mcp-verify` wrappers.
---

# Use chezmoi dotfiles (yigitkonur/script-dotfiles)

`yigitkonur` runs every Mac on a single private chezmoi repo with an age-encrypted secrets catalog. Everything routes through four CLI wrappers (`sync`, `skill`, `mcp-manage`, `mcp-verify`); never touch raw chezmoi commands unless you know exactly why.

## When to use

Trigger when asked to:

- Add / remove / rotate an MCP server (Morph, Brave, etc.)
- Add a skill from a GitHub repo or local path
- Edit shared `AGENTS.md` that Claude + Codex + Factory + Copilot all read
- Change a zsh alias, function, or prompt setting
- Install a brew formula or cask
- Toggle a macOS default
- Understand why `chezmoi status` shows `MM`

**Skip** for: one-off code changes inside a repo that isn't `~/.local/share/chezmoi/`; anything inside `~/.claude.json`, `~/.codex/sessions/`, or other paths listed in `.chezmoiignore`.

---

## The canonical workflow

1. **Check drift** first, always:
   ```bash
   sync           # interactive TUI — shows drifts, ripple effects, lets you pick resolution
   # or quick read-only:
   czs            # = chezmoi status
   ```
2. **Edit** via the right wrapper (see command matrix below). Never hand-edit a generated file — find its source.
3. **Verify** with `mcp-verify` or `chezmoi diff`.
4. **Push** happens automatically (autoCommit + autoPush in chezmoi.toml) after any re-add or apply that changes source.

---

## Command matrix — the 4 wrappers + aliases

| Goal | Command |
|---|---|
| Resolve drift interactively | `sync` |
| Add MCP server (all non-Claude providers) | `mcp-manage add <name> --stdio npx --arg '-y' --arg <pkg> [--env-secret KEY=secret_key] [--providers ...]` |
| Add MCP HTTP server | `mcp-manage add <name> --http https://…` |
| Remove MCP | `mcp-manage remove <name>` |
| Set a secret | `mcp-manage secret set <key> <value>` |
| Add skill from repo | `skill add <gh-owner/repo>` or `skill add <gh-owner/repo> --skill <name>` |
| Add skill from local dir | `skill add <path>` |
| Refresh skills from upstream | `skill update` |
| Remove skill | `skill remove <name>` |
| List skills | `skill list` |
| Snapshot all provider MCP + skills + symlinks + secrets (redacted) | `mcp-verify` |
| Force re-run of run_once scripts (macOS defaults etc.) | `cz-reset-scripts` |
| Pull remote + apply | `czu` (= `chezmoi update`) |

Raw chezmoi you still need:

- `chezmoi edit ~/<target>` — opens source in `$EDITOR`, auto-applies on save
- `chezmoi re-add <path>` — the "keep my live edits" move for `MM` drift
- `chezmoi merge <path>` — 3-way merge when both sides legit changed

---

## The five drift scenarios

From `chezmoi status` output:

```
Status  Meaning                                 Correct action
──────  ───────────────────────────────────────  ─────────────────────────────────
 M      source changed, live still old          chezmoi apply  (or sync)
M       live edited, source still old           chezmoi re-add <path>
MM      both changed                            sync → pick: keep live OR source
 R      run-script pending                      chezmoi apply
 A      new source file                         chezmoi apply
```

For a Claude edit to `~/.agents/AGENTS.md` that needs to land in the repo: **always `re-add`**, never naive `apply` (would overwrite the edit).

`sync` encodes this decision tree. Prefer it.

---

## Architecture cheat sheet

```
Canonical (edit here)                   Rendered targets (don't edit)
─────────────────────                   ──────────────────────────────
.chezmoidata/mcp-servers.yaml      →    ~/.codex/config.toml           (TOML)
                                   →    ~/.factory/mcp.json            (type:stdio/http)
                                   →    ~/.cursor/mcp.json             (bare JSON)
                                   →    ~/.copilot/mcp-config.json     (type:local/http)
                                        Claude — runtime, register via `claude mcp add`

.chezmoidata/ai-defaults.yaml      →    ~/.codex/config.toml
                                   →    ~/.factory/settings.json

dot_agents/AGENTS.md               →    ~/.agents/AGENTS.md  (file)
                                        ~/.claude/CLAUDE.md  (symlink → ^)
                                        ~/.codex/AGENTS.md   (symlink → ^)
                                        ~/.factory/AGENTS.md (symlink → ^)
                                        ~/.copilot/copilot-instructions.md (symlink → ^)

dot_agents/skills/<name>/          →    ~/.agents/skills/<name>/
                                        ~/.claude/skills/   (symlink → ~/.agents/skills)
                                        ~/.codex/skills/    (symlink → ^)
                                        ~/.factory/skills/  (symlink → ^)
                                        ~/.copilot/skills/  (symlink → ^)
                                        ~/.cursor/skills/   (symlink → ^)

secrets.yaml.age                   →    decrypted at apply time via
                                        includeTemplate "secrets" | fromYaml
```

---

## Hard boundaries

- **Never commit a plaintext API key, bearer token, SSH private key, or `.env` file.** Always via `mcp-manage secret set` → age-encrypted.
- **Never rename `symlink_X.tmpl` → `X.tmpl`** or vice versa. The prefix is semantic.
- **Never touch files listed in `.chezmoiignore`** (`~/.claude.json`, `cache/`, `sessions/`, `logs_*.sqlite`, `history.jsonl`, auth tokens). These are runtime-owned.
- **`cz-sync` binary at `~/.local/bin/cz-sync` is built from `cz-sync/main.go`** via `run_onchange_after_40-build-cz-sync.sh`. Do not edit the binary; edit the Go source and chezmoi rebuilds.

---

## Template variables quick reference

```go
.chezmoi.homeDir          // /Users/yigitkonur
.chezmoi.hostname         // mbp-m3 | macmini | ...
.chezmoi.sourceDir        // ~/.local/share/chezmoi
.servers.<name>.transport // stdio | http (from mcp-servers.yaml)
.servers.<name>.providers // []string
.codex.model              // from ai-defaults.yaml
.factory.autonomy_mode    // from ai-defaults.yaml

{{- $secrets := (includeTemplate "secrets" . | fromYaml).secrets -}}
{{ $secrets.morph_api_key }}
{{ $secrets.codex_bearer_token }}
```

---

## Before ending your task

1. Run `czs` (or `sync`) to confirm the working tree is clean.
2. If you edited a generated target (not a source), run `chezmoi re-add <path>` first — otherwise the next agent will overwrite your edit.
3. Verify with `mcp-verify` if you touched any provider's MCP config.
4. All commits auto-push. If `czs` shows nothing and `git log -1` shows your change on `origin/main`, you're done.
