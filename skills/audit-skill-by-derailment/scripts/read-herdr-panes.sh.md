# `read-herdr-panes.sh`

Extracts, formats, and analyzes terminal scrollback logs and cognitive thought blocks from one or more active Herdr agent panes.

## Usage

```bash
bash scripts/read-herdr-panes.sh [options] <pane-id> [pane-id2 ...]
```

## Options

- `-n, --lines <N>`: Number of scrollback lines to fetch per pane (default: 300).
- `--source <src>`: Herdr source (`recent-unwrapped` [default], `visible`, `recent`, `detection`).
- `--thoughts`: Filters and highlights agent thought and reasoning blocks.
- `--tools`: Filters and highlights agent tool invocations (`● Edit`, `● Bash`, etc.).
- `-h, --help`: Displays help message.

## Examples

```bash
# Read recent scrollback from website-yigitkonur and aura-monorepo panes
bash scripts/read-herdr-panes.sh wJ:p2 wH:p4 --lines 400

# Extract agent thoughts from gocmenpsikolog pane
bash scripts/read-herdr-panes.sh wK:p2 --thoughts
```
