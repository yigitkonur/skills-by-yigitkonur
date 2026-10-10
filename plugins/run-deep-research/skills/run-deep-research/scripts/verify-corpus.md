# verify-corpus.sh

Use `scripts/verify-corpus.sh` at the end of Wave 2, Wave 3, and during Phase 7 to deterministically verify corpus integrity.

## Usage

```bash
# During intermediate wave gates:
bash scripts/verify-corpus.sh <corpus-root-path>

# During Phase 7 completion gate (enforces master summary presence):
bash scripts/verify-corpus.sh --final <corpus-root-path>
```

## What It Evaluates

1. **Junk Files**: Detects unwanted `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.bak`.
2. **Placeholder Text**: Detects forbidden strings (`TODO`, `TBD`, `fill later`, `<placeholder>`, `???`).
3. **MAX-N Folder Caps**:
   - `_meta/`: MAX 8 markdown files
   - `<entity-slug>/`: MAX 3 markdown files (`dossier.md`, `sources.md`, optional deep dive)
   - `_cross/<axis-slug>/`: MAX 3 markdown files (`synthesis.md`, optional `scenarios.md`)
4. **Core Deliverables**: Confirms `README.md` and `_meta/manifest.json`.
5. **Machine Layer & Frontmatter**: Verifies every entity folder contains `dossier.md` with valid YAML frontmatter delimiters (`---`) and `sources.md`.
6. **Cross Synthesis**: Verifies every axis folder under `_cross/` contains `synthesis.md`.
7. **Master Summary**: Confirms `_meta/00-master-summary.md` (mandatory in `--final` mode).
