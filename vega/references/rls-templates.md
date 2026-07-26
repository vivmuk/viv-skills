# Supabase RLS Policy Templates

Row Level Security (RLS) is the single most critical security control for Supabase-backed apps. Without RLS, anyone can open browser DevTools and read your entire database. These templates cover the most common table patterns.

## Enabling RLS

```sql
-- Enable RLS on every table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
```

## Pattern 1: User Owns Their Rows (profiles, settings, private data)

```sql
-- Users can only see their own profile
CREATE POLICY "Users can view own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert their own profile
CREATE POLICY "Users can insert own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only update their own profile
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own profile
CREATE POLICY "Users can delete own profile"
  ON public.profiles
  FOR DELETE
  USING (auth.uid() = user_id);
```

## Pattern 2: Public Read, Authenticated Write (blog posts, public content)

```sql
-- Anyone can read published posts
CREATE POLICY "Public can read posts"
  ON public.posts
  FOR SELECT
  USING (published = true);

-- Only authenticated users can create posts
CREATE POLICY "Authenticated users can create posts"
  ON public.posts
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = author_id);

-- Only the author can update their posts
CREATE POLICY "Authors can update own posts"
  ON public.posts
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = author_id);
```

## Pattern 3: Private Read Within a Group (team workspaces, shared resources)

```sql
-- Users can only read rows for teams they belong to
CREATE POLICY "Team members can read"
  ON public.team_resources
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM public.team_members
      WHERE user_id = auth.uid()
    )
  );
```

## Pattern 4: Public Anon Access (waitlists, contact forms)

```sql
-- Anyone (even unauthenticated) can insert into a waitlist
CREATE POLICY "Anyone can join waitlist"
  ON public.waitlist
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- Only authenticated admins can read the waitlist
CREATE POLICY "Admins can read waitlist"
  ON public.waitlist
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE user_id = auth.uid() AND is_admin = true
    )
  );
```

## Testing RLS Policies

Always test that policies actually work. Enabling RLS without testing is worse than not having it because it creates false confidence.

```sql
-- Test as a specific user
SET request.jwt.claim.sub = 'user-uuid-here';
SELECT * FROM public.profiles; -- should only return that user's row

-- Reset
RESET request.jwt.claim.sub;
```

Or use the Supabase dashboard SQL editor with the "Run as authenticated user" option.

## Common RLS Mistakes

1. **Enabling RLS but adding zero policies** — this blocks all access including legitimate access, causing developers to disable RLS in frustration. Always write policies when you enable RLS.
2. **Using `USING (true)` on all policies** — this is equivalent to no RLS at all. Every policy must check `auth.uid()` against a user_id column.
3. **Forgetting INSERT policies** — RLS requires explicit policies for each operation (SELECT, INSERT, UPDATE, DELETE). A SELECT policy does not cover INSERT.
4. **Not testing with different users** — a policy that works for user A might leak data for user B. Test with at least two different user accounts.
5. **Trusting client-side auth state** — RLS checks `auth.uid()` which comes from the JWT. The JWT is verified server-side. Never pass user_id as a parameter and trust it.
