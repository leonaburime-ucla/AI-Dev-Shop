---
name: supabase
version: 1.0.0
last_updated: 2026-02-23
description: Use when implementing Supabase-specific features including Row Level Security, PostgREST API conventions, realtime subscriptions, storage buckets, edge functions, auth integration, and typed client setup.
---

# Skill: Supabase

Supabase wraps PostgreSQL with a set of platform services: an auto-generated REST and GraphQL API (PostgREST), a realtime engine, object storage, edge functions, and auth. Understanding the interactions between these layers — especially how RLS governs all of them — is what separates a working Supabase implementation from one that silently returns wrong data.

The most important thing to internalize: **RLS is the security layer for everything.** The same policies that govern SQL queries also govern PostgREST API calls and realtime subscriptions. Misconfigured RLS does not throw errors — it silently returns empty result sets or allows unintended access.

## Row Level Security (RLS)

RLS restricts which rows a database role can access. With Supabase, every request from the browser client runs as the `authenticated` or `anon` role. The `service_role` key bypasses RLS entirely — never expose it to the browser.

### Enabling RLS

RLS must be explicitly enabled per table. A table with RLS enabled but no policies returns zero rows to non-superuser roles.

```sql
-- Enable RLS on a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Force RLS even for the table owner (belt-and-suspenders for shared schemas)
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
```

### Writing Policies

A policy has a name, an operation (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, or `ALL`), a role, and a `USING` expression (for row filtering) and/or `WITH CHECK` expression (for row validation on write).

```sql
-- SELECT: users can only read their own orders
CREATE POLICY "users_select_own_orders"
ON orders
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

-- INSERT: users can only insert rows with their own user_id
CREATE POLICY "users_insert_own_orders"
ON orders
FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

-- UPDATE: users can only update their own orders
CREATE POLICY "users_update_own_orders"
ON orders
FOR UPDATE
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- DELETE: users can only delete their own orders
CREATE POLICY "users_delete_own_orders"
ON orders
FOR DELETE
TO authenticated
USING (user_id = auth.uid());

-- Allow public read access for published content
CREATE POLICY "public_select_published_articles"
ON articles
FOR SELECT
TO anon, authenticated
USING (published_at IS NOT NULL AND published_at <= now());
```

**`auth.uid()`**: Returns the UUID of the currently authenticated user from the JWT. Available in any policy or SQL function called during a Supabase request. Returns `NULL` for the `anon` role.

**`USING` vs `WITH CHECK`**:
- `USING` — filters rows when reading (SELECT, UPDATE, DELETE); the expression runs against existing rows
- `WITH CHECK` — validates rows when writing (INSERT, UPDATE); the expression runs against the new row values
- For `UPDATE`, both are typically needed: `USING` to confirm the user can touch the row, `WITH CHECK` to confirm the new values are valid

### Role-Based Policies

For multi-role applications (e.g. `admin`, `member`, `viewer`), store role in a profile table or in a custom JWT claim.

```sql
-- Profile table approach
CREATE TABLE profiles (
    id   uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role text NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer'))
);

-- Policy using a subquery join to profile
CREATE POLICY "admins_select_all_orders"
ON orders
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
          AND profiles.role = 'admin'
    )
);
```

### Policy Testing

Test RLS by impersonating roles within a transaction and verifying query results.

```sql
-- Test that a non-owner cannot see another user's orders
BEGIN;
SET LOCAL role = authenticated;
SET LOCAL request.jwt.claims = '{"sub": "user-b-uuid"}';

-- Should return zero rows (order belongs to user-a)
SELECT * FROM orders WHERE id = 'order-belonging-to-user-a';

ROLLBACK;
```

## PostgREST Conventions

Supabase exposes every table, view, and function via PostgREST automatically. API behavior is driven by naming and schema structure.

### Table and View Naming

Tables exposed as REST endpoints appear at `/rest/v1/<table_name>`. No additional configuration is required.

```sql
-- Table: accessible at GET /rest/v1/orders
CREATE TABLE orders (...);

-- View: accessible at GET /rest/v1/order_summaries
-- RLS on the underlying tables applies to the view
CREATE VIEW order_summaries AS
SELECT o.id, o.status, u.email AS customer_email
FROM orders o
JOIN users u ON u.id = o.user_id;
```

Views do not have their own RLS policies — they inherit the policies of their underlying tables. If the underlying tables have RLS enabled, the view respects those policies.

### Custom Functions as RPC Endpoints

Expose business logic as RPC endpoints with `CREATE FUNCTION`. Called via `POST /rest/v1/rpc/<function_name>`.

```sql
-- Accessible at POST /rest/v1/rpc/get_user_dashboard
CREATE OR REPLACE FUNCTION get_user_dashboard()
RETURNS json
LANGUAGE plpgsql
SECURITY INVOKER  -- runs as the calling user, so RLS applies
STABLE
AS $$
DECLARE
    result json;
BEGIN
    SELECT json_build_object(
        'order_count', COUNT(id),
        'total_spent', SUM(amount)
    )
    INTO result
    FROM orders
    WHERE user_id = auth.uid();

    RETURN result;
END;
$$;
```

**`SECURITY DEFINER` for elevated operations**: Use `SECURITY DEFINER` with care for operations that legitimately need to bypass RLS (e.g. an admin function, a signup trigger). Always validate `auth.uid()` or role inside the function body.

### Filtering and Pagination

PostgREST supports filtering via query parameters. Document the parameters the frontend can use.

```
GET /rest/v1/orders?status=eq.pending&user_id=eq.<uuid>
GET /rest/v1/orders?select=id,amount,status&order=created_at.desc&limit=20&offset=0
```

For cursor-based pagination (preferred over offset for large tables), use `gt` or `lt` operators with the last-seen ID or timestamp.

## Supabase Client Setup

### Installation and Initialization

```bash
npm install @supabase/supabase-js
```

```typescript
// lib/supabase/client.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'  // generated types

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
```

**Environment variables**: Always use `SUPABASE_URL` and `SUPABASE_ANON_KEY` (public, safe in browser). Never expose `SUPABASE_SERVICE_ROLE_KEY` to the browser — it bypasses RLS.

For server-side code that legitimately needs to bypass RLS (admin operations, background jobs):

```typescript
// lib/supabase/server-admin.ts — server-only, never imported in browser code
import { createClient } from '@supabase/supabase-js'

export const supabaseAdmin = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!  // never exposed to browser
)
```

### Type Generation

Generate TypeScript types from the live database schema:

```bash
npx supabase gen types typescript --project-id <your-project-ref> > lib/supabase/database.types.ts
```

Or from a local Supabase instance:

```bash
npx supabase gen types typescript --local > lib/supabase/database.types.ts
```

The generated `Database` type is passed to `createClient<Database>()` to get fully typed query results.

### Querying with the Typed Client

```typescript
// Fully typed — TypeScript infers the return type from the schema
const { data: orders, error } = await supabase
    .from('orders')
    .select('id, amount, status, created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(20)

if (error) throw error
// orders: Array<{ id: string; amount: number; status: string; created_at: string }>
```

## Realtime

Supabase Realtime broadcasts database changes to subscribed clients over WebSockets.

### Enabling Replication

Tables must be added to the realtime publication before changes are broadcast.

```sql
-- Enable replication for specific tables
ALTER PUBLICATION supabase_realtime ADD TABLE orders;
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
```

**RLS and realtime**: Realtime respects RLS. A client subscribed to a table only receives changes for rows it is permitted to read. This means the RLS SELECT policy must cover the rows the client expects to receive as realtime events.

### Subscribing to Changes

```typescript
// Subscribe to all changes on the orders table for the current user
const channel = supabase
    .channel('user-orders')
    .on(
        'postgres_changes',
        {
            event: '*',  // INSERT | UPDATE | DELETE | *
            schema: 'public',
            table: 'orders',
            filter: `user_id=eq.${userId}`
        },
        (payload) => {
            console.log('Change received:', payload)
            // payload.eventType: 'INSERT' | 'UPDATE' | 'DELETE'
            // payload.new: new row data
            // payload.old: old row data (for UPDATE and DELETE)
        }
    )
    .subscribe()

// Unsubscribe when component unmounts
return () => { supabase.removeChannel(channel) }
```

### Presence

Presence tracks which clients are online in a channel — useful for showing active users in collaborative features.

```typescript
const channel = supabase.channel('room-1')

channel
    .on('presence', { event: 'sync' }, () => {
        const state = channel.presenceState()
        console.log('Online users:', state)
    })
    .on('presence', { event: 'join' }, ({ key, newPresences }) => {
        console.log('User joined:', newPresences)
    })
    .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
        console.log('User left:', leftPresences)
    })
    .subscribe(async (status) => {
        if (status === 'SUBSCRIBED') {
            await channel.track({ user_id: userId, online_at: new Date().toISOString() })
        }
    })
```

## Storage

Supabase Storage manages file uploads in buckets, backed by S3-compatible object storage. Access is controlled by storage policies that mirror RLS.

### Creating Buckets

```sql
-- Public bucket: objects accessible without authentication
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true);

-- Private bucket: objects require policy to access
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false);
```

Or via the Supabase CLI in `config.toml`:

```toml
[storage.buckets.avatars]
public = true

[storage.buckets.documents]
public = false
```

### Storage Policies

Storage policies use the same `USING` / `WITH CHECK` syntax as RLS, applied to `storage.objects`.

```sql
-- Users can upload to their own folder in the avatars bucket
CREATE POLICY "users_upload_own_avatar"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Anyone can view avatars (public bucket)
CREATE POLICY "public_read_avatars"
ON storage.objects
FOR SELECT
TO anon, authenticated
USING (bucket_id = 'avatars');

-- Users can delete their own avatar
CREATE POLICY "users_delete_own_avatar"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
);
```

### Upload and Download Patterns

```typescript
// Upload
const { data, error } = await supabase.storage
    .from('avatars')
    .upload(`${userId}/avatar.jpg`, file, {
        contentType: 'image/jpeg',
        upsert: true  // overwrite if exists
    })

// Get public URL (for public buckets)
const { data: { publicUrl } } = supabase.storage
    .from('avatars')
    .getPublicUrl(`${userId}/avatar.jpg`)

// Get signed URL (for private buckets, expires after N seconds)
const { data: { signedUrl } } = await supabase.storage
    .from('documents')
    .createSignedUrl(`${userId}/report.pdf`, 3600)  // 1 hour

// Download
const { data, error } = await supabase.storage
    .from('documents')
    .download(`${userId}/report.pdf`)
```

## Edge Functions

Edge Functions run TypeScript on Deno at the edge. Use them for logic that cannot be expressed in SQL: webhooks from third-party services, complex server-side computations, calling external APIs with secrets, or custom auth flows.

### When to Use Edge Functions vs SQL Functions

| Use Edge Function | Use SQL Function |
|---|---|
| Calling an external API (Stripe, SendGrid, etc.) | Business logic that only touches database data |
| Processing a webhook payload from a third-party | Complex queries that benefit from SQL optimization |
| File processing after upload | RPC endpoints that compose multiple queries |
| Custom auth logic (e.g. enriching JWTs) | Triggers on table changes |

### Basic Structure

```typescript
// supabase/functions/process-payment/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req: Request) => {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        // Access secrets via Deno.env
        const stripeSecretKey = Deno.env.get('STRIPE_SECRET_KEY')!

        // Create a Supabase client with the caller's JWT (respects RLS)
        const authHeader = req.headers.get('Authorization')!
        const supabase = createClient(
            Deno.env.get('SUPABASE_URL')!,
            Deno.env.get('SUPABASE_ANON_KEY')!,
            { global: { headers: { Authorization: authHeader } } }
        )

        const body = await req.json()

        // ... function logic ...

        return new Response(
            JSON.stringify({ success: true }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    } catch (error) {
        return new Response(
            JSON.stringify({ error: error.message }),
            { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    }
})
```

### Secrets

Store secrets in the Supabase dashboard under Project Settings > Edge Functions > Secrets, or via the CLI:

```bash
supabase secrets set STRIPE_SECRET_KEY=sk_live_...
```

Access in the function with `Deno.env.get('STRIPE_SECRET_KEY')`. Never hardcode secrets or commit them to source control.

## Auth Integration

### The `auth.users` Table

Supabase Auth manages users in a `auth.users` table (in the `auth` schema). Do not write to this table directly — use the Auth API.

To store additional user data, create a `profiles` table in the `public` schema with a 1:1 FK to `auth.users`:

```sql
CREATE TABLE profiles (
    id         uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username   text UNIQUE NOT NULL,
    full_name  text,
    avatar_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id, username)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

### The `user_id` FK Pattern

Every table that stores user-owned data should have:

```sql
user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
```

This enforces referential integrity directly against the auth users table. When a user account is deleted, their data cascades automatically.

### Auth Hooks and Custom Claims

For role-based access or organization membership, inject custom claims into the JWT at sign-in using a database hook (available in Supabase Auth Hooks):

```sql
-- Function called by Auth Hook: Custom Access Token Hook
CREATE OR REPLACE FUNCTION custom_access_token_hook(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    claims jsonb;
    user_role text;
BEGIN
    SELECT role INTO user_role FROM profiles WHERE id = (event->>'user_id')::uuid;

    claims := event->'claims';
    claims := jsonb_set(claims, '{user_role}', to_jsonb(COALESCE(user_role, 'member')));

    RETURN jsonb_set(event, '{claims}', claims);
END;
$$;
```

After enabling the hook, `auth.jwt() -> 'user_role'` is available in RLS policies.

## Calling Database Functions via `.rpc()`

```typescript
// Call a SQL function via RPC
const { data, error } = await supabase.rpc('get_user_dashboard')

// With parameters
const { data, error } = await supabase.rpc('search_products', {
    search_query: 'headphones',
    category: 'electronics',
    max_price: 500
})
```

RLS applies to `.rpc()` calls when the function is `SECURITY INVOKER`. If the function is `SECURITY DEFINER`, RLS is bypassed — ensure the function itself enforces authorization via `auth.uid()` checks.

## Type Generation

After any schema change, regenerate types to keep the TypeScript client in sync:

```bash
# Against the remote project
npx supabase gen types typescript --project-id abcdefghijklmnop > lib/supabase/database.types.ts

# Against a local Supabase instance (recommended in development)
npx supabase gen types typescript --local > lib/supabase/database.types.ts
```

Commit the generated types file. CI should fail if a schema change lands without a regenerated types file.

## Common Gotchas

**RLS blocking queries silently**: A table with RLS enabled and no matching SELECT policy returns an empty array — not an error. This is the most common source of "data just isn't showing up" bugs. Always check that a SELECT policy exists for the role that is querying.

**Anon vs service role keys**: The `anon` key (safe for browsers) respects RLS and runs as the `anon` role until the user authenticates. The `service_role` key bypasses RLS entirely — treat it like a root credential. Never use the service role key in client-side code.

**Realtime RLS interaction**: Realtime events are filtered by the RLS SELECT policy of the subscribed table. If a user's permissions change (e.g. they lose access to a row), they will stop receiving realtime updates for that row — but they will not receive a "removed" event. Design UI accordingly.

**Calling `.rpc()` with RLS in SECURITY DEFINER functions**: A `SECURITY DEFINER` function bypasses RLS. If you call such a function via `.rpc()` from the browser, the function runs with the table owner's permissions. Always add explicit `auth.uid()` checks inside `SECURITY DEFINER` functions.

**`updated_at` not auto-updating**: Supabase does not add an `updated_at` trigger automatically. Create an explicit trigger using the `set_updated_at()` pattern (see `sql-data-modeling` skill) on every table that needs it.

**Storage policies are not applied to the bucket — they are applied to `storage.objects`**: A common mistake is thinking "public bucket = no policies needed." A public bucket sets the default visibility of objects, but INSERT, UPDATE, and DELETE still require explicit storage policies. Always define all four operation policies.

**Edge function cold starts**: Edge Functions have a cold start latency (~200-500ms) on first invocation after a period of inactivity. For latency-sensitive endpoints, prefer SQL functions exposed via `.rpc()` over edge functions. Use edge functions for operations that require calling external services or running non-SQL logic.

**PostgREST schema cache**: PostgREST caches the database schema. If you add a new table, view, or function, the auto-generated API will not reflect it until the schema cache is reloaded. In Supabase, this happens automatically every few minutes, or you can trigger it manually from the dashboard under API settings.
