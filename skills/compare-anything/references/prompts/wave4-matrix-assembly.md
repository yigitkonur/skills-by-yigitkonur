# Wave 4: Master Assembly & Matrix Compilation Prompt

You are the Lead Synthesis Architect. All candidate tools have completed their Wave 2 research and Wave 3 verification audits. Your job is to assemble all verified per-tool JSONs into the final canonical dataset for the Canvas comparison matrix.

## Objectives
1. **Reconciliation & Integrity**:
   - Verify that every candidate tool defines values for every criterion in the frozen schema.
   - Retain all `evidence`, `confidence`, `uncertainty`, `prediction`, and `verificationAudit` metadata on every cell.
2. **Scoring Calibration**:
   - Verify that default weights (0–10) are logically calibrated so the total weighted scores provide a fair, balanced assessment.
3. **Summary Statistics**:
   - Compile `metadata.waveStats`:
     - `discoveredCandidates`: total tool count
     - `expandedCriteriaCount`: total criteria count
     - `verifiedEvidenceRatio`: percentage of cells with direct citations
     - `uncertaintyCount`: count of cells with `isUncertain: true`
4. **Save Target**:
   - Output the finalized matrix JSON to `content/matrix/<slug>.json`.
   - Run deterministic validation:
     ```bash
     node scripts/validate-matrix-schema.mjs content/matrix/<slug>.json
     ```
5. **Astro Route**:
   - The dynamic route `frontend/src/pages/compare/[slug].astro` automatically picks up all `content/matrix/*.json` files at build time. No page creation is needed for new matrix slugs.
   - If the route file is missing (e.g. on a fresh checkout), refer to `references/executable-template-guide.md` for the recipe.
