# SocialCue — from *Signal* to *Story*
**An AI content strategist that decides what a D2C brand should post, and why — grounded in the brand's own performance data.**

> This is the explanation (submission item 3).

---

### The problem I chose to solve
D2C teams don't struggle to *write* a caption — tools have made that free. They struggle to decide **what is worth posting, for whom, and when** — and today those decisions are disconnected from the data that should inform them (product catalog, audience, and *past post performance*). The result: content gets made on gut feel, and nobody connects the decision to the outcome.

So I deliberately did **not** build another caption generator. Generation is commoditized. I built the layer above it: a **decision engine that ranks content opportunities by predicted value using the brand's own history, explains every recommendation with real numbers, and only then generates.** The value is the decision and its rationale, not the output.

### My product decisions
- **Decision-first, generation-second.** The hero of the product is a ranked list of *opportunities*, each with a plain-English "why now" backed by the brand's actual metrics. Generation is a downstream action, not the point.
- **DTC-native objectives.** Every opportunity serves **Discovery, Trust, or Conversion** — the way a D2C marketer actually thinks — not abstract funnel jargon.
- **Explainable ranking, on purpose.** The LLM *proposes* opportunities; a transparent, tunable Python scorer *ranks* them (performance-fit, reach, objective value, short-form-video format fit, novelty, minus effort). Marketers can trust and tune it. "AI proposes, code disposes."
- **Grounded generation.** When a marketer drafts, the system retrieves their top-performing past posts as exemplars so the copy matches proven voice *and* structure.
- **Honesty over magic.** Every cited number links back to its source posts (provenance). When data is thin, the UI says it's using best-practice defaults instead of pretending.
- **Ruthless scope.** Real publishing, auth, and image generation are out; the core decision→draft→approve→calendar→learn loop is in. A small sharp product beats a large unfinished one.

### How AI is being used
- **LangGraph orchestrates an explicit decision pipeline** (a state graph, not one mega-prompt): extract insights → generate opportunities → *deterministic* score/rank → grounded generation → tone guardrail (LLM self-critique) → log feedback. The feedback step **cycles back** into scoring — a real self-improving loop.
- **LLMs (OpenAI) with Pydantic-validated structured outputs** for the reasoning-heavy steps; retries + deterministic fallback so it never crashes on bad JSON.
- **RAG-lite** exemplar retrieval grounds generation in the brand's proven winners.
- **Anti-hallucination, enforced in code (not just prompted):** metrics are computed in Python and passed to the model as facts. A deterministic **grounding guard** (`app/grounding.py`) then runs over every LLM rationale and insight takeaway and *strips any number that isn't in the real fact set* — so even if a live model disobeys the prompt, no fabricated metric reaches the ranker or the UI. An eval proves it live-safe.
- **A tiny eval suite** checks schema validity, that rationales cite only real metrics, platform length limits, and voice fidelity.
- **Built with Kiro, with a deliberate model split:** the planning/architecture pass (the product spec in `BUILD_PROMPT.md`, where design decisions compound) was done in Kiro's **web chat with Claude Opus**; the implementation was done in the **Kiro agentic IDE with Claude Sonnet** (faster iteration on code). I then reviewed, debugged, and hardened the output by hand — the scoring model, the anti-hallucination grounding guard, per-platform timing, and the eval suite were all iterated on until they held up.

### What I would build next
1. **Connect real data** — replace mock metrics with live Instagram/Shopify performance so the loop learns from reality.
2. **Close the loop for real** — feed actual post results back into the scorer for continuous, per-brand re-weighting.
3. **Per-segment experiments** — auto-A/B content angles per audience, and let the winning angle compound.
4. **Creator/UGC briefs + social-as-search** — recommend UGC angles and optimize for in-platform discoverability, where D2C growth is moving.

### Run it
`MOCK_MODE=true` (the default) runs the full workflow with zero API key. Add an OpenAI key and set `MOCK_MODE=false` for live generation. Frontend: React + Vite + TypeScript. Backend: FastAPI + LangGraph. `docker compose up --build` for one command.
