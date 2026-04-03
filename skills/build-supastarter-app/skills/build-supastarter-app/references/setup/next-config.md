# Next.js Configuration

> Annotated breakdown of `apps/web/next.config.ts`. Consult this when adding new plugins, configuring image domains, or debugging build issues.

## Full Configuration

```typescript
// apps/web/next.config.ts
import { withContentCollections } from "@content-collections/next";
import type { NextConfig } from "next";
import { PrismaPlugin } from "@prisma/nextjs-monorepo-helper";
import createNextIntlPlugin from "next-intl/plugin";
import webpack from "webpack";

const withNextIntl = createNextIntlPlugin("./modules/i18n/request.ts");

const nextConfig: NextConfig = {
  // Transpile monorepo packages for Next.js bundling
  transpilePackages: ["@repo/api", "@repo/auth", "@repo/database", "@repo/ui"],

  images: {
    remotePatterns: [
      { hostname: "lh3.googleusercontent.com" },  // Google profile pics
      { hostname: "avatars.githubusercontent.com" }, // GitHub avatars
      { hostname: "picsum.photos" },                // Placeholder images
    ],
  },

  async redirects() {
    return [
      // Settings pages default to "general" tab
      { source: "/app/settings", destination: "/app/settings/general", permanent: false },
      { source: "/app/:orgSlug/settings", destination: "/app/:orgSlug/settings/general", permanent: false },
      // Admin defaults to "users" tab
      { source: "/app/admin", destination: "/app/admin/users", permanent: false },
    ];
  },

  webpack: (config, { isServer }) => {
    // Suppress pg-native and cloudflare:sockets warnings
    config.plugins.push(
      new webpack.IgnorePlugin({
        resourceRegExp: /^pg-native$|^cloudflare:sockets$/,
      })
    );

    // Prisma monorepo helper (server-side only)
    if (isServer) {
      config.plugins.push(new PrismaPlugin());
    }

    return config;
  },
};

// Plugin chain: Content Collections wraps next-intl wraps base config
export default withContentCollections(withNextIntl(nextConfig));
```

## Key Sections

### transpilePackages

These monorepo packages are transpiled by Next.js at build time:

```typescript
transpilePackages: ["@repo/api", "@repo/auth", "@repo/database", "@repo/ui"]
```

If you create a new package that's imported in the web app, add it here.

### Image Remote Patterns

Allow `next/image` to optimize remote images from these hosts:

```typescript
images: {
  remotePatterns: [
    { hostname: "lh3.googleusercontent.com" },   // Google OAuth avatars
    { hostname: "avatars.githubusercontent.com" }, // GitHub OAuth avatars
    { hostname: "picsum.photos" },                 // Dev placeholder images
  ],
}
```

To add a new image source (e.g., your S3 bucket), add its hostname here.

### Redirects

```
/app/settings        → /app/settings/general
/app/:orgSlug/settings → /app/:orgSlug/settings/general
/app/admin           → /app/admin/users
```

These ensure settings and admin pages always land on a specific tab.

### Webpack Customization

Two webpack plugins:
1. **IgnorePlugin** — Suppresses `pg-native` and `cloudflare:sockets` warnings from the Prisma PostgreSQL driver
2. **PrismaPlugin** — Required for Prisma to work correctly in monorepo setups (server-side only)

### Plugin Chain

The config is wrapped by two higher-order functions:

```
withContentCollections(withNextIntl(nextConfig))
```

1. `withNextIntl` — Configures next-intl with the request handler at `./modules/i18n/request.ts`
2. `withContentCollections` — Enables MDX content collections for blog/legal pages

Order matters: Content Collections wraps the outermost layer.

## Adding a New Next.js Plugin

1. Install the plugin package in `apps/web`
2. Import the plugin's wrapper function
3. Add it to the chain: `withNewPlugin(withContentCollections(withNextIntl(nextConfig)))`
4. Configure any needed options in `nextConfig`

---

**Related references:**
- `references/setup/monorepo-structure.md` — Package layout
- `references/i18n/setup.md` — next-intl configuration details
- `references/marketing/content-collections.md` — MDX content setup
- `references/deployment/vercel.md` — Deployment config
