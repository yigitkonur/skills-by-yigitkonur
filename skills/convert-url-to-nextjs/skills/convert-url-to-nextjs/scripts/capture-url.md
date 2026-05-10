# capture-url.sh

Use `scripts/capture-url.sh` during the Capture Wave to create the deterministic route artifact skeleton before browser work starts.

## Inputs

```bash
scripts/capture-url.sh --url https://example.com/pricing --route pricing --root .
```

Options:

| Option | Required | Purpose |
|---|---:|---|
| `--url` | yes | Source route to capture |
| `--route` | no | Kebab-case route id; derived from URL when omitted |
| `--root` | no | Working root that owns `.design-soul/`; defaults to current directory |
| `--browser-command` | no | Shell command that performs capture using exported paths |

`BROWSER_CAPTURE_CMD` may be used instead of `--browser-command`.

## Behavior

- Creates `.design-soul/capture/{route}/`.
- Creates `mirror/{css,js,fonts,images}/` and `screenshots/`.
- Writes `expected-artifacts.json` and `capture-handoff.md`.
- Exports paths for a supplied browser command:
  - `CAPTURE_URL`
  - `CAPTURE_ROUTE`
  - `CAPTURE_DIR`
  - `DOM_PATH`
  - `HEADINGS_PATH`
  - `RUNTIME_METADATA_PATH`
  - `ASSETS_PATH`
  - `MIRROR_DIR`
  - `SCREENSHOTS_DIR`

## Browser Routing

Use `run-agent-browser` for the command that creates the actual artifacts.

The script does not perform browser automation by itself. It delegates to the supplied command and then verifies that required files exist.

## Failure Rules

- If the browser command exits nonzero, the script exits nonzero and writes `capture-status.json`.
- If the browser command exits zero but required artifacts are missing, the script exits nonzero.
- The script never writes `done.signal`; the executor writes it only after the full Capture Wave gate passes.
