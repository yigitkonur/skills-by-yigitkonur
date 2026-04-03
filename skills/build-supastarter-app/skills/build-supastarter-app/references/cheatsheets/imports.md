# Common Imports Cheatsheet

> Most frequently used imports from each package, organized for quick reference.

## @repo/auth

```typescript
import { auth } from "@repo/auth";
import type { Session, ActiveOrganization, Organization } from "@repo/auth";
import type { OrganizationMemberRole } from "@repo/auth";
```

## @repo/database

```typescript
import { db } from "@repo/database";
// Import generated types from Prisma
import type { User, Organization, Purchase } from "@repo/database";
```

## @repo/api (procedures)

> ⚠️ **Steering:** Only three procedure tiers exist. Do not try to use `organizationProcedure` — it does not exist.

```typescript
import { publicProcedure, protectedProcedure, adminProcedure } from "../../../orpc/procedures";
import { ORPCError } from "@orpc/server";
import { z } from "zod";
```

## @repo/ui

```typescript
// Utility
import { cn } from "@repo/ui";

// Components (always deep import)
import { Button } from "@repo/ui/components/button";
import { Input } from "@repo/ui/components/input";
import { Label } from "@repo/ui/components/label";
import { Card, CardContent, CardHeader, CardTitle } from "@repo/ui/components/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@repo/ui/components/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@repo/ui/components/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@repo/ui/components/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@repo/ui/components/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@repo/ui/components/tabs";
import { Badge } from "@repo/ui/components/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@repo/ui/components/avatar";
import { Skeleton } from "@repo/ui/components/skeleton";
import { toast } from "sonner";
```

## @shared/ (web app shared modules)

```typescript
import { orpcClient } from "@shared/lib/orpc-client";
import { orpc } from "@shared/lib/orpc-query-utils";
```

## @saas/ (SaaS feature modules)

```typescript
import { getSession, getActiveOrganization } from "@saas/auth/lib/server";
import { useSession } from "@saas/auth/hooks/use-session";
import { useActiveOrganization } from "@saas/organizations/hooks/use-active-organization";
```

## @repo/payments

```typescript
import { config as paymentsConfig } from "@repo/payments/config";
import type { PaymentProvider, CreateCheckoutLink } from "@repo/payments/types";
```

## @repo/mail

```typescript
import { sendEmail } from "@repo/mail";
```

## @repo/i18n

```typescript
import { config as i18nConfig } from "@repo/i18n/config";
import { useTranslations } from "next-intl";
```

## @repo/logs

```typescript
import { logger } from "@repo/logs";
```

## @repo/utils

```typescript
import { getBaseUrl } from "@repo/utils";
```

## @repo/storage

```typescript
import { getSignedUrl, getSignedUploadUrl } from "@repo/storage";
```

## Next.js

```typescript
import { redirect, notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import dynamic from "next/dynamic";
```

## React / TanStack Query

```typescript
import { Suspense } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
```

## Forms

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
```

## Common oRPC + toast pattern

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { orpc } from "@shared/lib/orpc-query-utils";
import { toast } from "sonner";
```

---

**Related references:**
- `references/setup/import-conventions.md` — Import rules and path aliases
- `references/cheatsheets/file-locations.md` — Where to put new files
