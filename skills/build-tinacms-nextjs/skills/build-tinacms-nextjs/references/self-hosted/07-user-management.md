# User Management (Self-hosted with Auth.js)

The `tinacms-authjs` package validates editors against a user collection in your CMS schema. How to add/remove/manage users.

## The user collection

```typescript
// tina/config.ts schema.collections
{
  name: 'user',
  label: 'Users',
  path: 'content/users',
  format: 'json',
  ui: {
    allowedActions: { create: true, delete: true },
  },
  fields: [
    { name: 'username', type: 'string', isTitle: true, required: true },
    { name: 'email', type: 'string', required: true },
    { name: 'password', type: 'string', ui: { component: 'hidden' } },
    { name: 'role', type: 'string', options: ['admin', 'editor', 'viewer'] },
  ],
}
```

Each user is a JSON file at `content/users/<email>.json`:

```json
{
  "username": "Jane Doe",
  "email": "jane@example.com",
  "password": "$2a$10$xxx...hashed",
  "role": "editor"
}
```

## Hashing passwords

Passwords MUST be bcrypt-hashed before storage. Don't store plaintext.

```typescript
import bcrypt from 'bcryptjs'

const hashed = await bcrypt.hash('plaintext-password', 10)
console.log(hashed)  // $2a$10$xxxxxxx...
```

Store the hash; `tinacms-authjs` validates incoming login attempts via `bcrypt.compare`.

## Adding the first user

For a fresh project, you can't log in (no users exist). Two options:

**Option 1: Direct file edit**

```bash
node -e "
const bcrypt = require('bcryptjs');
const fs = require('fs');
const hash = bcrypt.hashSync('your-password', 10);
fs.writeFileSync('content/users/admin.json', JSON.stringify({
  username: 'Admin',
  email: 'admin@example.com',
  password: hash,
  role: 'admin',
}, null, 2));
"
```

Commit and deploy. Now you can log in.

**Option 2: Setup script**

The official starter includes `pnpm tina:setup`. It prompts for credentials and creates the file.

## Adding more users via admin

Once you have an admin user:

1. Log into `/admin`
2. Open the Users collection
3. Click "Create" — fill in username, email
4. **Set password via a custom mechanism** (the admin form can't hash automatically)

This is a UX gap — `tinacms-authjs` doesn't provide a "create user with password" form. Workarounds:

- Use a custom form on your site (e.g. `/api/admin/create-user` route that hashes + writes)
- Have admins create user files via git directly
- Use the password-reset flow

## Password reset

`tinacms-authjs` supports email-based password reset if you wire up the email-sending. Otherwise, admins reset passwords by directly editing the file (with a new bcrypt hash).

## Removing users

Delete the JSON file:

```bash
rm content/users/jane-doe.json
git add content/users/jane-doe.json && git commit && git push
```

Or via the admin UI (if `delete: true` in `allowedActions`).

## Roles

`tinacms-authjs` doesn't enforce roles — it just validates login. Use the `role` field in your renderers / authorization logic:

```typescript
// In your backend or app code:
if (user.role !== 'admin') {
  return unauthorized()
}
```

For now, role-based access in TinaCMS is DIY. The admin UI shows all users full access regardless.

## OAuth instead of email/password

`tinacms-authjs` supports OAuth providers (GitHub, Google, etc.) too. Configure NextAuth providers:

```typescript
// in your NextAuth config
providers: [
  GitHubProvider({
    clientId: process.env.GITHUB_CLIENT_ID!,
    clientSecret: process.env.GITHUB_CLIENT_SECRET!,
  }),
  // Plus the email/password Credentials provider for fallback
]
```

OAuth users still need a corresponding entry in the `user` collection for authorization (their email matches).

## Multiple identity sources

For complex setups (LDAP, SSO, custom auth), implement a custom auth provider — see `references/self-hosted/auth-provider/05-bring-your-own.md`.

## Audit / who edited what

Git history is the audit log. Each commit is authored by the editor who saved it. For aggregated reports:

```bash
git log --pretty=format:'%an %h %s' content/posts/
```

For UI-based audit, build it yourself by tailing the git log.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Plaintext passwords | Security disaster | Always bcrypt before storage |
| No initial user | Can't log in to bootstrap | Create via script or direct file edit |
| Created user via admin without setting password | Login fails | Set password via separate mechanism |
| Used `username` field for login (instead of `email`) | Auth fails | `tinacms-authjs` uses `email` by default |
| Deleted only admin user | Locked out | Restore from git or create new via direct file edit |
