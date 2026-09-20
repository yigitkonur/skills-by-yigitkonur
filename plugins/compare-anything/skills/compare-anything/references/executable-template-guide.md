# Executable Template Guide

This guide describes how to connect a validated `matrix.json` schema file into the Astro static workshop and expose it over a live Cloudflare Tunnel.

---

## 1. Directory Conventions

- Schema file: `content/matrix/<slug>.json` (or `frontend/src/data/matrix/<slug>.json`)
- Astro Route: `frontend/src/pages/compare/[slug].astro` (or dedicated route `frontend/src/pages/<slug>.astro`)
- Generic React Engine: `frontend/src/components/matrix/GenericMatrixPage.tsx`
- Shared Style: `frontend/src/components/recorders/styles/recorders.css`

---

## 2. Astro Page Recipe

```astro
---
// frontend/src/pages/compare/[slug].astro
import Layout from "../../layouts/Layout.astro";
import GenericMatrixPage from "../../components/matrix/GenericMatrixPage";
import "../../components/recorders/styles/recorders.css";
import fs from "node:fs";
import path from "node:path";
import { comparisonMatrixSchema } from "../../../../shared/matrix/schema";

export async function getStaticPaths() {
  const dir = path.resolve(process.cwd(), "content/matrix");
  if (!fs.existsSync(dir)) return [];
  const files = fs.readdirSync(dir).filter(f => f.endsWith(".json"));
  return files.map(file => {
    const slug = file.replace(/\.json$/, "");
    const raw = JSON.parse(fs.readFileSync(path.join(dir, file), "utf-8"));
    const data = comparisonMatrixSchema.parse(raw);
    return {
      params: { slug },
      props: { matrix: data },
    };
  });
}

const { matrix } = Astro.props;
---

<Layout
  title={`${matrix.title} — Empirical Comparison & Benchmarks`}
  description={matrix.description}
  hasTranslations={false}
>
  <script is:inline>
    if (!document.documentElement.dataset.theme) {
      document.documentElement.dataset.theme = 'dark';
      document.documentElement.style.colorScheme = 'dark';
    }
  </script>

  <div class="page-intro" id="top">
    <a class="eyebrow" href="/research">← RESEARCH & BENCHMARKS</a>
    <h1>{matrix.title}<span style="color:var(--orange)">.</span></h1>
    <p>{matrix.description}</p>
  </div>

  <div class="comparison-workspace-container">
    <GenericMatrixPage client:load schema={matrix} />
  </div>
</Layout>
```

---

## 3. Verification & Live Preview

Before opening the preview to the user, run the hermetic checks:

```bash
# 1. Validate the matrix schema:
node .agents/skills/compare-anything/scripts/validate-matrix-schema.mjs content/matrix/<slug>.json

# 2. Build and typecheck:
npm run build:frontend && npm run typecheck

# 3. Launch live tunnel with 3-gate verification:
bash scripts/dev/live-tunnel.sh start --port 4321 --path /compare/<slug>
```
