# Design Token Formats & Specifications

Reference for structuring extracted design tokens in standard formats.

---

## W3C Design Tokens Format (DTCG)

The W3C Design Tokens Community Group defines a standard JSON format for design tokens. File extension: `.tokens` or `.tokens.json`. MIME type: `application/design-tokens+json`.

### Core Structure

```json
{
  "color": {
    "$type": "color",
    "brand": {
      "primary": {
        "$value": "#007acc",
        "$description": "Primary brand color for CTAs and active states"
      },
      "secondary": {
        "$value": "#6c757d",
        "$description": "Secondary actions and muted elements"
      }
    },
    "semantic": {
      "background": {
        "default": {
          "$value": "{color.base.white}",
          "$description": "Page canvas background"
        },
        "muted": {
          "$value": "{color.base.gray.100}",
          "$description": "Muted surface for cards and panels"
        }
      }
    }
  },
  "spacing": {
    "$type": "dimension",
    "xs": { "$value": "4px" },
    "sm": { "$value": "8px" },
    "md": { "$value": "16px" },
    "lg": { "$value": "24px" },
    "xl": { "$value": "32px" }
  }
}
```

### Token Object Properties

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `$value` | Yes | varies | The token value (color, dimension, etc.) |
| `$type` | No | string | Token type (inherited from parent group) |
| `$description` | No | string | Human-readable description |
| `$extensions` | No | object | Vendor-specific metadata |
| `$deprecated` | No | bool/string | Marks token as deprecated |

### Supported Types

| Type | Example $value | Use Case |
|------|----------------|----------|
| `color` | `"#ff0000"`, `"hsl(0 100% 50%)"` | Colors |
| `dimension` | `"16px"`, `"1rem"` | Spacing, sizing, radius |
| `fontFamily` | `"Inter, sans-serif"` | Font stacks |
| `fontWeight` | `500`, `"medium"` | Font weights |
| `duration` | `"150ms"` | Animation timing |
| `cubicBezier` | `[0.4, 0, 0.2, 1]` | Easing curves |
| `shadow` | `{ color, offsetX, offsetY, blur, spread }` | Box shadows |
| `number` | `0.5` | Opacity, ratios |
| `string` | `"solid"` | Border style |

### References (Aliases)

Tokens can reference other tokens using curly-brace syntax:

```json
{
  "color": {
    "base": {
      "blue-500": { "$value": "#3b82f6", "$type": "color" }
    },
    "semantic": {
      "primary": { "$value": "{color.base.blue-500}" }
    },
    "component": {
      "button-bg": { "$value": "{color.semantic.primary}" }
    }
  }
}
```

### Naming Rules

- Names are **case-sensitive**
- Must NOT start with `$`
- Must NOT contain `{`, `}`, or `.`
- Must be unique within their group

---

## Token Hierarchy

### Three-Tier Architecture

```
┌─────────────────────────────────────────────┐
│  Component Tokens (most specific)           │
│  button.primary.background                  │
│  input.border.default                       │
│  card.background                            │
├─────────────────────────────────────────────┤
│  Semantic Tokens (context-aware)            │
│  color.background.default                   │
│  color.interactive.primary                  │
│  spacing.content.padding                    │
├─────────────────────────────────────────────┤
│  Primitive Tokens (raw values)              │
│  color.base.blue.500 = #3b82f6             │
│  spacing.base.4 = 16px                     │
│  font.size.base = 16px                     │
└─────────────────────────────────────────────┘
```

### Tier Breakdown

| Tier | What It Contains | Example | Who Uses It |
|------|-----------------|---------|-------------|
| Primitive | Raw, unaliased values | `gray.100: #f5f5f5` | Semantic tokens reference these |
| Semantic | Context-aware aliases | `background.default: {gray.100}` | Component tokens reference these |
| Component | Component-specific aliases | `card.bg: {background.default}` | Developers use these directly |

### Why Three Tiers?

1. **Theme switching**: Change primitives → semantics update automatically → all components update
2. **Dark mode**: Same semantic names, different primitive references
3. **White-labeling**: Swap the primitive tier, everything else follows

---

## CSS Custom Properties Format

The most common token format in web codebases:

```css
:root {
  /* Primitives */
  --color-blue-500: #3b82f6;
  --color-gray-100: #f5f5f5;

  /* Semantic */
  --background: var(--color-gray-100);
  --foreground: var(--color-gray-900);
  --primary: var(--color-blue-500);

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;

  /* Radius */
  --radius: 0.625rem;
}

.dark {
  --background: var(--color-gray-950);
  --foreground: var(--color-gray-50);
}
```

---

## Tailwind CSS Token Format

Tokens defined in `tailwind.config.ts`:

```typescript
export default {
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      spacing: {
        // Usually uses Tailwind defaults (4px base)
      },
    },
  },
}
```

---

## Style Dictionary Format

For cross-platform token transformation:

```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "build/css/",
      "files": [{
        "destination": "variables.css",
        "format": "css/variables"
      }]
    },
    "json": {
      "transformGroup": "json",
      "buildPath": "build/json/",
      "files": [{
        "destination": "tokens.json",
        "format": "json/flat"
      }]
    }
  }
}
```

### CTI Naming Convention

Style Dictionary uses Category-Type-Item (CTI) naming:

| Category | Type | Item | Full Path | CSS Output |
|----------|------|------|-----------|------------|
| color | background | default | color.background.default | --color-background-default |
| color | brand | primary | color.brand.primary | --color-brand-primary |
| spacing | size | md | spacing.size.md | --spacing-size-md |
| font | size | base | font.size.base | --font-size-base |

---

## Choosing a Format for Extraction Output

| Situation | Recommended Format | Why |
|-----------|-------------------|-----|
| Web-only, Tailwind | CSS Custom Properties | Native, no build step needed |
| Multi-platform | W3C DTCG JSON | Standard, tool-agnostic |
| Existing Style Dictionary | Style Dictionary JSON | Compatible with existing pipeline |
| Documentation-only | Markdown tables | Human-readable, no tooling needed |

For design extraction (this skill's output), use **Markdown tables** as the primary format with **CSS recreation blocks** as the implementable format. The extracted tokens ARE the documentation.

---

## Output Checklist

- [ ] Token format identified in the target codebase
- [ ] All tokens organized by hierarchy tier (primitive → semantic → component)
- [ ] References/aliases documented with resolution chain
- [ ] Dark mode token overrides documented
- [ ] Token naming convention identified (kebab-case, camelCase, CTI)
