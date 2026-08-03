# Full Example Inventory

*Read this to find a specific example pattern or tool type.*

Two separate lists. **Canonical in-repo examples** are maintained source under `libraries/typescript/packages/server/examples/` in the `mcp-use/mcp-use` monorepo, indexed at `docs/v2/typescript/server/examples.mdx` — these are the source of truth for API patterns. The **external template gallery** is a set of standalone, separately hosted repos with live demos, indexed at `docs/home/templates.mdx` — good for forking a deployable app, not for citing as canonical server behavior (the vendor's own docs: "a repository example is the maintained reference for server behavior," not a showcase).

## Canonical in-repo examples

Source: `docs/v2/typescript/server/examples.mdx`, cross-checked against the real directory listing under `libraries/typescript/packages/server/examples/` on the `mcp-use/mcp-use` beta branch.

### Core protocol and lifecycle

| Example | What it demonstrates |
|---------|----------------------|
| `basic` | Tools, a resource, and a prompt |
| `conformance` | Protocol conformance fixtures; use focused examples for application patterns |
| `middleware` | Request-scoped MCP middleware |
| `notifications` | `subscriptions/listen` invalidations |
| `sampling` | The stateless server-side sampling boundary |
| `security` | Host and origin validation |
| `sessionless-lifecycle` | Request-scoped context without session affinity |
| `elicitation` | Form and URL input-required rounds (`inputRequired`, `inputRequired.elicit`, `inputResponse`, `acceptedContent`) |
| `resource-template-completion` | Resource-template autocomplete |
| `events` | Read-only request observers |
| `proxy` | Composing upstream MCP servers |

### Views (MCP Apps)

| Example | Notes |
|---------|-------|
| `views/basic` | "Fruit Store" reference server: view-bound + plain tools, capability gating (`ctx.client.supportsViews()`), elicitation, sampling round-trip, resources/resource templates/prompts |
| `views/excalidraw` | Streaming tool input, manual resize, `visibility: "app"` helper tools, external CSP domains, `permissions` |
| `views/file-upload` | File upload flow through a view |
| `views/property-search` | "HomeScout SF" — split list/map view, `useSendFollowUp`, `useCallTool` for app-only tools, six `useViewTool` host-callable tools. Present in the examples directory but not listed in `examples.mdx`'s Views section — verify current status before depending on it. |
| `views/story-writer` | Interactive story generation view |
| `views/tic-tac-toe` | Simple game view with server-authoritative state |
| `views/view-state` | View state persistence patterns |

### Schema libraries

Not listed in `examples.mdx` but present under `examples/schema-libraries/`: `zod`, `arktype`, `typebox` — the same `greet` tool implemented with each Standard Schema-compatible library. See `references/04-tools/03-schemas-standard-schema-and-zod-v4.md` for the pattern.

### Authentication

Under `examples/auth/`: `auth0`, `better-auth`, `clerk`, `keycloak`, `supabase`, `workos`. Each requires provider credentials/tenants; repository verification checks configuration, not live provider calls. See `references/11-auth/providers/`.

### Runtime and deployment

| Example | Target |
|---------|--------|
| `nextjs` | Drop-in Next.js route |
| `nextjs-standalone` | Standalone Next.js application |
| `vercel` | Serverless Web `fetch` handler |
| `railway` | Railway deployment |
| `openapi` | Generated tools for weather.gov |
| `public-landing` | Public server landing page |

Clone and run any of these from the monorepo:

```bash
git clone https://github.com/mcp-use/mcp-use
cd mcp-use/libraries/typescript/packages/server/examples/<name>
npm install
npm run dev
```

## External template gallery (deployable full apps, not in-repo)

Source: `docs/home/templates.mdx`. Each has a live demo, a standalone GitHub repo, and a one-click deploy button through Manufact Cloud.

| Template | Tools | Live endpoint | GitHub source |
|----------|-------|----------------|----------------|
| **Chart Builder** | `create-chart` | `https://yellow-shadow-21833.run.mcp-use.com/mcp` | [mcp-use/mcp-chart-builder](https://github.com/mcp-use/mcp-chart-builder) |
| **Diagram Builder** | `create-diagram`, `edit-diagram` | `https://lucky-darkness-402ph.run.mcp-use.com/mcp` | [mcp-use/mcp-diagram-builder](https://github.com/mcp-use/mcp-diagram-builder) |
| **Slide Deck** | `create-slides`, `edit-slide` | `https://solitary-block-r6m6x.run.mcp-use.com/mcp` | [mcp-use/mcp-slide-deck](https://github.com/mcp-use/mcp-slide-deck) |
| **Maps Explorer** | `show-map`, `get-place-details`, `add-markers` | `https://super-night-ttde2.run.mcp-use.com/mcp` | [mcp-use/mcp-maps-explorer](https://github.com/mcp-use/mcp-maps-explorer) |
| **Hugging Face Spaces** | `search-spaces`, `show-space`, `trending-spaces` | `https://gentle-frost-pvxpk.run.mcp-use.com/mcp` | [mcp-use/mcp-huggingface-spaces](https://github.com/mcp-use/mcp-huggingface-spaces) |
| **Recipe Finder** | `search-recipes`, `get-recipe`, `meal-plan`, `recipe-suggestion` | `https://bold-tree-1fe79.run.mcp-use.com/mcp` | [mcp-use/mcp-recipe-finder](https://github.com/mcp-use/mcp-recipe-finder) |
| **Widget Gallery** | `show-react-widget`, `html-greeting`, `mcp-ui-poll`, `programmatic-counter`, `detect-client` | `https://wandering-lake-mmxhs.run.mcp-use.com/mcp` | [mcp-use/mcp-widget-gallery](https://github.com/mcp-use/mcp-widget-gallery) |
| **Multi Server Hub** | `hub-status`, `hub-config-example`, `audit-log` | `https://soft-voice-4nxfi.run.mcp-use.com/mcp` | [mcp-use/mcp-multi-server-hub](https://github.com/mcp-use/mcp-multi-server-hub) |
| **File Manager** | `open-vault`, `get-file`, `list-files` | `https://muddy-pond-eyays.run.mcp-use.com/mcp` | [mcp-use/mcp-file-manager](https://github.com/mcp-use/mcp-file-manager) |
| **Progress Demo** | `process-data`, `fetch-report`, `delete-dataset`, `search-external`, `failing-tool` | `https://crimson-river-pzsz1.run.mcp-use.com/mcp` | [mcp-use/mcp-progress-demo](https://github.com/mcp-use/mcp-progress-demo) |
| **i18n Adaptive** | `show-context`, `detect-caller` | `https://falling-grass-58yov.run.mcp-use.com/mcp` | [mcp-use/mcp-i18n-adaptive](https://github.com/mcp-use/mcp-i18n-adaptive) |
| **Media Mixer** | `generate-image`, `generate-audio`, `generate-pdf`, + more | `https://wandering-breeze-nuipu.run.mcp-use.com/mcp` | [mcp-use/mcp-media-mixer](https://github.com/mcp-use/mcp-media-mixer) |
| **Resource Watcher** | `show-config`, `update-config`, `toggle-feature`, `list-roots` | `https://fragrant-term-zmdks.run.mcp-use.com/mcp` | [mcp-use/mcp-resource-watcher](https://github.com/mcp-use/mcp-resource-watcher) |

Deploy any of these with the repo's own "Deploy" link, or after cloning: `npm run deploy` (see `references/25-deploy/`).

## How to use

1. **Need a maintained code pattern?** Clone the matching in-repo example above and read its source directly.
2. **Need a deployable full app?** Copy a template gallery demo URL into [Inspector](/inspector/index) under **Direct transport**, call a tool or two, then clone the standalone repo if it fits.
3. **Testing without cloning:** the Inspector connects to any live endpoint (in-repo examples do not have public demo URLs; template gallery entries do).

## Patterns by tool type

### Structured output + views
- In-repo: `views/basic`, `views/excalidraw`, `views/property-search`, `views/story-writer`, `views/tic-tac-toe`, `views/view-state`
- Template gallery: Chart Builder (`create-chart`), Diagram Builder (`create-diagram`, `edit-diagram`), Slide Deck (`create-slides`, `edit-slide`), Widget Gallery

### Location/geospatial
- Maps Explorer (`show-map`, `get-place-details`, `add-markers`)

### Auth
- In-repo: `auth/auth0`, `auth/better-auth`, `auth/clerk`, `auth/keycloak`, `auth/supabase`, `auth/workos`

### Deployment targets
- In-repo: `nextjs`, `nextjs-standalone`, `vercel`, `railway`, `openapi`, `public-landing`
