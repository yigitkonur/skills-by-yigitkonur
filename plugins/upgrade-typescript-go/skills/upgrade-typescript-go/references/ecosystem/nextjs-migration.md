# Next.js Fullstack Migration & TypeScript 7.0 Compatibility

## Overview

Next.js (versions 14, 15, 16+) uses a combination of SWC / Turbopack for compilation and TypeScript for type checking and IDE intelligence (via the Next.js TypeScript plugin).

When upgrading to TypeScript 7.0 (Go native):

## Next.js TypeScript Plugin Handling

In `tsconfig.json`, Next.js injects:
```json
{
  "compilerOptions": {
    "plugins": [
      {
        "name": "next"
      }
    ]
  }
}
```

### Key Considerations:
1. **Turbopack & SWC Build Isolation**: Next.js builds rely on Turbopack / SWC to strip types and bundle JavaScript. Next.js does not use `tsc` for bundling. Therefore, the removal of the Strada JS Compiler API does **not** break `next build`.
2. **Type Checking During Build**:
   - `next build` runs type checking using the configured `typescript` binary.
   - With TypeScript 7.0, `next build` invokes the native Go type checker, significantly accelerating build-time static page collection and metadata verification.
3. **App Router Types**:
   - Dynamic route params and layout props (e.g. `params: Promise<{ id: string }>` in Next.js 15+) are verified seamlessly by TS 7.0.

## Next.js Recommended `tsconfig.json`

```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ESNext",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts"
  ],
  "exclude": ["node_modules"]
}
```

## Troubleshooting Next.js Edge Runtime Types

If using Next.js Edge API routes or middleware:
- Ensure `"skipLibCheck": true` is enabled in `tsconfig.json` to avoid conflicts between DOM types and Cloudflare / Edge runtime webworker globals.
