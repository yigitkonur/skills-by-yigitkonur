# Example: full Managed Auth flow

End-to-end Hosted UI with the embedded `@onkernel/managed-auth-react` component, a Next.js App Router page, the backend route, and a downstream browser launch.

Stack assumptions: Next.js 14+ App Router, TypeScript, `@onkernel/sdk`, `@onkernel/managed-auth-react`.

## Backend route — start a connection

```ts
// app/api/auth/[...slug]/route.ts
import Kernel from '@onkernel/sdk';
import { NextRequest, NextResponse } from 'next/server';

const kernel = new Kernel();

export async function POST(req: NextRequest) {
  const userId = await getCurrentUserId(req);                 // your session helper

  const conn = await kernel.auth.connections.create({
    domain: 'netflix.com',
    profile_name: `netflix-${userId}`,
    save_credentials: true,
  });

  const { hosted_url } = await kernel.auth.connections.login(conn.id);

  // Parse the handoff: hosted_url ends with `/{conn.id}?code=<handoff>`
  const url = new URL(hosted_url);
  const code = url.searchParams.get('code');

  return NextResponse.json({
    connectionId: conn.id,
    hostedUrl: hosted_url,
    code,
  });
}
```

## Frontend — embed the component

```tsx
// app/connect/page.tsx
'use client';                                              // REQUIRED for the React component

import { useEffect, useState } from 'react';
import { KernelManagedAuth } from '@onkernel/managed-auth-react';
import { useRouter } from 'next/navigation';

export default function ConnectPage() {
  const router = useRouter();
  const [conn, setConn] = useState<{ connectionId: string; code: string } | null>(null);

  useEffect(() => {
    fetch('/api/auth/connect', { method: 'POST' })
      .then(r => r.json())
      .then(setConn);
  }, []);

  if (!conn) return <div>Loading…</div>;

  return (
    <KernelManagedAuth
      sessionId={conn.connectionId}
      handoffCode={conn.code}
      onSuccess={() => router.push('/connected')}
      onError={(err) => console.error(err)}
      appearance={{
        theme: 'light',
        variables: {
          colorPrimary: '#3b82f6',
          colorBackground: '#ffffff',
        },
        layout: {
          poweredByKernel: false,
          showSecurityCard: true,
          socialButtonsPlacement: 'top',
        },
      }}
    />
  );
}
```

Alternative (no embed, just redirect):

```tsx
'use client';
useEffect(() => {
  fetch('/api/auth/connect', { method: 'POST' })
    .then(r => r.json())
    .then(({ hostedUrl }) => { window.location.href = hostedUrl; });
}, []);
```

## Backend — confirm the connection completed

After `onSuccess` (or after the redirect comes back), confirm the state from your backend before launching a browser:

```ts
// app/api/auth/[connectionId]/state/route.ts
import Kernel from '@onkernel/sdk';
import { NextRequest, NextResponse } from 'next/server';

const kernel = new Kernel();

export async function GET(
  req: NextRequest,
  { params }: { params: { connectionId: string } }
) {
  const state = await kernel.auth.connections.retrieve(params.connectionId);
  return NextResponse.json({
    flowStatus: state.flow_status,
    status: state.status,
    needsAuth: state.status !== 'AUTHENTICATED',
  });
}
```

For long polls, prefer `kernel.auth.connections.follow(id)` (SSE) over re-polling `retrieve` from the client.

## Launch a browser with the saved profile

```ts
// app/api/run/route.ts
import Kernel from '@onkernel/sdk';
import { chromium } from 'playwright';

const kernel = new Kernel();

export async function POST() {
  const userId = await getCurrentUserId();

  const session = await kernel.browsers.create({
    stealth: true,
    timeout_seconds: 600,
    // SAME profile name from the connection. Set save_changes: true if you
    // want any new auth state (refreshed cookies, MFA tokens) captured back
    // into the profile when the browser is deleted.
    profile: { name: `netflix-${userId}`, save_changes: true },
  });

  try {
    const browser = await chromium.connectOverCDP(session.cdp_ws_url);
    const page = browser.contexts()[0].pages()[0];
    await page.goto('https://www.netflix.com/browse');     // already authenticated
    const html = await page.content();
    return new Response(html, { headers: { 'Content-Type': 'text/html' } });
  } finally {
    await kernel.browsers.deleteByID(session.session_id);
  }
}
```

## When the session goes stale

If a browser launch shows the login page instead of the authenticated content, the connection's `status` is `NEEDS_AUTH`. Re-run the flow:

```ts
const state = await kernel.auth.connections.retrieve(connectionId);
if (state.status === 'NEEDS_AUTH') {
  await kernel.auth.connections.login(connectionId);
  // redirect or re-mount the React component again
}
```

Most sessions remain valid for days; Kernel auto-refreshes when possible.

## Important caveats

- The React component is a **client component**. Mark the file `'use client'` in App Router; it will not render server-side.
- `auth.connections.create` returns 409 on duplicate `(domain, profile_name)`. Either reuse the existing connection or pick a new `profile_name`.
- The handoff `code` query-param expires quickly. Re-`login` if the user lingers before completing.
- Same-origin proxying via Next rewrites is supported via `baseUrl=""` on the component if you want the iframe to look like your domain.

## Programmatic flow alternative

If you need full UI control instead of embedding, drive the flow yourself — see `references/guides/managed-auth.md` § "Programmatic — your own UI".
