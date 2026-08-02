# Reference Index

*Full inventory fallback. Prefer the intent table and symptom index in SKILL.md; come here only when you need an exact filename.*


## 01-concepts

- `references/01-concepts/01-what-is-mcp-use.md` — What is mcp-use
- `references/01-concepts/02-server-vs-client-vs-agent.md` — Server vs Client vs Agent
- `references/01-concepts/03-transports-overview.md` — Transports Overview
- `references/01-concepts/04-stateless-model-and-request-state.md` — Stateless Model and Request State
- `references/01-concepts/05-mcp-spec-version-history.md` — MCP Spec Version History
- `references/01-concepts/06-mcp-apps-and-views-terminology.md` — MCP Apps and Views Terminology
- `references/01-concepts/07-this-skill-vs-build-mcp-use-client.md` — This Skill vs build-mcp-use-client

## 02-setup

- `references/02-setup/01-prerequisites.md` — Prerequisites
- `references/02-setup/02-scaffold-with-create-mcp-use-app.md` — Scaffold with create-mcp-use-app
- `references/02-setup/03-template-flags.md` — Template flags
- `references/02-setup/04-manual-http-server.md` — Manual HTTP server
- `references/02-setup/05-add-to-existing-app.md` — Add to existing app
- `references/02-setup/06-package-scripts.md` — Package scripts
- `references/02-setup/07-tsconfig-and-types.md` — tsconfig and types
- `references/02-setup/08-env-vars.md` — Environment variables

## 03-cli

- `references/03-cli/01-overview.md` — CLI Overview
- `references/03-cli/02-create-mcp-use-app.md` — create-mcp-use-app
- `references/03-cli/03-mcp-use-dev.md` — mcp-use dev
- `references/03-cli/04-mcp-use-build-and-typecheck.md` — Build and Typecheck
- `references/03-cli/05-mcp-use-start.md` — mcp-use start
- `references/03-cli/06-mcp-use-deploy-and-cloud.md` — Cloud Deployment and Management
- `references/03-cli/07-login-and-org.md` — Login and Organization
- `references/03-cli/08-client-and-screenshot.md` — Client and Screenshot
- `references/03-cli/09-flag-reference.md` — Flag Reference
- `references/03-cli/10-environment-variables.md` — Environment Variables

## 04-tools

- `references/04-tools/01-overview.md` — Tools Overview
- `references/04-tools/02-registering-a-tool.md` — Registering a Tool
- `references/04-tools/03-schemas-standard-schema-and-zod-v4.md` — Schemas: Standard Schema & Zod v4
- `references/04-tools/04-describe-and-annotations.md` — `.describe()` and Annotations
- `references/04-tools/05-the-ctx-object.md` — The `ctx` Object (RequestContext)
- `references/04-tools/06-validation-pipeline.md` — Validation Pipeline
- `references/04-tools/07-input-schema-vs-output-schema.md` — `inputSchema` vs `outputSchema`
- `references/04-tools/08-tool-anti-patterns.md` — Tool Anti-Patterns
- `references/04-tools/canonical-anchor.md` — Canonical Anchor — Complete Tool Example

## 05-responses

- `references/05-responses/01-overview-decision-table.md` — Response envelopes: decision table
- `references/05-responses/02-text-and-content-blocks.md` — Text and content blocks
- `references/05-responses/03-structured-content-and-output-schema.md` — Structured content and output schema
- `references/05-responses/04-images-audio-binary-resources.md` — Images, audio, binary, and resources
- `references/05-responses/05-error-handling.md` — Error handling
- `references/05-responses/06-meta-and-private-data.md` — _meta and private data
- `references/05-responses/07-deprecated-v1-helpers.md` — Deprecated v1 response helpers
- `references/05-responses/canonical-anchor.md` — Canonical response example

## 06-resources

- `references/06-resources/01-overview.md` — Resources Overview
- `references/06-resources/02-static-resources.md` — Static Resources
- `references/06-resources/03-resource-templates.md` — Resource Templates
- `references/06-resources/04-binary-and-image.md` — Binary and Image Resources
- `references/06-resources/05-uri-conventions.md` — URI Conventions
- `references/06-resources/06-subscriptions-listen.md` — Resource Subscriptions & Listening (Stateless Model)
- `references/06-resources/canonical-anchor.md` — Example Reference: `mcp-use/mcp-resource-watcher`

## 07-prompts

- `references/07-prompts/01-overview.md` — Prompts Overview
- `references/07-prompts/02-static-prompts.md` — Static Prompts
- `references/07-prompts/03-prompt-templates.md` — Prompt Templates
- `references/07-prompts/04-completable-arguments.md` — Completable Arguments
- `references/07-prompts/05-prompt-engineering.md` — Prompt Engineering Guidance

## 08-server-config

- `references/08-server-config/01-mcp-server-constructor.md` — MCPServer Constructor Options
- `references/08-server-config/02-network-basepath-and-endpoints.md` — Network, basePath, and Endpoints
- `references/08-server-config/03-cors-and-allowed-origins.md` — CORS and Origin Validation
- `references/08-server-config/04-dns-rebinding-and-host-validation.md` — DNS Rebinding and Host Validation
- `references/08-server-config/05-middleware.md` — Middleware
- `references/08-server-config/06-custom-routes.md` — Custom Routes
- `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md` — Lifecycle: listen, fetch, and Shutdown

## 09-transports

- `references/09-transports/01-overview.md` — Transports in v2
- `references/09-transports/02-streamable-http.md` — Streamable HTTP
- `references/09-transports/03-stateless-and-request-state.md` — Stateless model and request state
- `references/09-transports/04-runtime-adapters-node-next-fetch.md` — Runtime adapters: Node, Next.js, and Fetch
- `references/09-transports/05-no-stdio-and-sse-history.md` — No stdio and SSE in v2

## 10-sessions

- `references/10-sessions/01-overview-stateless-truth.md` — Sessions in v2: Stateless Truth
- `references/10-sessions/02-session-storage-roadmap.md` — Session storage roadmap
- `references/10-sessions/03-state-patterns-without-sessions.md` — State patterns without sessions
- `references/10-sessions/04-multi-instance-and-scaling.md` — Multi-instance and scaling

## 11-auth

- `references/11-auth/01-overview.md` — Authentication Overview
- `references/11-auth/02-attaching-a-provider.md` — Attaching a Provider to MCPServer
- `references/11-auth/03-ctx-auth-and-user-context.md` — Runtime: ctx.auth and User Context
- `references/11-auth/04-permission-guards.md` — Permission Guards
- `references/11-auth/05-custom-provider-oauthcustomprovider.md` — Custom Provider: oauthCustomProvider
- `references/11-auth/06-debugging-checklist.md` — Debugging OAuth
- `references/11-auth/07-oauth-proxy-removed.md` — OAuth Proxy Removed in v2
- `references/11-auth/providers/01-clerk.md` — OAuth Provider: Clerk
- `references/11-auth/providers/02-auth0.md` — OAuth Provider: Auth0
- `references/11-auth/providers/03-workos.md` — OAuth Provider: WorkOS
- `references/11-auth/providers/04-supabase.md` — OAuth Provider: Supabase
- `references/11-auth/providers/05-keycloak.md` — OAuth Provider: Keycloak
- `references/11-auth/providers/06-better-auth.md` — OAuth Provider: Better Auth

## 12-elicitation

- `references/12-elicitation/01-overview.md` — Elicitation Overview
- `references/12-elicitation/02-form-mode.md` — Form Mode
- `references/12-elicitation/03-url-mode.md` — URL Mode
- `references/12-elicitation/04-multi-round-and-request-state.md` — Multi-Round and Request State
- `references/12-elicitation/05-anti-patterns.md` — Elicitation Anti-Patterns

## 13-sampling

- `references/13-sampling/01-sampling-removed-in-v2.md` — Sampling Removed in v2

## 14-notifications

- `references/14-notifications/01-overview.md` — Notifications Overview
- `references/14-notifications/02-ctx-sendnotification.md` — ctx.sendNotification()
- `references/14-notifications/03-progress-reporting.md` — Progress Reporting with ctx.reportProgress()
- `references/14-notifications/04-list-changed-events.md` — List-Changed Events
- `references/14-notifications/05-subscriptions-delivery.md` — Subscriptions and Notification Delivery
- `references/14-notifications/canonical-anchor.md` — Canonical Notification Example

## 15-logging

- `references/15-logging/01-overview.md` — Logging Overview
- `references/15-logging/02-ctx-sendlog.md` — ctx.sendLog()
- `references/15-logging/03-server-and-request-logging.md` — Server and Request Logging

## 16-client-introspection

- `references/16-client-introspection/01-overview.md` — Client Introspection Overview
- `references/16-client-introspection/02-capabilities.md` — Capabilities and Client Feature Detection
- `references/16-client-introspection/03-apps-detection.md` — MCP Apps Detection
- `references/16-client-introspection/canonical-anchor.md` — Canonical Client Introspection Example

## 17-advanced

- `references/17-advanced/01-proxy-and-gateway.md` — Proxy and Gateway
- `references/17-advanced/02-proxy-auth-and-namespacing.md` — Proxy Auth and Namespacing
- `references/17-advanced/03-openapi-fromopenapi.md` — OpenAPI → MCP
- `references/17-advanced/04-mcp-use-vs-official-sdk.md` — mcp-use v2 vs @modelcontextprotocol/sdk
- `references/17-advanced/canonical-anchor.md` — Canonical Example: Proxy Gateway with Multi-Tenant Auth

## 18-mcp-apps

- `references/18-mcp-apps/01-what-are-mcp-apps.md` — What Are MCP Apps
- `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md` — MCP Apps vs. ChatGPT Apps SDK
- `references/18-mcp-apps/03-vocabulary-views.md` — Vocabulary: Views
- `references/18-mcp-apps/04-when-to-use-vs-tools-only.md` — When to Use Views vs. Tools-Only
- `references/18-mcp-apps/05-host-capability-detection.md` — Host Capability Detection
- `references/18-mcp-apps/anti-patterns.md` — Anti-Patterns in MCP Apps Views
- `references/18-mcp-apps/canonical-anchor.md` — Canonical Example: End-to-End Tool + View + CSP
- `references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md` — Dual-Protocol: One Server Definition, Both MCP Apps and ChatGPT
- `references/18-mcp-apps/chatgpt-apps/02-legacy-window-openai-and-skybridge.md` — Legacy: window.openai API and Skybridge MIME
- `references/18-mcp-apps/chatgpt-apps/03-csp-differences.md` — CSP Differences: MCP Apps vs. ChatGPT
- `references/18-mcp-apps/chatgpt-apps/04-runtime-detection.md` — Runtime Detection: ChatGPT vs. MCP Apps
- `references/18-mcp-apps/server-surface/01-tool-view-field.md` — The Tool `view` Field
- `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md` — Register Views and Folder Conventions
- `references/18-mcp-apps/server-surface/03-viewconfig.md` — ViewConfig: View Runtime Configuration
- `references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md` — Assets, MCP_URL, and MCP_ASSETS_URL
- `references/18-mcp-apps/server-surface/05-csp-metadata.md` — CSP Metadata: Domains and Sandbox Permissions
- `references/18-mcp-apps/view-react/01-setup-and-providers.md` — Setup and providers
- `references/18-mcp-apps/view-react/02-usetoolcontext.md` — useToolContext
- `references/18-mcp-apps/view-react/03-usecalltool.md` — useCallTool
- `references/18-mcp-apps/view-react/04-useviewstate-and-model-context.md` — useViewState and ModelContext
- `references/18-mcp-apps/view-react/05-display-modes.md` — Display modes
- `references/18-mcp-apps/view-react/06-followups-and-open-external.md` — Follow-ups and open external
- `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` — Host context, files, and size
- `references/18-mcp-apps/view-react/08-theme-and-components.md` — Theme and components

## 19-nextjs-drop-in

- `references/19-nextjs-drop-in/01-overview-withmcpuse.md` — Next.js drop-in: withMcpUse + createNextHandler
- `references/19-nextjs-drop-in/02-route-and-file-placement.md` — Route handler placement & config
- `references/19-nextjs-drop-in/03-views-in-nextjs.md` — MCP App views in Next.js
- `references/19-nextjs-drop-in/04-deploying-on-vercel.md` — Deploying Next.js MCP to Vercel

## 20-inspector

- `references/20-inspector/01-overview.md` — Inspector Overview
- `references/20-inspector/02-cli.md` — Inspector CLI
- `references/20-inspector/03-connection-settings.md` — Connection Settings
- `references/20-inspector/04-url-parameters.md` — URL Parameters
- `references/20-inspector/05-keyboard-shortcuts-and-palette.md` — Keyboard Shortcuts and Command Palette
- `references/20-inspector/06-integration-and-add-to-client.md` — Integration and Add to Client
- `references/20-inspector/07-self-hosting.md` — Self-Hosting with Docker
- `references/20-inspector/08-debugging-chatgpt-apps.md` — Debugging MCP Apps Widgets
- `references/20-inspector/09-changelog-pointer.md` — Changelog

## 21-tunneling

- `references/21-tunneling/01-overview.md` — Tunneling: Expose local MCP to remote clients
- `references/21-tunneling/02-when-to-tunnel-and-debugging.md` — When to use a tunnel + remote client debugging

## 22-validate

- `references/22-validate/01-inspector-walkthrough.md` — Inspector Walkthrough
- `references/22-validate/02-curl-handshake.md` — curl Handshake: v2 Protocol Walkthrough
- `references/22-validate/03-connect-real-clients.md` — Connect Real Clients
- `references/22-validate/04-unit-testing-server-fetch.md` — Unit Testing via server.fetch

## 23-debug

- `references/23-debug/01-debugging-workflow.md` — Debugging Workflow
- `references/23-debug/02-transport-debugging.md` — Transport Debugging
- `references/23-debug/03-view-debugging.md` — View Debugging

## 24-production

- `references/24-production/01-env-config.md` — Environment configuration for production
- `references/24-production/02-error-strategy.md` — Error handling strategy for production
- `references/24-production/03-health-and-custom-routes.md` — Health checks and custom routes
- `references/24-production/04-security-hardening.md` — Security hardening for production
- `references/24-production/05-scaling-stateless.md` — Scaling and stateless request model

## 25-deploy

- `references/25-deploy/01-decision-matrix.md` — Deployment Decision Matrix
- `references/25-deploy/02-pre-deploy-checklist.md` — Pre-Deploy Checklist
- `references/25-deploy/03-docker.md` — Docker
- `references/25-deploy/04-cli-and-org-management.md` — CLI and Org Management
- `references/25-deploy/platforms/01-mcp-use-cloud.md` — Manufact Cloud (mcp-use Cloud)
- `references/25-deploy/platforms/02-vercel.md` — Vercel
- `references/25-deploy/platforms/03-cloudflare-workers.md` — Cloudflare Workers
- `references/25-deploy/platforms/04-google-cloud-run.md` — Google Cloud Run
- `references/25-deploy/platforms/05-supabase.md` — Supabase Edge Functions
- `references/25-deploy/platforms/06-deno.md` — Deno Deploy
- `references/25-deploy/platforms/07-bun.md` — Bun
- `references/25-deploy/platforms/08-hono.md` — Hono
- `references/25-deploy/platforms/09-railway.md` — Railway
- `references/25-deploy/platforms/10-runtime-patterns.md` — Runtime Patterns

## 26-anti-patterns

- `references/26-anti-patterns/01-sdk-misuse.md` — SDK Misuse
- `references/26-anti-patterns/02-tool-design.md` — Tool Design
- `references/26-anti-patterns/03-schemas.md` — Schemas
- `references/26-anti-patterns/04-results.md` — Results
- `references/26-anti-patterns/05-security-and-cors.md` — Security and CORS

## 27-troubleshooting

- `references/27-troubleshooting/01-error-catalog.md` — Error Catalog
- `references/27-troubleshooting/02-quick-diagnostic-table.md` — Quick Diagnostic Table
- `references/27-troubleshooting/03-oauth-issues.md` — OAuth Issues
- `references/27-troubleshooting/04-view-rendering-issues.md` — View Rendering Issues
- `references/27-troubleshooting/05-csp-violations.md` — CSP Violations
- `references/27-troubleshooting/06-decision-tree.md` — Decision Tree

## 28-migration

- `references/28-migration/01-from-modelcontextprotocol-sdk.md` — Adopting mcp-use v2 from raw SDK
- `references/28-migration/02-v1-to-v2-overview.md` — v1 → v2 Migration Overview
- `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` — Imports, Server, and Tool Registration
- `references/28-migration/04-v1-to-v2-responses-and-helpers.md` — Responses and Deprecated Helpers
- `references/28-migration/05-v1-to-v2-auth.md` — Authentication and OAuth Migration
- `references/28-migration/06-v1-to-v2-widgets-to-views.md` — Widgets to Views: Complete Rewrite
- `references/28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md` — Sessions, Transports, and Stateless Model
- `references/28-migration/08-appssdk-to-mcp-apps.md` — Migrating OpenAI Apps SDK to MCP Apps

## 29-templates

- `references/29-templates/01-overview-and-decision-matrix.md` — Template Overview and Decision Matrix
- `references/29-templates/02-template-mcp-server.md` — Template: mcp-server
- `references/29-templates/03-template-mcp-apps.md` — Template: mcp-apps
- `references/29-templates/04-template-blank-and-manual.md` — Template: blank and Manual HTTP Server

## 30-workflows

- `references/30-workflows/01-greenfield-tool-server-to-vercel.md` — Workflow: Greenfield Tool Server to Vercel
- `references/30-workflows/02-views-app-chart-widget.md` — Workflow: MCP Apps View — Chart Widget
- `references/30-workflows/03-oauth-protected-server-clerk.md` — Workflow: OAuth-Protected Server with Clerk
- `references/30-workflows/04-supabase-oauth-and-deploy.md` — Workflow: Supabase OAuth and Deploy
- `references/30-workflows/05-nextjs-drop-in.md` — Workflow: Next.js Drop-In
- `references/30-workflows/06-openapi-to-mcp.md` — Workflow: OpenAPI to MCP
- `references/30-workflows/07-proxy-gateway.md` — Workflow: Proxy Gateway
- `references/30-workflows/08-elicitation-input-required-flow.md` — Workflow: Elicitation with InputRequired Re-Entry

## 31-canonical-examples

- `references/31-canonical-examples/00-how-to-use-this-cluster.md` — Canonical Examples Cluster
- `references/31-canonical-examples/01-chart-builder.md` — Chart Builder Example
- `references/31-canonical-examples/02-diagram-builder.md` — Diagram Builder Example
- `references/31-canonical-examples/03-example-inventory.md` — Full Example Inventory

## Root hubs

- `references/00-clean-architecture-coordination.md` — Clean Architecture Coordination
- `references/00-reference-index.md` — Reference Index
- `references/00-symptom-index.md` — Symptom Index
- `references/00-version-drift.md` — Version Drift Policy

## Bundled scripts

- `scripts/audit-server-readiness.sh`
- `scripts/audit-server-readiness.sh.md`
- `scripts/check-mcp-use-version.sh`
- `scripts/check-mcp-use-version.sh.md`
- `scripts/scaffold-mcp-use-server.sh`
- `scripts/scaffold-mcp-use-server.sh.md`
