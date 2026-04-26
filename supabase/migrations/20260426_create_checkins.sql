-- Create a simple check-in log table for QR attendance.
-- This migration is optional but recommended for the GitHub Pages + Edge Function demo.

create table if not exists public.checkins (
  id bigint generated always as identity primary key,
  shift_id text not null,
  volunteer_id text not null,
  checked_in_at timestamptz not null default now(),
  source text,
  token_nonce text,
  token_issued_at text,
  token_expires_at text
);

-- For the Edge Function using the Service Role key, RLS is not required.
-- Keep it enabled for safety if you later expose anon-key inserts.
alter table public.checkins enable row level security;

