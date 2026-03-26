# Research Summary: develop-macos-liquid-glass

## Search Queries

| # | Tool | Query | Results |
|---|------|-------|---------|
| 1 | skill-dl search | "liquid glass" "swiftui" "macos" "glass effect" "apple design" "translucency" "glassmorphism" --top 100 | 224 matched, 100 shown |
| 2 | skill-dl search | "swiftui" "macos" "appkit" "toolbar" "sidebar" "window" "menu bar" "dock" --top 100 | 437 matched, 100 shown |
| 3 | skill-dl search | "apple" "human interface" "design guidelines" "hig" "macos design" "swift" "ui design" --top 100 | 442 matched, 100 shown |
| 4 | skill-dl search | "swift" "macos app" "cocoa" "nswindow" "swift development" "xcode" "mac app" --top 100 | 218 matched, 100 shown |
| 5 | skill-dl search | "glass" "blur" "vibrancy" "material" "transparency" "visual effect" "nsvisualeffect" --top 100 | 220 matched, 100 shown |
| 6 | internet-researcher | Liquid Glass WWDC25 APIs (macOS focus) | Comprehensive |
| 7 | internet-researcher | macOS Tahoe design patterns + SwiftUI changes | Comprehensive |
| 8 | internet-researcher | SwiftUI macOS best practices | Comprehensive |

## Candidate Selection

### Tier 1 - Direct download and full read (12 skills)

| Skill | Source | Match Count | Rationale |
|-------|--------|-------------|-----------|
| swiftui-liquid-glass | dimillian/skills | 4 | Top match, IceCubes author, clean 3-path workflow |
| liquid-glass-design | bluewaves-creations | 3 | Failed to download (not found) |
| macos-hig-designer | designnotdrum/skills | 3 | macOS-specific HIG + Liquid Glass |
| liquid-glass | rshankras/claude-code-apple-skills | 3 | Most comprehensive single file (801L) |
| axiom-liquid-glass-ref | charleswiltgen/axiom | 2 | Adoption reference + 30-item audit checklist |
| axiom-liquid-glass | charleswiltgen/axiom | 2 | Design principles + troubleshooting |
| swiftui-liquid-glass | openclaw/skills | 2 | Copy of dimillian's skill |
| ios-glass-ui-designer | heyman333/atelier-ui | 3 | iOS glass design philosophy |
| ios-26-platform | johnrogers/claude-swift-engineering | 2 | iOS 26 platform reference with ref loading |
| macos-app-design | petekp/agent-skills | 4 | Mac Citizen Checklist, app archetypes |
| swiftui-expert-skill | avdlee/swiftui-agent-skill | 3 | Antoine van der Lee's comprehensive SwiftUI |
| axiom-swiftui-26-ref | charleswiltgen/axiom | 2 | iOS 26/SwiftUI 26 feature reference |

### Tier 2 - macOS specific (8 skills)

| Skill | Source | Rationale |
|-------|--------|-----------|
| macos | fusengine/agents | macOS platform skill with MCP tools |
| appkit-swiftui-bridge | rshankras | Failed (not found) |
| macos | rshankras | Modular macOS dev with sub-references |
| macos-capabilities | rshankras | Failed (not found) |
| settings-screen | rshankras | Settings screen generator |
| toolbars | rshankras | Modern toolbar patterns |
| build-macos-apps | mosif16/codex-skills | Full lifecycle macOS dev |
| macos-swiftui | fumiya-kume | macOS SwiftUI patterns (Sonoma+) |

### Tier 3 - SwiftUI + HIG (15+ skills)

Downloaded and read: swiftui-ui-patterns, swiftui-performance-audit, axiom-hig-ref, swiftui-expert-skill (third774), swiftui-forms, swiftui-architecture, swift-navigation, macos-developer-skill, swift-best-practices, macos-mapkit, ios-ux-design, swiftui-multiplatform-design-guide, swift-macos, swiftui-style-driven-components, ios-hig-design, ios-hig-reference, ios-hig (multiple sources), swift-human-guidelines, and more.

## Downloaded Corpus Tree

```
/tmp/lg-corpus/
├── dimillian--skills--swiftui-liquid-glass/
├── rshankras--claude-code-apple-skills--liquid-glass/
├── charleswiltgen--axiom--axiom-liquid-glass-ref/
├── charleswiltgen--axiom--axiom-liquid-glass/
├── charleswiltgen--axiom--axiom-swiftui-26-ref/
├── charleswiltgen--axiom--axiom-hig-ref/
├── openclaw--skills--swiftui-liquid-glass/
├── heyman333--atelier-ui--ios-glass-ui-designer/
├── johnrogers--claude-swift-engineering--ios-26-platform/
├── designnotdrum--skills--macos-hig-designer/
├── fusengine--agents--macos/
├── petekp--agent-skills--macos-app-design/
├── petekp--claude-code-setup--macos-app-design/
├── rshankras--claude-code-apple-skills--macos/
├── rshankras--claude-code-apple-skills--settings-screen/
├── rshankras--claude-code-apple-skills--toolbars/
├── mosif16--codex-skills--build-macos-apps/
├── dimillian--skills--swiftui-ui-patterns/
├── dimillian--skills--swiftui-performance-audit/
├── avdlee--swiftui-agent-skill--swiftui-expert-skill/
├── third774--dotfiles--swiftui-expert-skill/
├── fumiya-kume--toy-poodle-love--macos-swiftui/
├── wshobson--agents--mobile-ios-design/
├── jamesrochabrun--skills--apple-hig-designer/
├── wondelai--skills--ios-hig-design/
├── heyman333--atelier-ui--apple-ui-designer/
├── beshkenadze--claude-skills-marketplace--ios-hig-reference/
├── johnrogers--claude-swift-engineering--ios-hig/
├── pproenca--dot-skills--ios-hig/
├── frostist--swift-human-guidelines--swift-human-guidelines/
├── kaakati--rails-enterprise-dev--swiftui-patterns/
├── kaakati--rails-enterprise-dev--navigation-patterns/
├── johnrogers--claude-swift-engineering--swiftui-advanced/
├── johnrogers--claude-swift-engineering--swiftui-patterns/
├── mintuz--claude-plugins--swiftui-architecture/
├── arjenschwarz--agentic-coding--swiftui-forms/
├── beshkenadze--claude-skills-marketplace--swiftui-developer/
├── nonameplum--agent-skills--swift-navigation/
├── 404kidwiz--claude-supercode-skills--macos-developer-skill/
├── rshankras--claude-code-apple-skills--design/
├── mosif16--codex-skills--ios-ux-design/
├── mosif16--codex-skills--swiftui-multiplatform-design-guide/
├── pluginagentmarketplace--custom-plugin-swift--swift-macos/
├── rshankras--claude-code-apple-skills--feature-flags/
├── rshankras--claude-code-apple-skills--text-editing/
├── fusengine--agents--swiftui-core/
├── openclaw--skills--distinctive-design-systems/
├── dasien--claudemultiagenttemplate--desktop-ui-design/
├── fumiya-kume--toy-poodle-love--macos-mapkit/
├── sammcj--agentic-coding--swift-best-practices/
├── hmohamed01--swift-development--swift-development/
├── cacr92--wereply--macos-agent-development/
├── jamesrochabrun--skills--releasing-macos-apps/
├── kylehughes--apple-platform-build-tools-claude-code-plugin/
├── openclaw--skills--macos-spm-app-packaging/
├── jamesrochabrun--skills--swiftui-animation/
├── williamzujkowski--standards--swift/
├── a5c-ai--babysitter--appkit-menu-bar-builder/
├── avdlee--swiftui-agent-skill--update-swiftui-apis/
├── ahmadbrkt--swiftui-style-driven-components-skill/
├── beshkenadze--claude-skills-marketplace--ios-swiftui-generator/
├── mosif16--codex-skills--xcode-shared-swiftui-workflow/
├── nonameplum--agent-skills--programming-swift/
├── nonameplum--agent-skills--swift-observation/
└── petekp--claude-code-setup--swiftui/
```

Plus direct clone: `/tmp/liquid-glass-research/plugins/liquid-glass/` (haider-nawaz)

**Total: 65+ skills downloaded and read across 8 parallel batch agents**

## Next: Compare the downloaded corpus before drafting

See comparison table in the approved plan file at:
`/Users/yigitkonur/.claude/plans/abstract-whistling-flute.md`
