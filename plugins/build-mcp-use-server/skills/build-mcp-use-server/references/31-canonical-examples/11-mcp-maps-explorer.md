# Canonical: `mcp-use/mcp-maps-explorer`

**URL:** https://github.com/mcp-use/mcp-maps-explorer
**Hosted demo:** https://super-night-ttde2.run.mcp-use.com/mcp

The Leaflet-map widget reference. `show-map` produces an interactive map with colored markers, `add-markers` mutates the in-process map state, and `get-place-details` returns structured lookup data for marker clicks.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`markerSchema`) | The marker shape — `lat`, `lng`, `title`, optional `description`, optional color enum |
| `index.ts` (`lastMapState` module-scope ref) | In-process current-map document |
| `index.ts` (`placeDatabase` constant) | Hand-curated metadata so `get-place-details` can answer without calling out |
| `index.ts` (`show-map` tool) | The map schema — center, zoom, title, and an array of markers |
| `index.ts` (`add-markers` tool) | In-process mutation that merges new markers into `lastMapState` |
| `index.ts` (`get-place-details` tool) | Structured lookup tool that does not return a widget |
| `resources/map-view/widget.tsx` | Leaflet init, marker color icons, popup descriptions, fullscreen |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Rendering an array of structured marker objects | `show-map` schema + widget |
| Hand-curated lookup table as an alternative to an external geocoding API | `placeDatabase` |
| Mixing widget tools and structured/plain tools in the same server | `show-map`, `add-markers`, and `get-place-details` |
| Color enum mapped to icon variants in the widget | `marker.color` → Leaflet icon URL |
| Tile-layer choice (OpenStreetMap, no API key) | `widget.tsx` Leaflet init |

## Clusters this complements

- `../31-canonical-examples/10-mcp-slide-deck.md` — another multi-item visual widget
- `../18-mcp-apps/widget-react/` — React widget mechanics

## When to study this repo

- You are building a widget that integrates a map / geo-spatial library.
- You want a marker-array example with a third-party render lib (Leaflet).
- You need a precedent for color-enum → icon-variant mapping.
- You have a small, finite domain dataset and want to avoid external API dependencies.

## Local run

```bash
gh repo clone mcp-use/mcp-maps-explorer
cd mcp-maps-explorer
npm install
npm run dev
```
