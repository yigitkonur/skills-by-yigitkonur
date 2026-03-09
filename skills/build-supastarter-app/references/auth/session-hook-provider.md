# Session Hook and Provider

> Documents the `SessionProvider` / `useSession()` pair that exposes authenticated user state to client components. Consult this when a client feature needs the current user, session metadata, or a `reloadSession()` hook after profile updates.

## Key files

- `apps/web/modules/saas/auth/components/SessionProvider.tsx`
- `apps/web/modules/saas/auth/hooks/use-session.ts`
- `apps/web/modules/saas/auth/lib/api.ts`

## Representative code

```ts
export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { data: session } = useSessionQuery();

  return (
    <SessionContext.Provider
      value={{
        session: session?.session ?? null,
        user: session?.user ?? null,
        reloadSession: async () => {
          const { data: newSession } = await authClient.getSession({
            query: { disableCookieCache: true },
          });

          queryClient.setQueryData(sessionQueryKey, () => newSession);
        },
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => {
  const sessionContext = useContext(SessionContext);
  if (sessionContext === undefined) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return sessionContext;
};
```

## Responsibilities

- `SessionProvider` supplies the session context to client components under SaaS and marketing layouts
- `SessionProvider` reads session state through `useSessionQuery()` instead of calling Better Auth directly on every consumer
- `useSession()` exposes `{ user, session, loaded, reloadSession }`
- `reloadSession()` bypasses Better Auth cookie caching and writes the fresh result back into the React Query cache
- Provider misuse fails loudly because the hook throws outside the provider boundary

## Implementation notes

- This hook is intentionally tiny; it only unwraps `SessionContext` and enforces provider presence.
- The provider is the real integration point: it combines `useSessionQuery()`, React Query cache access, and `authClient.getSession({ query: { disableCookieCache: true } })`.
- `reloadSession()` is used after settings changes such as email, name, avatar, or language updates.
- Session context complements the server helpers: layouts fetch auth state on the server, then client components consume the provider.

---

**Related references:**
- `references/auth/server-session-helpers.md` — Server-side counterpart to session access
- `references/auth/client-auth-client.md` — Client auth actions often followed by `reloadSession()`
- `references/hooks/auth-hooks.md` — Broader session/provider patterns
