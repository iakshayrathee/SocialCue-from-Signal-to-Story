"""LLM boundary.

In MOCK_MODE (default) every function returns pre-baked, data-consistent output
so the app runs with no key. With a real key we call OpenAI via langchain-openai
using Pydantic-structured outputs, retry once on malformed output, then fall back
to the deterministic mock so the app can never crash on bad JSON.
"""
from __future__ import annotations

import json

from pydantic import BaseModel

from . import mock
from .config import get_settings
from .schemas import Brand, Draft, Insights, Opportunity, PastPost, Product


# --- structured-output wrapper models (for the real LLM path) --------------- #
class _SynthesisOut(BaseModel):
    takeaways: list[str]


class _OpportunitiesOut(BaseModel):
    opportunities: list[Opportunity]


class _CritiqueOut(BaseModel):
    passed: bool
    notes: str


def _chat():
    """Lazily construct a ChatOpenAI client (only when real LLM is in use)."""
    from langchain_openai import ChatOpenAI  # imported lazily

    s = get_settings()
    return ChatOpenAI(model=s.openai_model, api_key=s.openai_api_key, temperature=0.4)


def _structured(prompt: str, schema: type[BaseModel]):
    """Call the LLM with structured output, retrying once."""
    llm = _chat().with_structured_output(schema)
    last_err: Exception | None = None
    for _ in range(2):  # initial try + one retry
        try:
            return llm.invoke(prompt)
        except Exception as err:  # noqa: BLE001 - we intentionally recover
            last_err = err
    raise RuntimeError(f"structured LLM call failed after retry: {last_err}")


# --------------------------------------------------------------------------- #
# Public API used by graph nodes
# --------------------------------------------------------------------------- #
def synthesize_insights(brand: Brand, rollup) -> list[str]:
    s = get_settings()
    if not s.use_real_llm:
        return mock.mock_synthesis(brand, rollup)
    try:
        facts = rollup.model_dump()
        prompt = (
            f"You are {brand.name}'s data analyst. Using ONLY the numbers in this JSON "
            f"of computed metrics, write 3-4 short plain-English takeaways. Never invent "
            f"a number that is not present. For TIMING, do NOT state a single universal "
            f"best time; timing is platform-specific, so reference "
            f"'best_day_time_by_platform' (e.g. TikTok peaks <slot>, Instagram peaks "
            f"<slot>) rather than the account-wide 'best_day_time'.\n\n"
            f"METRICS:\n{json.dumps(facts, default=str)}"
        )
        return _structured(prompt, _SynthesisOut).takeaways  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        return mock.mock_synthesis(brand, rollup)


def propose_opportunities(
    brand: Brand,
    products: list[Product],
    insights: Insights,
    past_posts: list[PastPost],
) -> list[Opportunity]:
    s = get_settings()
    if not s.use_real_llm:
        return mock.mock_opportunities(brand, products, past_posts)
    try:
        prompt = (
            f"You are a senior D2C content strategist for {brand.name}. Propose 6-10 "
            f"content opportunities. Objectives must be Discovery, Trust, or Conversion. "
            f"CRITICAL: exactly one opportunity that repurposes/re-runs a top past post MUST "
            f"have the boolean field is_amplify set to true (not just described as such in the "
            f"rationale). All others must have is_amplify=false. Every rationale must reference "
            f"ONLY the metrics provided; cite the post ids you rely on in source_post_ids. "
            f"Also set a short 'theme' on each opportunity matching the kind of content.\n\n"
            f"BRAND: {brand.model_dump_json()}\n\n"
            f"PRODUCTS: {json.dumps([p.model_dump() for p in products])}\n\n"
            f"INSIGHTS: {insights.model_dump_json()}\n\n"
            f"PAST_POSTS: {json.dumps([p.model_dump() for p in past_posts], default=str)}"
        )
        out = _structured(prompt, _OpportunitiesOut)
        opps = out.opportunities  # type: ignore[union-attr]
        if not opps:
            raise ValueError("empty opportunities")
        return opps
    except Exception:  # noqa: BLE001
        return mock.mock_opportunities(brand, products, past_posts)


def generate_draft(
    brand: Brand,
    opp: Opportunity,
    exemplars: list[PastPost],
    products: list[Product] | None = None,
    revision_note: str | None = None,
) -> Draft:
    s = get_settings()
    if not s.use_real_llm:
        return mock.mock_draft(brand, opp, exemplars)
    try:
        ex = [
            {"caption": e.caption, "angle": e.angle, "engagement_rate": e.metrics.engagement_rate}
            for e in exemplars
        ]
        # Pass the real product catalog so the copy uses actual product names and
        # benefits instead of inventing generic claims (observed live: a skincare
        # post drifting into vague 'understanding your body's needs' language).
        prod = [
            {"name": p.name, "description": p.description, "key_benefits": p.key_benefits}
            for p in (products or [])
        ]
        revision = (
            f" A previous attempt failed the tone check for this reason: "
            f"'{revision_note}'. Fix that while keeping the exemplar voice."
            if revision_note
            else ""
        )
        prompt = (
            f"Write a {opp.platform} {opp.format} post for {brand.name}, a "
            f"skincare brand. Stay specific to skincare and this brand's products; "
            f"do not drift into generic wellness language. "
            f"Match this brand tone: {brand.tone_of_voice.model_dump_json()}. "
            f"Ground the voice and structure in these proven past posts (exemplars): "
            f"{json.dumps(ex)}. Relevant products: {json.dumps(prod)}. "
            f"Opportunity: {opp.model_dump_json()}.{revision} "
            f"Return caption, 3 hooks, up to 6 hashtags (each a single token, no "
            f"leading spaces), a cta, and an image_prompt."
        )
        return _structured(prompt, Draft)  # type: ignore[return-value]
    except Exception:  # noqa: BLE001
        return mock.mock_draft(brand, opp, exemplars)


def critique_draft(brand: Brand, draft: Draft) -> tuple[bool, str]:
    s = get_settings()
    if not s.use_real_llm:
        return mock.mock_critique(brand, draft)
    try:
        prompt = (
            f"You are {brand.name}'s brand editor. Tone rules: "
            f"{brand.tone_of_voice.model_dump_json()}. Does this draft follow the rules "
            f"(no over-promising, no jargon dumps, on-voice)? Draft: {draft.model_dump_json()}. "
            f"Return passed (bool) and a one-line notes."
        )
        out = _structured(prompt, _CritiqueOut)
        return out.passed, out.notes  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        return mock.mock_critique(brand, draft)
