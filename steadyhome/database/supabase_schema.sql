-- SteadyHome: Supabase schema. Run once in the Supabase SQL editor.
-- The FastAPI backend writes with the service_role key (bypasses RLS); RLS is enabled with
-- no public policies so the anon key can read nothing.

create table if not exists public.escalations (
    escalation_id        text primary key,
    borrower_id          text,
    intent               text not null,
    reason               text not null,
    payment_mode         text,
    conversation_summary text not null,
    transfer_status      text not null default 'INITIATED',
    timestamp            text not null
);

create table if not exists public.interaction_logs (
    id          bigint generated always as identity primary key,
    session_id  text not null,
    borrower_id text,
    event_type  text not null,
    agent_name  text not null,
    details     text not null,
    timestamp   text not null
);
create index if not exists interaction_logs_session_idx on public.interaction_logs (session_id);

create table if not exists public.call_sessions (
    session_id    text primary key,
    borrower_id   text,
    verified      boolean not null default false,
    intent_tag    text,
    is_escalated  boolean not null default false,
    escalation_id text,
    transcript    jsonb not null default '[]'::jsonb,
    tool_logs     jsonb not null default '[]'::jsonb,
    updated_at    timestamptz not null default now()
);

alter table public.escalations      enable row level security;
alter table public.interaction_logs enable row level security;
alter table public.call_sessions    enable row level security;
