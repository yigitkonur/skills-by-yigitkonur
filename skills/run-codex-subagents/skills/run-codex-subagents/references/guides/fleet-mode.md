# Fleet Mode

`codex-worker` supports a fleet-specific instruction append when the environment variable below is enabled:

```bash
export CODEX_ENABLE_FLEET=1
```

With that enabled, thread-start and thread-resume flows append fleet developer instructions before the turn runs.

## When To Use It

Use fleet mode when:
- the wrapper environment expects extra shared orchestration rules
- you want consistent behavior across many worker threads launched by the same operator

## Verification

```bash
CODEX_ENABLE_FLEET=1 codex-worker thread start --cwd /abs/project
```

If you do not need fleet-specific behavior, leave the variable unset.
