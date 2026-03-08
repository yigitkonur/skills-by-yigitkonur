# Component Patterns

> React component conventions used in the Supastarter codebase. Follow these when creating new components.

## Component Declaration

Always use named exports with the `function` keyword:

```typescript
// ✅ Correct pattern
export function UserCard({ user }: UserCardProps) {
  return <div>{user.name}</div>;
}

// ❌ Wrong — default export
export default function UserCard() {}

// ❌ Wrong — arrow function component
export const UserCard = ({ user }: UserCardProps) => {};

// ❌ Wrong — class component
export default class UserCard extends Component {}
```

## File Structure

Structure component files in this order:

```typescript
// 1. Imports
import { Button } from "@repo/ui/components/button";
import { cn } from "@repo/ui";

// 2. Types/Interfaces
interface UserCardProps {
  user: User;
  className?: string;
}

// 3. Main exported component
export function UserCard({ user, className }: UserCardProps) {
  const isActive = user.status === "active";
  return (
    <div className={cn("rounded-lg border p-4", className)}>
      <UserAvatar user={user} />
      <UserDetails user={user} isActive={isActive} />
    </div>
  );
}

// 4. Sub-components (not exported, only used by main component)
function UserAvatar({ user }: { user: User }) {
  return <img src={user.avatarUrl} alt={user.name} />;
}

function UserDetails({ user, isActive }: { user: User; isActive: boolean }) {
  return (
    <div>
      <p>{user.name}</p>
      {isActive && <span>Active</span>}
    </div>
  );
}
```

## Server vs Client Components

**Default to Server Components.** Only add `"use client"` when required:

```typescript
// Server Component (default) — can fetch data, access DB, etc.
export async function UserProfile({ userId }: { userId: string }) {
  const user = await getUser(userId);
  return <UserCard user={user} />;
}

// Client Component — only when interactivity or browser APIs are needed
"use client";

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Add `"use client"` only for:**
- Components using `useState`, `useEffect`, `useRef`, or other hooks
- Event handlers (`onClick`, `onChange`, `onSubmit`)
- Browser APIs (`window`, `document`, `localStorage`)
- Third-party client libraries

**Never add `"use client"` for:**
- Data fetching (use server components or server actions)
- Layout components
- Static content

## Forms Pattern

Forms use `react-hook-form` + `zod` + Shadcn Form components:

```typescript
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@repo/ui/components/form";
import { Input } from "@repo/ui/components/input";
import { Button } from "@repo/ui/components/button";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
});

type FormValues = z.infer<typeof schema>;

export function NameForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    // Handle submission
  });

  return (
    <Form {...form}>
      <form onSubmit={onSubmit}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl><Input {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

## Conditional Rendering

Use short-circuit evaluation for simple conditions:

```typescript
// ✅ Boolean short-circuit
{isAdmin && <AdminPanel />}
{hasError && <ErrorMessage error={error} />}

// ✅ Ternary for either/or
{isLoading ? <Skeleton /> : <Content data={data} />}

// ❌ Avoid nested ternaries — extract to variables or sub-components
```

## Styling with cn()

Use the `cn()` utility for conditional class names:

```typescript
import { cn } from "@repo/ui";

export function Card({ active, className }: CardProps) {
  return (
    <div className={cn(
      "rounded-lg border p-4",  // Base classes
      active && "border-primary bg-primary/5",  // Conditional
      className,  // Consumer override (always last)
    )}>
      {/* content */}
    </div>
  );
}
```

---

**Related references:**
- `references/conventions/naming.md` — Naming conventions
- `references/ui/forms.md` — Full form pattern reference
- `references/ui/components.md` — Available UI components
