# Canonical: `mcp-use/mcp-huggingface-spaces`

**URL:** https://github.com/mcp-use/mcp-huggingface-spaces
**Hosted demo:** https://gentle-frost-pvxpk.run.mcp-use.com/mcp

The external-API + iframe-embedding reference. Three tools — `search-spaces`, `trending-spaces`, `show-space` — wrap the Hugging Face Spaces REST API and embed an arbitrary Space as an interactive iframe inside the widget. Demonstrates a real third-party API client and a CSP-aware iframe widget.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`searchSpaces(opts)` helper) | Realistic external REST client — query string assembly, sort/direction mapping, expand fields, error handling |
| `index.ts` (`SORT_MAP` constant) | Translating model-friendly enum values to vendor-specific API params |
| `index.ts` (`HFSpace` interface) | Shape returned to the widget — author, sdk, tags, embed URL, runtime |
| `index.ts` (`search-spaces`, `trending-spaces`, `show-space` tools) | Three tools sharing the same helper |
| `resources/spaces-browser/widget.tsx` | Iframe embedding with `allow="..."`, fullscreen, sandbox attributes |
| Widget metadata `csp.connectDomains` / `resourceDomains` / `frameDomains` | The CSP allow-list for huggingface.co domains |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| External REST API wrapper without a custom SDK — pure `fetch` + URLSearchParams | `searchSpaces` |
| Vendor-enum mapping table (`SORT_MAP`) to keep the tool schema clean | Top of `index.ts` |
| Embedding third-party iframes safely — CSP `frameDomains` declaration in widget metadata | `widget.tsx` `widgetMetadata.metadata.csp` |
| `allow="autoplay; clipboard-read; clipboard-write"` and `sandbox` on the iframe | `widget.tsx` |
| Three tools backed by one helper, each with a slightly different default | `search-spaces`, `trending-spaces`, `show-space` |
| Trending fallback when the user query is empty | Default sort `trendingScore`, direction `desc` |

## Clusters this complements

- `../18-mcp-apps/widget-react/` — CSP fields in `widgetMetadata.metadata.csp`
- `../30-workflows/05-github-api-wrapper-with-cache.md` — similar REST-wrapper shape with caching layered on top
- `../17-advanced/` — Hono passthrough for CSP headers

## When to study this repo

- You are wrapping any external REST API as MCP tools.
- Your widget must embed third-party iframes (YouTube, Spotify, Hugging Face, custom dashboards).
- You need to declare CSP allow-lists for `connectDomains`, `resourceDomains`, and `frameDomains`.
- You want a precedent for sharing one fetch helper across multiple tools with different defaults.

## Local run

```bash
gh repo clone mcp-use/mcp-huggingface-spaces
cd mcp-huggingface-spaces
npm install
npm run dev
```
