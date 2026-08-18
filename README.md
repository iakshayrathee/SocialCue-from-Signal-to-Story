# SocialCue — from *Signal* to *Story*

**An AI content strategist for D2C brands that decides *what to post and why* — grounded in the brand's own past-post performance — then drafts it, schedules it, and learns from results.**

> **This is not a caption generator. It's a decision engine.** The LLM *proposes* content
> opportunities; deterministic Python *ranks* them with an explainable, auditable score.
> Generation is a downstream action. **AI proposes, code disposes.**

One command, one URL, zero API key required:

```bash
docker compose up --build   # then open http://localhost:8000
```

---

## The problem

D2C teams don't struggle to *write* a caption — that's commoditized. They struggle to decide
**what is worth posting, for whom, and when**, and today those decisions are disconnected from the
data that should inform them (product catalog, audience, past performance). Content gets made on gut
feel and nobody links the decision to the outcome.

SocialCue closes that loop: it reads the brand's own performance, ranks the highest-value content
opportunities with a plain-English "why now" backed by real numbers, generates a grounded draft on
approval, schedules it, and nudges its own strategy when a post performs.

## Product decisions

- **Decision-first, generation-second.** The hero is a ranked list of *opportunities*, each with a
  data-backed rationale. Generation happens only after a decision is made.
- **DTC-native objectives.** Every opportunity serves **Discovery, Trust, or Conversion** — how a D2C
  marketer actually thinks — not abstract funnel jargon.
- **Explainable ranking, on purpose.** The LLM proposes; a transparent, tunable Python scorer ranks
  (performance fit, reach, objective value, short-form-video format fit, novelty, minus effort).
- **Grounded generation.** On draft, the system retrieves the brand's top-performing relevant past
  posts as exemplars so copy matches proven voice *and* structure.
- **Honesty over magic.** Every cited number links back to the exact source posts/stats (provenance).
  Recommended timing is derived from the brand's own best day/time buckets, not invented.
- **Ruthless scope.** A small sharp product beats a large unfinished one.

## How AI is used

The whole pipeline is an explicit **LangGraph state graph** (not one mega-prompt). Reasoning-heavy
steps use OpenAI via `langchain-openai` with **Pydantic-structured outputs**; the deterministic
scorer is plain Python.

```
State = { brand, products, past_posts, weights, insights,
          opportunities, ranked, selected, exemplars, draft, feedback_log }

  START
    │
    ▼
[extract_insights]        deterministic metric rollups + LLM synthesis → grounding guard (strips fake numbers)
    │
    ▼
[generate_opportunities]  LLM proposes 6–10 ideas (incl. "Amplify a winner") → grounding guard
    │
    ▼
[score_and_rank]          PURE PYTHON explainable scorer → ranked + per-factor breakdown + provenance
    │
    ▼
   (marketer selects an opportunity in the UI)
    │
    ▼
[generate_content]        RAG-lite exemplar retrieval + LLM → caption, hooks, hashtags, cta, image_prompt
    │
    ▼
[guardrail_check]         LLM self-critique vs brand tone; retry once → deterministic fallback
    │
    ▼
   (marketer edits / approves → schedules on the week calendar)
    │
    ▼
[log_feedback] ─────────► nudges state.weights ──┐   mock published result
    ▲                                             │   closes the self-improving loop
    └─────────────────────────────────────────────┘   (feeds the next score_and_rank run)
```

The scoring formula (weights are tunable in the UI's Advanced drawer and auto-nudged by feedback):

```
score = w_perf·PerformanceFit    # similarity to past winners (theme/format/objective vs top performers)
      + w_reach·AudienceReach     # segment size proxy × platform fit
      + w_obj·ObjectiveValue      # business weight per Discovery/Trust/Conversion
      + w_fmt·FormatFit           # bias toward short-form vertical video
      + w_nov·Novelty             # penalize repeating very recent themes
      - w_eff·EffortCost          # format production cost
```

**Anti-hallucination (graded hard — data company):** all performance numbers are computed in Python
from the seed data and passed into prompts as *facts*. But instruction isn't enforcement, so a
deterministic **grounding guard** (`app/grounding.py`) runs over every LLM rationale and insight
takeaway and **removes any metric-like number that isn't in the real fact set** — even a live model
that ignores the prompt cannot leak a fabricated figure into the ranker, the provenance chips, or the
UI. Every recommendation also carries provenance (the exact post ids / stats behind it), surfaced in
the UI. An eval feeds a poisoned rationale through the guard to prove it strips fakes while keeping
real numbers.

**Robustness:** structured outputs are validated with Pydantic; malformed LLM JSON never crashes the
app — it validates, retries once, then falls back to a deterministic template.

### MOCK_MODE (zero key, zero cost)

`MOCK_MODE=true` (the default) makes every LLM node return realistic, data-consistent pre-baked output,
so the entire flow runs end-to-end with **no API key and no cost**. Set `MOCK_MODE=false` and provide
`OPENAI_API_KEY` to use real OpenAI. Everything else is identical.

## Tech stack

- **Backend:** FastAPI (Python 3.12) · Pydantic v2 · Uvicorn
- **AI orchestration:** LangGraph state graph · OpenAI via `langchain-openai` · Pydantic-structured I/O
- **Frontend:** React + Vite + TypeScript + TailwindCSS (typed client mirroring the API)
- **Single service:** FastAPI serves the built React SPA from `/` and JSON at `/api/*` — no second
  server, no CORS, one URL.
- **Packaging:** one multi-stage `Dockerfile` (build React → copy into Python image) + `docker-compose.yml`.

## API

| Method | Path             | Purpose                                                             |
|--------|------------------|---------------------------------------------------------------------|
| POST   | `/api/plan`      | insights → opportunities → rank; returns ranked opps + provenance   |
| POST   | `/api/generate`  | grounded draft + exemplars used for a selected opportunity          |
| POST   | `/api/approve`   | add a draft to the calendar at a slot                               |
| GET    | `/api/calendar`  | approved posts for the week view                                    |
| POST   | `/api/feedback`  | log a mock published result → returns nudged weights                |
| GET/PUT| `/api/weights`   | view / tune scoring weights                                         |
| GET    | `/api/health`    | ok + mode                                                           |

## Running it

### Option A — Docker (recommended, one command)

```bash
docker compose up --build
# open http://localhost:8000
```

Live mode instead of mock:

```bash
MOCK_MODE=false OPENAI_API_KEY=sk-... docker compose up --build
```

### Option B — Local (two terminals for dev, or build + one server)

Prereqs: Python 3.11+ and Node 18+.

**One server (production-style, serves built frontend):**

```bash
# 1. Backend deps
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt      # Windows
# source .venv/bin/activate && pip install -r backend/requirements.txt   # macOS/Linux

# 2. Build the frontend into backend/static
cd frontend && npm install && npm run build && cd ..
#   then copy frontend/dist/* into backend/static/   (make build does this on Unix)

# 3. Run
cd backend
MOCK_MODE=true ../.venv/Scripts/python -m uvicorn app.main:app --port 8000
# open http://localhost:8000
```

**Hot-reload dev (two terminals):**

```bash
# terminal 1 — API
cd backend && MOCK_MODE=true uvicorn app.main:app --reload --port 8000
# terminal 2 — Vite (proxies /api -> :8000)
cd frontend && npm run dev        # open http://localhost:5173
```

On Windows PowerShell, set env vars with `$env:MOCK_MODE="true"` before the command.

### Evals

```bash
cd backend && MOCK_MODE=true python -m evals.run
```

Runs 8 golden checks: opportunities match schema, an "amplify a winner" exists, rationales cite only
real metrics (anti-hallucination), captions respect platform length limits, generated copy is
keyword-grounded in its exemplars, the **runtime grounding guard strips fabricated metrics while
keeping real ones** (mode-independent, live-safe), and **grounded aggregates survive at any precision**
(no false strips). Prints a pass/fail summary and exits non-zero on failure (CI-ready).

## Seed data

A fictional sustainable skincare brand, **Lumen**, in `backend/app/data/`:
`brand.json`, `products.json`, and `past_posts.json` (18 posts with real metrics). The data encodes
discoverable patterns — short-form video and "behind-the-scenes" over-perform; Thursday/Friday evenings
beat Monday mornings; static product shots underperform — so the engine has something genuine to find.

## What I'd build next

1. **Connect real data** — replace mock metrics with live Instagram/Shopify performance.
2. **Close the loop for real** — feed actual post results into the scorer for continuous per-brand re-weighting.
3. **Per-segment experiments** — auto-A/B content angles per audience so the winning angle compounds.
4. **Creator/UGC briefs + social-as-search** — recommend UGC angles and optimize for in-platform discoverability.

## Scope trade-offs (explicit)

**In:** the full decision → draft → approve → calendar → learn loop, explainable scoring, grounded
generation, anti-hallucination provenance, MOCK_MODE, eval suite.

**Out (deliberately):** real platform publishing, authentication, multi-brand, heavy vector DB
(RAG-lite in-memory retrieval is enough here), and actual image *generation* (we output the image
*prompt*; wire a key + image model to render one).

## AI coding tools used

Built with **Kiro**, using a deliberate model split: the planning/architecture pass (the product
spec in `BUILD_PROMPT.md`, where design decisions compound) was done in **Kiro's web chat with
Claude Opus**; the implementation was done in the **Kiro agentic IDE with Claude Sonnet** (faster
iteration on code). I then reviewed, debugged, and hardened the output myself — the scoring model,
the anti-hallucination grounding guard, the per-platform timing, and the eval suite were all
iterated on by hand until they held up.

## Project structure

```
backend/
  app/
    main.py            FastAPI app + routes + static SPA serving
    schemas.py         Pydantic models for every AI I/O + API contract
    config.py          MOCK_MODE / key / paths
    data_loader.py     load + validate seed JSON
    insights.py        deterministic metric rollups
    scoring.py         PURE-python explainable scorer
    rag.py             in-memory exemplar retrieval (RAG-lite)
    grounding.py       runtime anti-hallucination guard (strips ungrounded numbers)
    llm.py             LLM boundary (mock vs OpenAI, retry + fallback)
    mock.py            pre-baked, data-consistent outputs for MOCK_MODE
    store.py           in-memory calendar + weights + feedback nudging
    graph/{state,nodes,build}.py   the LangGraph state graph
    data/*.json        Lumen seed data
  evals/run.py         golden-case eval suite
frontend/
  src/{App.tsx, api.ts, types.ts}  typed client mirroring the API
  src/components/*                 cards → draft → approve → calendar → tune
Dockerfile             multi-stage build (React → Python)
docker-compose.yml     one-command run
Makefile               local dev helpers
```
