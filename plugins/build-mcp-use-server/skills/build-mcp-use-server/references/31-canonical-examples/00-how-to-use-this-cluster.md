# Canonical Examples Cluster

*Read this first to understand how to navigate real working examples.*

This cluster distinguishes two different things that both get called "examples":

1. **Canonical in-repo examples** — real, maintained source under `libraries/typescript/packages/server/examples/` in the `mcp-use/mcp-use` monorepo, indexed at `docs/v2/typescript/server/examples.mdx`. These are the maintained reference for server behavior; the repository's example registry runs automated verification against them. `03-example-inventory.md` lists all ~30 of them by category.
2. **External template gallery** — separately hosted, standalone GitHub repos (`mcp-use/mcp-chart-builder`, `mcp-use/mcp-diagram-builder`, etc.), each with a live demo and a one-click deploy button, listed on the marketing site's Templates page. **These are not canonical repository fixtures.** The vendor's own docs say so explicitly: "Community and product showcases are not canonical repository fixtures... a repository example is the maintained reference for server behavior" (`docs/v2/typescript/server/examples.mdx`). `01-chart-builder.md` and `02-diagram-builder.md` cover two of these — verified metadata only (tool names, demo URL, GitHub repo); their internal code is not part of the monorepo and was not independently verifiable against shipped source, so treat any code shown there as illustrative, not quoted.

## Quick start

1. **Want a maintained, verifiable code pattern to copy?** Go to `03-example-inventory.md` and clone the matching in-repo example from `libraries/typescript/packages/server/examples/`.
2. **Want a deployable full app to fork and re-skin?** Use the external template gallery (`01-chart-builder.md`, `02-diagram-builder.md`, or the fuller list in `03-example-inventory.md`) — clone the standalone repo, not a monorepo subdirectory.
3. **Try a live demo first:** Both categories expose a live MCP endpoint. Paste it into the [Inspector](/inspector/index) under "Direct" transport before cloning anything.

## What's included

- **01-chart-builder.md** — External template: natural-language chart generation (tool: `create-chart`). Verified demo URL and GitHub repo; illustrates structured output + view binding at the metadata level.
- **02-diagram-builder.md** — External template: conversational diagram editing (tools: `create-diagram`, `edit-diagram`). Verified demo URL and GitHub repo; illustrates a multi-tool workflow at the metadata level.
- **03-example-inventory.md** — Full grounded list: every in-repo canonical example (core protocol, views, auth, runtime/deployment) plus the external template gallery. Start here if looking for a specific pattern.

## How to read each example

Each file shows:
- What the example does
- The live MCP endpoint URL (paste into Inspector under "Direct" transport), where one exists
- The GitHub source (in-repo path or standalone repo — noted per example)
- Key tools exposed
- Clone/deploy instructions

The Inspector lets you call tools before you commit to cloning.
