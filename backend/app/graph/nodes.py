"""LangGraph node functions. Each takes the state and returns a partial update."""
from __future__ import annotations

import re
from collections import Counter

from .. import llm
from ..grounding import ground_opportunities, ground_synthesis
from ..insights import compute_rollup
from ..rag import retrieve_exemplars
from ..scoring import rank_opportunities
from ..schemas import Draft, Insights
from .state import GraphState


def _recent_themes(past_posts) -> list[str]:
    """Themes considered 'saturated' (appear often) get a novelty penalty."""
    counts = Counter(p.theme for p in past_posts)
    return [theme for theme, c in counts.items() if c >= 3]


# Word STEMS so we match inflections ("repurpose"/"repurposing", "amplify"/
# "amplifying"). Substring match against a lowercased blob of title+angle+rationale.
_AMPLIFY_HINTS = (
    "amplif",
    "re-run",
    "rerun",
    "repurpos",
    "proven winner",
    "top past post",
    "top-performing",
    "recreate",
    "re-post",
    "repost",
)

_POST_ID_RE = re.compile(r"post_\d{3,}")


def _recover_source_ids(opportunities, past_posts):
    """Recover grounding when the LLM writes post ids into the rationale prose
    instead of the structured source_post_ids field.

    Observed live: opportunities came back with source_post_ids=[] while the
    rationale said '...from post_015...'. Without this, provenance chips and the
    performance-fit score silently lose their grounding. We extract real post ids
    from the text and tidy any '(Source post IDs: [...])' fragment the model appends.
    """
    valid = {p.id for p in past_posts}
    for o in opportunities:
        if not o.source_post_ids:
            found: list[str] = []
            for text in (o.rationale, o.angle, o.title):
                for pid in _POST_ID_RE.findall(text or ""):
                    if pid in valid and pid not in found:
                        found.append(pid)
            o.source_post_ids = found
        # Strip an awkward trailing 'Source post IDs: [...]' the model sometimes appends.
        o.rationale = re.sub(
            r"\s*Source post ID[s]?:.*$", "", o.rationale, flags=re.IGNORECASE
        ).strip()
    return opportunities


def _ensure_amplify(opportunities, past_posts):
    """Guarantee at least one 'Amplify a proven winner' opportunity.

    The brief requires one. In MOCK_MODE it's hard-coded, but a live LLM often
    writes an amplify-style rationale/title without setting the structured
    is_amplify flag (observed: a card titled 'Amplify Proven Winner' with
    is_amplify=false). We enforce it deterministically so the requirement holds
    in both modes and the UI badge is reliable.
    """
    if not opportunities:
        return opportunities
    if any(o.is_amplify for o in opportunities):
        return opportunities

    # 1) The model signalled amplify intent in the title/angle/rationale but
    #    forgot the flag. Match against all three, using word stems.
    for o in opportunities:
        blob = f"{o.title} {o.angle} {o.rationale}".lower()
        if any(hint in blob for hint in _AMPLIFY_HINTS):
            o.is_amplify = True
            return opportunities

    # 2) Otherwise, promote the opportunity that repurposes the single
    #    highest-revenue past post — the most defensible "amplify a winner".
    revenue = {p.id: p.metrics.revenue_attributed for p in past_posts}
    best_opp = None
    best_rev = -1.0
    for o in opportunities:
        for pid in o.source_post_ids:
            if revenue.get(pid, -1.0) > best_rev:
                best_rev = revenue.get(pid, -1.0)
                best_opp = o
    (best_opp or opportunities[0]).is_amplify = True
    return opportunities


# --------------------------------------------------------------------------- #
# 1. extract_insights — deterministic rollups + LLM synthesis
# --------------------------------------------------------------------------- #
def extract_insights(state: GraphState) -> GraphState:
    rollup = compute_rollup(state["past_posts"])
    synthesis = llm.synthesize_insights(state["brand"], rollup)
    # Enforce grounding in code: strip any number the model invented.
    synthesis = ground_synthesis(synthesis, state["past_posts"], rollup)
    return {"insights": Insights(rollup=rollup, synthesis=synthesis)}


# --------------------------------------------------------------------------- #
# 2. generate_opportunities — LLM proposes (Pydantic-structured)
# --------------------------------------------------------------------------- #
def generate_opportunities(state: GraphState) -> GraphState:
    opps = llm.propose_opportunities(
        state["brand"], state["products"], state["insights"], state["past_posts"]
    )
    opps = _recover_source_ids(opps, state["past_posts"])
    opps = _ensure_amplify(opps, state["past_posts"])
    # Runtime anti-hallucination: no fabricated metric survives into the ranker,
    # the provenance chips, or the UI — regardless of what the LLM wrote.
    opps = ground_opportunities(opps, state["past_posts"])
    return {"opportunities": opps}


# --------------------------------------------------------------------------- #
# 3. score_and_rank — PURE PYTHON
# --------------------------------------------------------------------------- #
def score_and_rank(state: GraphState) -> GraphState:
    brand = state["brand"]
    segment_sizes = {s.name: s.size_proxy for s in brand.target_audience}
    ranked = rank_opportunities(
        state["opportunities"],
        state["insights"],
        state["weights"],
        segment_sizes,
        _recent_themes(state["past_posts"]),
    )
    return {"ranked": ranked}


# --------------------------------------------------------------------------- #
# 4. generate_content — RAG-lite grounding + LLM generation
# --------------------------------------------------------------------------- #
def _normalize_draft(draft: Draft) -> Draft:
    """Clean up live-LLM formatting quirks so the UI renders cleanly.

    Observed live: hashtags came back with leading spaces (' #SimpleStart') and
    duplicate '#'. We trim whitespace, guarantee exactly one leading '#', drop
    blanks, and de-duplicate while preserving order. Caption/hooks/cta are trimmed.
    """
    seen: set[str] = set()
    tags: list[str] = []
    for h in draft.hashtags:
        cleaned = "#" + h.strip().lstrip("#").strip()
        if cleaned == "#" or cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        tags.append(cleaned)
    draft.hashtags = tags
    draft.hooks = [h.strip() for h in draft.hooks if h.strip()]
    draft.caption = draft.caption.strip()
    draft.cta = draft.cta.strip()
    return draft


def generate_content(state: GraphState) -> GraphState:
    opp = state["selected"]
    pairs = retrieve_exemplars(opp, state["past_posts"], k=3)
    exemplar_posts = [p for p, _ in pairs]
    exemplar_refs = [ref for _, ref in pairs]
    draft = llm.generate_draft(
        state["brand"], opp, exemplar_posts, state.get("products", [])
    )
    return {"draft": _normalize_draft(draft), "exemplars": exemplar_refs}


# --------------------------------------------------------------------------- #
# 5. guardrail_check — LLM self-critique; retry once, then deterministic fallback
# --------------------------------------------------------------------------- #
def _deterministic_fallback_draft(state: GraphState) -> Draft:
    opp = state["selected"]
    brand = state["brand"]
    return Draft(
        caption=(
            f"{opp.angle}. Made by {brand.name} — clear, science-backed, and kind "
            f"to your skin. Here's how it fits your routine."
        ),
        hooks=[opp.title, "The simple version", "Save this for later"],
        hashtags=["#skincare", "#skinbarrier", "#cleanbeauty", "#lumenskincare"],
        cta="Learn more — link in bio.",
        image_prompt="Clean minimalist skincare editorial, soft natural light, beige palette.",
    )


def guardrail_check(state: GraphState) -> GraphState:
    brand = state["brand"]
    draft = state["draft"]
    passed, notes = llm.critique_draft(brand, draft)
    if passed:
        return {"guardrail_passed": True, "guardrail_notes": notes}

    # Retry once. Keep the exemplars AND products so the regenerated draft stays
    # grounded (a tone miss is not a reason to throw away the brand's proven
    # voice) and pass the critique note so the model actually fixes the issue.
    pairs = retrieve_exemplars(state["selected"], state["past_posts"], k=3)
    exemplar_posts = [p for p, _ in pairs]
    regenerated = _normalize_draft(
        llm.generate_draft(
            brand,
            state["selected"],
            exemplar_posts,
            state.get("products", []),
            revision_note=notes,
        )
    )
    passed2, notes2 = llm.critique_draft(brand, regenerated)
    if passed2:
        return {
            "draft": regenerated,
            "guardrail_passed": True,
            "guardrail_notes": f"Retried once (kept exemplars): {notes2}",
        }

    # Deterministic fallback that is guaranteed on-tone.
    fallback = _deterministic_fallback_draft(state)
    return {
        "draft": fallback,
        "guardrail_passed": True,
        "guardrail_notes": (
            f"LLM output failed tone check ({notes2}); used a safe deterministic template."
        ),
    }
