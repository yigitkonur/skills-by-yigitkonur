# run-agent-browser

Priority-routed browser automation for the installed `agent-browser` CLI:

1. **Plain local Chrome** (always start here; unset sticky providers)
2. **Steel Browser CDP** (self-hosted on this fleet — details in `references/cdp-and-steel.md`)
3. **Cloud providers** — Browser Use, Kernel, Browserless, Browserbase (`references/providers.md`)
4. **Ask the user** for a CDP URL, API key, or install/deploy approval — never dead-end

Stealth defaults apply at every tier. Secrets stay in `chmod 600` env files; never printed.

## Quick start

```bash
# Tier 1
SESSION="local-$(agent-browser session id --scope cwd --prefix task)"
env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" \
  --args "--disable-blink-features=AutomationControlled" \
  open https://example.com
```

If that fails, source `~/.config/steel-browser-cdp.env` and use `--cdp "$STEEL_AGENT_BROWSER_CDP"` (see SKILL.md). If Steel fails, pick a provider from `references/providers.md`.

## Layout

| Path | Role |
|---|---|
| `SKILL.md` | Priority ladder + operating loop |
| `references/cdp-and-steel.md` | Steel endpoints, single-session semantics, release, tailnet |
| `references/providers.md` | Browser Use / Browserbase / Browserless / Kernel |
| `references/managed-cdp-pool.md` | Patchright Google AI/Gemini scrape API |
| `references/*.md` | Commands, safety, trust, advanced |
| `scripts/` | Health check + page inspect helpers |

## Sync targets

- GitHub: `yigitkonur/skills-by-yigitkonur` → `skills/run-agent-browser/`
- Local: `~/.claude/skills` + `~/.codex/skills` + plugin marketplace
- MacBook: same skill paths + tailnet-oriented `~/.config/steel-browser-cdp.env`
