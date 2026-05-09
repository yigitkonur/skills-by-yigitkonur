# Adaptive Search Examples

Each example shows a small first pass, an internal filter, and one refinement.

## Example 1: Self-hosted Notion alternative

**Need:** collaborative self-hosted docs or knowledge base

**First pass**
1. `notion alternative`
2. `self-hosted wiki`
3. `outline OR affine`
4. `block editor collaborative docs`

**What to harvest from results**
- repo wording like `knowledge base`, `wiki`, `collaborative docs`, `workspace`
- likely product names that dominate the space

**Refinement**
- `knowledge base self-hosted`
- `collaborative wiki self-hosted`

## Example 2: AI code review bot

**Need:** repos that review pull requests with AI assistance

**First pass**
1. `ai code review`
2. `pull request review bot`
3. `coderabbit OR greptile`
4. `llm pr review`

**What to harvest from results**
- whether the field uses `code review bot`, `PR review`, `review agent`, or `GitHub App`
- whether promising repos position themselves as review bots, linters, or agents

**Refinement**
- `review agent github app`
- `ai pull request bot`

## Example 3: TypeScript MCP server framework

**Need:** frameworks or starter repos for building MCP servers in TypeScript

**First pass**
1. `mcp server typescript`
2. `model context protocol typescript`
3. `mcp framework typescript`
4. `mcp sdk typescript`

**What to harvest from results**
- whether repos call themselves `sdk`, `framework`, `starter`, or `boilerplate`
- whether relevant repos are libraries, example packs, or full applications

**Refinement**
- `mcp starter typescript`
- `mcp boilerplate typescript`

## Example 4: Fuzzy naming problem

**Need:** repos for "browser agents" where projects may use other labels

**First pass**
1. `browser agent`
2. `web automation agent`
3. `browser copilots`
4. `playwright ai agent`

**Observed issue:** repo names may use `automation`, `operator`, `assistant`, or `copilot` instead of `agent`.

**Refinement**
- pivot to the discovered naming cluster that showed up in repo descriptions
- optionally use web/MCP search to learn community labels, then return to GitHub search
