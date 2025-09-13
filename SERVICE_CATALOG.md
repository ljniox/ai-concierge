# Service Catalog & Orchestration – Implementation Notes

This document summarizes the work implemented to add a Service Catalog, session routing, Supabase persistence, and IA orchestration to the WhatsApp auto‑reply system.

## Overview
- New entry experience: gust‑ai sends a welcome message and proposes a service catalog on first contact or on greeting (bonjour/hello/salut/menu/help…).
- Service selection launches a guided session powered by Claude (Anthropic), with persisted context and interaction history in Supabase.
- “Parler directement à James” option is always available; if chosen outside 07:00–23:00 (Africa/Dakar), gust‑ai returns: “James est indisponible pour le moment, mais il repondra des que possible”.
- Legacy auto‑reply is disabled (AUTO_REPLY_ENABLED=false) to prioritize the new catalog flow.

## Key Changes
- Webhook routing now uses a Session Manager to always respond with a welcome + menu on greetings/first message.
- Supabase is the single source of truth for: services (catalog), sessions, interactions (with embeddings), and artifacts (reports).
- Anthropic GLM used for embeddings and Claude used for orchestrated replies (lazy imports to avoid hard failures).
- WAHA sending consolidated via `wa_service.py` with explicit logs for each outgoing message.
- Timezone set to Africa/Dakar for human‑handoff availability checks.

## Components Added
- `supabase_schema.sql` – DDL for tables: `services`, `sessions`, `interactions`, `artifacts` (plus extensions and indexes).
- `supabase_client.py` – Minimal REST client (service role) for CRUD.
- `catalog_repository.py` – Lists services, builds menu, matches selection (numero/mot‑clé).
- `session_manager.py` – State machine: awaiting_selection → in_service → human_handoff; welcome/menu logic; James option + hours gating.
- `orchestrator.py` – Claude‑based reply generator, first flow for “Catéchèse St Jean Bosco Dakar – infos”, saves artifact report.
- `embeddings.py` – Embeddings via GLM (/embeddings) with fallback via Claude Messages (JSON array of floats), stored as JSON.
- `wa_service.py` – WAHA `sendText` wrapper with logs.
- `seed_supabase_services.py` – One‑shot seed for initial service.
- `version_info.py` – `/version` endpoint data.

## Runtime Behavior
- First message or greeting (bonjour/bonsoir/salut/hello/hi/hey/coucou/menu/help/start):
  - gust‑ai sends: “Je suis gust‑ai, assistant virtuel de James. Que voulez‑vous faire ?”
  - then enumerates catalog options from Supabase + “Parler directement à James”.
- Selection:
  - Numeric (1..N) or keyword → resolves to `service_code`.
  - For “HUMAIN_JAMES”: if time ∉ [07:00,23:00), send unavailability message; else handoff message.
  - For services: session status becomes `in_service`; orchestrator processes messages and produces a useful output (message/report).
- Persistence:
  - Each user/assistant message logged in `interactions` with optional embeddings.
  - Final outputs saved in `artifacts` as type `report`.

## Supabase Data Model (summary)
- `services(code pk, title, description, keywords[], enabled, display_options, flow jsonb, created_at, updated_at)`
- `sessions(id uuid pk, phone, status, service_code fk, context jsonb, started_at, ended_at, last_message_at)`
- `interactions(id uuid pk, session_id fk, ts, role, content, meta jsonb, embedding_json jsonb)`
- `artifacts(id uuid pk, session_id fk, service_code, type, content, meta jsonb, created_at)`
- Extensions: `pgcrypto` for UUID, `vector` enabled for future vector column (currently JSON storage).

## Endpoints & Logs
- `GET /version` – returns { app, version, git_sha, build_time, tz, supabase_services_count }.
- Webhook logs:
  - Incoming: “Incoming message from <phone>: <text>”
  - Outgoing: “Sending reply to <phone>: …” and “WA send ok -> <phone>: …”

## Environment Variables
- WhatsApp (WAHA): `WAHA_API_KEY`, `WAHA_BASE_URL`, `SESSION_NAME`
- Supabase: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- Anthropic GLM: `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`, `ANTHROPIC_AUTH_TOKEN=...`
- Orchestrator models (optional): `ANTHROPIC_MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`
- Legacy auto‑reply: `AUTO_REPLY_ENABLED=false`
- Timezone: `TZ=Africa/Dakar` (Docker Compose + tzdata in image)

## Deployment Steps (Coolify)
1) Set env vars above (ensure Supabase + Anthropic keys are present).
2) Ensure Supabase schema is applied (run `supabase_schema.sql` in SQL Editor).
3) Seed catalog (once): POST to `/rest/v1/services?on_conflict=code` with JSON from `seed_supabase_services.py` or run the script.
4) Clear build cache and Redeploy.
5) Validate:
   - `GET /version` (tz, services count)
   - WhatsApp: send “menu” or “bonjour” → expect welcome + options.

## Testing
- Greeting flow: send “hello/bonjour/menu” → welcome + menu.
- Select service “Catéchèse St Jean Bosco Dakar”: expect info response; check `artifacts`.
- Human handoff: choose “Parler directement à James”
  - 07:00–23:00 → “mise en relation”
  - otherwise → unavailability message.

## Troubleshooting
- No reaction: check `/version`, ensure `supabase_services_count ≥ 0`, and webhook logs show “Sending reply …”. If not, rebuild without cache.
- Legacy auto‑reply messages seen: set `AUTO_REPLY_ENABLED=false` and toggle via `/auto-reply/toggle`.
- Supabase errors: verify URL/key, tables exist; fallback will still show menu statelessly.

## Security Notes
- Only server‑side service role key used; do not expose on client.
- Avoid logging PII; logs are already concise and truncated.
- HTTPS for WAHA and public endpoints.

## Next Steps
- Add more services (RDV, Devis, Support) to the catalog.
- Enable vector column + similarity search in `interactions` (replace JSON with pgvector).
- Add tool‑calls in orchestrator (calendar, CRM, documents).
- Add `/sessions/:id` and minimal admin dashboard for monitoring.

