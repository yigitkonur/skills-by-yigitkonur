# Skills Loading Configuration

OpenClaw loads skills from a few well-defined locations, then applies config overrides from `openclaw.json`. This reference keeps the skill-loading path explicit so the executor does not guess where a missing skill should live or why an env var did not arrive.

All snippets in this reference are JSON5 fragments for the real `openclaw.json`.

## Locations and precedence

Skills can come from:

1. bundled skills
2. managed/local skills in `~/.openclaw/skills`
3. workspace skills in `<workspace>/skills`
4. extra skill directories from `skills.load.extraDirs`

Precedence is:

1. `<workspace>/skills`
2. `~/.openclaw/skills`
3. bundled skills
4. `skills.load.extraDirs`

If the same skill name appears in more than one place, the highest-precedence copy wins.

## Config keys that matter

| Key | Meaning |
|-----|---------|
| `skills.allowBundled` | Optional allowlist for bundled skills only |
| `skills.load.extraDirs` | Additional skill roots to scan |
| `skills.load.watch` | Auto-refresh skills when files change |
| `skills.load.watchDebounceMs` | Debounce interval for watcher events |
| `skills.entries.<skillKey>.enabled` | Enable or disable one skill |
| `skills.entries.<skillKey>.env` | Per-skill env vars for host runs |
| `skills.entries.<skillKey>.apiKey` | Per-skill API key value or SecretRef |
| `skills.entries.<skillKey>.config` | Custom per-skill config bag |

## `skills.entries` key mapping

The key under `skills.entries` is:

- the skill name by default, or
- `metadata.openclaw.skillKey` if the skill defines one

If the key does not match, the skill can load but its env, apiKey, or enabled flag will not apply.

## `extraDirs`

Use `skills.load.extraDirs` for shared skill packs or other non-default roots:

```json5
{
  skills: {
    load: {
      extraDirs: [
        "/opt/team-skills",
        "/Users/me/custom-skills",
      ],
    },
  },
}
```

Use absolute paths unless you have a strong reason not to. Workspace and extra-dir discovery only accepts skill roots and `SKILL.md` files whose resolved path stays inside the configured root.

## Per-skill overrides

```json5
{
  skills: {
    entries: {
      "image-lab": {
        enabled: true,
        apiKey: { source: "env", provider: "default", id: "GEMINI_API_KEY" },
        env: {
          GEMINI_API_KEY: "GEMINI_KEY_HERE",
        },
        config: {
          endpoint: "https://example.invalid",
        },
      },
    },
  },
}
```

Important behavior:

- `env` is injected only if that variable is not already set in the host process
- `apiKey` is mainly a convenience for skills that declare a primary env var
- custom per-skill fields belong under `config`

## Host runs vs sandboxed runs

This is the most common source of confusion:

- `skills.entries.*.env` and `skills.entries.*.apiKey` apply to host runs
- sandboxed skill processes do not inherit the host `process.env`

For sandboxed agents, route needed env through one of:

- `agents.defaults.sandbox.docker.env`
- `agents.list[].sandbox.docker.env`
- a custom sandbox image that already contains the needed runtime setup

## Watcher tuning

```json5
{
  skills: {
    load: {
      watch: true,
      watchDebounceMs: 1000,
    },
  },
}
```

Guidance:

- leave the default `250` ms unless reload churn is a real problem
- increase to `500-2000` ms during active skill development if repeated saves cause noisy reloads
- reduce only when a faster feedback loop is clearly needed

## Common patterns

### Shared team skills

```json5
{
  skills: {
    load: {
      extraDirs: ["/opt/team-skills"],
    },
  },
}
```

### Workspace-only override of a shared skill

Put the replacement skill in:

```text
<workspace>/skills/<skill-name>/SKILL.md
```

That workspace copy will beat both `~/.openclaw/skills` and bundled copies.

### Bundled-skill allowlist

```json5
{
  skills: {
    allowBundled: ["peekaboo", "gemini"],
  },
}
```

This affects bundled skills only. Workspace and managed/local skills are unaffected.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Skill does not appear | Wrong location or no valid `SKILL.md` under the configured root | Verify the directory and file path |
| Wrong version loads | Higher-precedence copy shadows the intended one | Check workspace and managed/local copies first |
| Env vars seem ignored | `skills.entries` key does not match the skill key | Match the skill name or `metadata.openclaw.skillKey` |
| Skill works on host but fails in sandbox | Host env did not reach the sandbox | Use sandbox docker env or a custom image |
| Bundled skill unexpectedly unavailable | `skills.allowBundled` excludes it | Add it to the allowlist or remove the allowlist |

## Validation checklist

- [ ] The active workspace path is known
- [ ] The intended skill location matches the required precedence
- [ ] Every `skills.entries` key matches the skill name or `skillKey`
- [ ] Sandbox env needs are handled separately from host env
- [ ] The runtime shows the expected skill set after reload
