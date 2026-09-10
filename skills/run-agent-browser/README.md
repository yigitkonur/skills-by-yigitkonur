# run-agent-browser

Priority-routed browser automation for the installed `agent-browser` CLI:

1. **Plain local Chrome** (always start here; unset sticky providers)
2. **Steel Browser CDP** (self-hosted on this fleet — details in `references/cdp-and-steel.md`)
3. **Cloud providers** — Browser Use, Kernel, Browserless, Browserbase (`references/providers.md`)
4. **Ask the user** for a CDP URL, API key, or install/deploy approval — never dead-end

Stealth defaults apply at every tier. Secrets stay in `chmod 600` env files; never printed.

**Category:** automation

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-agent-browser@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/run-agent-browser

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-browser

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.

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
