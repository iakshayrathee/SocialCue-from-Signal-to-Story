# Build Prompt — SocialCue MVP

You are building an **AI-native social media automation MVP for a D2C brand**. Build a **working, single-service, runnable** product. Optimize for: reliable first-run, clean typed code, and a demo that shows *decisioning*, not just generation. Do NOT over-build. Follow this spec exactly; ask me only if something blocks you.

## Product (one line)
**SocialCue** — an AI content strategist for a D2C brand that *decides what to post and why* (grounded in the brand's own past-post performance), then generates platform-specific drafts for approval, schedules them on a week calendar, and learns from mock results.

**Core principle:** This is a **decision engine**, not a caption generator. The LLM *proposes* content opportunities; deterministic Python *ranks* them with an explainable score ("AI proposes, code disposes"). Generation is a downstream action.

## Tech stack (do not deviate)
- **Backend:** FastAPI (Python 3.11+) + Pydantic v2 + Uvicorn.
- **AI orchestration:** LangGraph state graph using OpenAI via `langchain-openai`. All LLM I/O uses Pydantic-structured outputs.
- **Frontend:** React + Vite + TypeScript + TailwindCSS (a small, clean SPA). Build to static assets.
- **Single service:** FastAPI serves the built React app from `/` (StaticFiles) and exposes JSON at `/api/*`. **No second server, no CORS, one deploy, one URL.**
- **Packaging:** one `Dockerfile` (multi-stage: build React → copy into Python image) + `docker-compose.yml`. Also a `Makefile`/README with plain local run steps.
- **Config:** `.env` with `OPENAI_API_KEY` and `MOCK_MODE`.

## Critical requirement: MOCK_MODE
`MOCK_MODE=true` (default) makes every LLM node return realistic pre-baked outputs so the app runs end-to-end with **zero API key and zero cost**. `MOCK_MODE=false` uses real OpenAI. Anyone must be able to `docker compose up` and use the whole flow with no key. This is non-negotiable.

## Anti-hallucination (critical — never fabricate metrics)
- All performance numbers are **computed in Python from the seed data** and passed into prompts as facts. The LLM must only reference provided numbers; never invent metrics.
- Every recommendation's rationale carries **provenance**: the ids of the past posts / the exact stats that justify it, surfaced in the UI as a small "why" detail.

## Seed / mock data (create realistic sample data)
A fictional D2C brand (e.g., a sustainable skincare brand "Lumen"). Provide JSON files:
- `brand.json`: name, description, tone_of_voice (3–5 adjectives + do/don't notes), target_audience segments (2–3, each with name + description + size proxy).
- `products.json`: 4–6 products (name, description, key benefits, price, tags).
- `past_posts.json`: 12–20 past posts, each: id, platform (instagram/tiktok/…), format (reel/carousel/static/story), theme/angle, objective (Discovery|Trust|Conversion), caption, posted_at (day+time), and metrics: reach, engagement_rate, saves, ctr, revenue_attributed. Make some clear winners and losers, and encode a couple of patterns (e.g., short-form video + "behind-the-scenes" over-performs; posting Thu evening beats Mon morning) so the engine has something real to discover.

## AI architecture — LangGraph state graph
State (Pydantic/TypedDict): `brand, products, past_posts, metrics_rollup, insights, opportunities, selected_id, draft, weights, feedback_log`.

Nodes:
1. `extract_insights` — deterministic metric rollups (best formats, best themes, best day/time buckets, top posts per objective/platform) + a short LLM synthesis referencing ONLY those computed numbers.
2. `generate_opportunities` — LLM (Pydantic-structured) proposes 6–10 opportunities. Each: `{title, angle, audience_segment, platform, objective (Discovery|Trust|Conversion), format, rationale, source_post_ids}`. Include at least one **"Amplify a proven winner"** type (repurpose a top past post).
3. `score_and_rank` — **PURE PYTHON, no LLM.** Score each opportunity and sort desc. Return score + per-factor breakdown for transparency:
   ```
   score = w_perf*PerformanceFit      # similarity to past winners (theme/format/objective match to top performers)
         + w_reach*AudienceReach      # segment size proxy × platform fit
         + w_obj*ObjectiveValue       # business weight per Discovery/Trust/Conversion
         + w_fmt*FormatFit            # bias toward short-form vertical video
         + w_nov*Novelty              # penalize repeating very recent themes
         - w_eff*EffortCost           # format production cost
   ```
   Weights come from `state.weights` (defaults provided, tunable via API/UI).
4. `generate_content` — for `selected_id`: retrieve top-3 relevant high-performing past posts as exemplars (simple relevance match is fine, no heavy vector DB needed), then LLM generates platform-specific output: `{caption, hooks[], hashtags[], cta, image_prompt}` grounded in exemplars + brand tone.
5. `guardrail_check` — LLM self-critique vs brand tone rules; if it fails, retry once, then fall back to a deterministic template. Never crash on bad/malformed JSON (validate with Pydantic, retry once, fallback).
6. `log_feedback` — record a mock "published result" and nudge `state.weights` (e.g., if a Conversion post did well, bump w_obj for Conversion slightly). This edge feeds back into future `score_and_rank` runs — the self-improving loop.

Human-in-the-loop: keep the backend simple/stateless across HTTP calls — the frontend holds the plan/selection and calls endpoints in sequence. (Use LangGraph to compose the pipeline; you don't need distributed checkpointing for the MVP.)

## API (FastAPI)
- `POST /api/plan` → runs insights → opportunities → score_and_rank; returns ranked opportunities with score breakdown + provenance + recommended publish time.
- `POST /api/generate` (body: opportunity) → grounded draft + exemplars used.
- `POST /api/approve` (body: draft + slot) → adds to calendar (in-memory store is fine).
- `GET /api/calendar` → approved posts for the week view.
- `POST /api/feedback` (body: post id + mock outcome) → logs result, returns updated weights.
- `GET /api/weights` / `PUT /api/weights` → view/tune scoring weights.
- `GET /api/health` → ok.

## Frontend (React + Vite + Tailwind) — marketer-first, non-technical
- **One primary action: "Plan my week."** Calls `/api/plan`, shows ranked **opportunity cards**.
- Each card (plain English, card layout — NOT a table): title · **"Why now"** rationale with a small expandable proof/provenance detail (the past posts/stats behind it) · target audience · platform · recommended time · objective badge (Discovery/Trust/Conversion) · a confidence/score chip · **"Draft this"** button.
- Draft view: generated caption + hooks + hashtags + CTA + image prompt (show the image_prompt as text; optionally one generated image if key present), inline-editable, **"Approve & schedule."**
- **Week calendar**: simple 7-day view showing approved posts at their recommended times.
- **Feedback moment**: a "Mark published (simulate result)" action that shows weights nudging — this is the demo's wow beat; make it visible.
- Advanced drawer: view/tune scoring weights (hidden by default so marketers aren't overwhelmed).
- Clean, modern, consumer-grade styling with Tailwind — good spacing, hierarchy, rounded cards, subtle shadows. It should NOT look like an internal dashboard.

## Quality bar
- Type everything: Pydantic models on the API boundary; TS types on the client (mirror the API responses).
- Clean module separation: `backend/app/{main.py, schemas.py, scoring.py, rag.py, data/*.json, graph/{state.py,nodes.py,build.py}}`, `frontend/src/...`, `evals/run.py`.
- **`evals/run.py`**: ~5 golden checks — opportunities match schema, rationales reference only real metric values, generated captions respect platform length limits, and a basic voice-similarity/keyword check against exemplars. Print a pass/fail summary.
- Robustness: malformed LLM JSON never crashes the app (validate → retry once → deterministic fallback).

## Deliverables
- Runnable repo, single `docker compose up` → open one URL → full flow works in MOCK_MODE with no key.
- `README.md` with: the problem, product decisions, how AI is used (with the LangGraph diagram), what's next, run instructions (MOCK and live), and the AI coding tools used. Explicitly state the scope trade-offs (what's out: real publishing, auth, heavy vector DB).
- Keep it small and sharp. A working core loop beats extra features.

## Build order (do this in sequence; pause at each checkpoint for my review)
1. **Scaffold** repo structure + seed JSON data + Pydantic schemas + FastAPI skeleton with `/api/health`. Checkpoint.
2. **The brain:** `extract_insights` + `generate_opportunities` + `score_and_rank` (with MOCK_MODE), wire `POST /api/plan`. Show me real ranked JSON output. Checkpoint.
3. **Generation + guardrail:** `generate_content` grounded in exemplars, `POST /api/generate`. Checkpoint.
4. **Frontend:** Plan → cards → draft → approve → calendar. Checkpoint.
5. **Feedback loop** (`log_feedback` + weights nudge + UI moment) + `evals/run.py`. Checkpoint.
6. **Package:** Dockerfile + compose + README + verify one-command run in MOCK_MODE. Final checkpoint.

Start with step 1. Confirm the structure and seed data with me before moving on.

---
### (Optional) If I switch the frontend to Streamlit instead
Replace the React/Vite frontend + StaticFiles with a single `streamlit_app.py` that calls the same FastAPI `/api/*` endpoints (or imports the graph directly). Keep everything else identical. Use `st.container(border=True)` cards (not `st.dataframe`), hide the default menu/footer, and add minimal custom CSS so it reads as a product. Note the trade-off in the README.
