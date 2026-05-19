# Workflow — Phased Procedure

The end-to-end procedure for producing `design.md` + the `references/[context]/` tree from a source. Six phases. The skill never claims done before completing Phase 6.

> Before producing any `design.md` for a real source, re-read `references/design-md-spec.md` so the output is consistent across runs.

---

## Phase 1 — Frame the source and scope

**Inputs:** the user's request.

**Outputs:** a one-line scope statement, source mode, target root, declared contexts.

Procedure:

1. Restate the scope in one line. Example: *"Document the visual system of the dashboard at admin.example.com — full extraction, oversize the sidebar context."*
2. Identify the **source mode**:
    - **Live URL** — running app, requires browser capture.
    - **Codebase** — repository with `package.json` (or `pyproject.toml`, etc.) and component source files.
    - **HTML snapshot** — `.html` + adjacent CSS, or SingleFile export.

    Routing per source mode: `references/source-variants.md`.

3. Decide the **target root** — where `design.md` and `references/` will be written. Defaults:
    - Codebase source → repo root.
    - Live URL → a writable working directory (e.g. `~/.design-soul-<domain>/`).
    - Snapshot → the directory containing the snapshot.

4. Declare which `[context]/` directories the run will produce. Start with the canonical set in `references/output-tree.md`; trim contexts the source genuinely doesn't have (e.g. no `motion/` for a static print-style design).

Acceptance: scope is one sentence. Mode is one of three. Target root is an absolute path. Context list is finite.

---

## Phase 2 — Inventory contexts (no content yet)

**Inputs:** Phase 1 output.

**Outputs:** the list of `[context]/` directories the run will create.

Procedure:

1. Walk the source breadth-first looking for evidence of each canonical context.
2. For each context with evidence, mark it included.
3. For each context without evidence, mark it excluded with reason. Excluded contexts get a one-line note under their would-be section in `design.md`.
4. Add new domain-specific contexts when the source has a strong cluster of concepts not covered by the canonical set (e.g. a charts-heavy analytics tool warrants `charts/`).

Acceptance: every `[context]/` decision has a reason. Excluded contexts have a reason recorded for Phase 5.

---

## Phase 3 — Per-context asset inventory (no content yet)

**Inputs:** Phase 2 output.

**Outputs:** for each `[context]/`, a flat list of `NN-slug` stems.

Procedure for each `[context]/`:

1. Enumerate every asset the context will contain. Examples:
    - `tokens/` — every CSS custom property in the source's theme/root selectors.
    - `typography/` — every font family, size, weight, line-height, letter-spacing value.
    - `components/` — every component the design exposes (walk component source files, walk DOM exemplars).

2. Assign `NN-` ordinals reflecting reading order. Foundational assets first (`01-base-unit` before `02-spacing-scale`).

3. Pick the slug. Use the most specific noun a reproducer would search for. `button-primary`, not `button` or `primary-button-component`.

Acceptance: every stem is unique within its context, ordered, and named with a specific noun.

Helpful tools at this phase:

- For codebase source: see `references/extraction-cheatsheet.md` for grep patterns.
- For live URL: invoke `run-agent-browser` and snapshot the relevant routes; record DOM evidence.
- For HTML snapshot: read every `.html` and `.css` file; record every selector that exposes a token-bearing rule.

---

## Phase 4 — Per-asset capture

**Inputs:** Phase 3 stems.

**Outputs:** every `references/[context]/NN-slug.md` and `.json` populated.

Procedure for each stem:

1. **Write the JSON first.** It has rigid structure; once correct, the `.md` writes itself around it.
2. **Resolve every token chain to its literal.** Example: `bg-primary` → `var(--primary)` → `#1A1C1E`. Never stop at the class name; never stop at the alias.
3. **Write states explicitly.** For every state in the per-asset template's States table:
    - If the source implements it → record the values.
    - If the source does not implement it → write `not-implemented`.
    - Never omit a state row.
4. **Record source evidence.** File path, selector, CSS variable, line range. This is the audit trail.
5. **Write the `.md`** mirroring the JSON. Cross-reference (do not duplicate) the JSON's machine values.

Rules of thumb:

- Source over screenshot.
- Document, don't redesign.
- Absence is evidence — `not-implemented` over silence.
- Preserve the source's vocabulary in prose; map to canonical vocabulary in the JSON.

Cheatsheet for token-chain resolution, Tailwind-to-CSS conversions, oklch reading: `references/extraction-cheatsheet.md`.

---

## Phase 5 — Assemble design.md

**Inputs:** the populated `references/[context]/` tree.

**Outputs:** `design.md` at the target root.

Procedure:

1. **Frontmatter first.** Pull tokens from:
    - `references/tokens/*.json` → `colors:` map (where `tokenType: color`).
    - `references/typography/*.json` → `typography:` map (where `tokenType: typography`).
    - `references/radius/*.json` → `rounded:` map.
    - `references/spacing/*.json` → `spacing:` map.
    - `references/components/*.json` → `components:` composites (using the JSON's `tokens` block, which already uses curly-brace references).

2. **Body in canonical section order.** Use `references/design-md-spec.md` as the authoritative guide. For each section:
    - Open with one-paragraph framing.
    - List every relevant token / asset with a link to its `references/[context]/NN-*.{md,json}` pair.
    - Keep prose concise — the per-asset files carry the depth.

3. **`## References Index` last.** Walk the actual file tree and emit a table:

    ```markdown
    | Path | Purpose |
    |---|---|
    | `references/tokens/01-color-primary.md` | Primary color token — purpose, mode, consumers. |
    | `references/tokens/01-color-primary.json` | Primary color token — machine values. |
    | ... | ... |
    ```

Acceptance: `design.md` is a valid DESIGN.md (frontmatter + canonical sections in order). Every per-asset file is linked at least once.

---

## Phase 6 — Cross-reference verification

**Inputs:** `design.md` + the `references/[context]/` tree.

**Outputs:** a pass/fail report; revisions until pass.

Use the rungs in `references/verification.md`. The bar:

- Every asset has both files.
- Every asset is linked from `design.md`.
- Every token in `design.md` frontmatter has a `references/tokens/` asset.
- Every component listed under `## Components` has a `references/components/` asset pair.
- Every `references/[context]/NN-*.md` file is referenced from `design.md` (typically via the References Index).
- Every JSON `consumers`/`dependsOn` graph edge resolves.
- Every state in every component JSON is explicitly defined or `not-implemented` (no missing keys, no `null`).

If any check fails, fix and re-run. Never claim done with an open check.

---

## Re-entry triggers

If during execution the scope changes, the source reveals something Phase 1 didn't anticipate, or two assets contradict, loop back:

| Trigger | Loop back to |
|---|---|
| New context emerges (e.g. discovering chart palette mid-extraction) | Phase 2 — add it, then continue. |
| New component family emerges | Phase 3 — extend the components inventory. |
| Two values conflict across files | Document dominant in the asset's `.md`; list exceptions in the **Notes** section. Do not loop back. |
| Source insufficient for a state | Record `not-implemented`. Do not invent. |
| User's scope changes | Phase 1 — restate scope; re-run from there. |

Never silently expand scope. Every re-entry is recorded in the run notes (or commit message).
