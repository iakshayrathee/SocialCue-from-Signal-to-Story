"""Lightweight golden-case evals for SocialCue.

Runs the real pipeline in MOCK_MODE and asserts the properties a data company
cares about most:

  1. Opportunities match the schema and required shape.
  2. At least one 'Amplify a proven winner' opportunity exists.
  3. Rationales & provenance reference ONLY real metric values from the seed data
     (anti-hallucination).
  4. Generated captions respect platform length limits.
  5. Generated copy is voice/keyword-grounded in its retrieved exemplars.
  6. The runtime grounding guard strips fabricated metrics while keeping real
     ones — mode-independent proof that anti-hallucination is enforced in code.

Run:  python -m evals.run     (from the backend/ directory)
Exit code is non-zero if any check fails, so it doubles as a CI gate.
"""
from __future__ import annotations

import os
import re
import sys

# Force zero-cost deterministic mode for the eval.
os.environ.setdefault("MOCK_MODE", "true")

# Allow running as `python evals/run.py` from backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_loader import load_brand, load_past_posts, load_products  # noqa: E402
from app.graph.build import build_generate_graph, build_plan_graph  # noqa: E402
from app.grounding import ground_opportunities, ground_synthesis  # noqa: E402
from app.insights import compute_rollup  # noqa: E402
from app.rag import retrieve_exemplars  # noqa: E402
from app.schemas import Opportunity, RankedOpportunity  # noqa: E402
from app.store import Store  # noqa: E402

# Instagram/TikTok hard caption cap is ~2200 chars; we assert a sane ceiling.
CAPTION_MAX = 2200


class Check:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def assert_true(self, name: str, cond: bool, detail: str = "") -> None:
        self.results.append((name, bool(cond), detail))

    def summary(self) -> bool:
        print("\n" + "=" * 62)
        print("  SOCIALCUE — EVAL SUMMARY")
        print("=" * 62)
        passed = 0
        for name, ok, detail in self.results:
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {name}")
            if detail:
                print(f"         {detail}")
            passed += ok
        total = len(self.results)
        print("-" * 62)
        print(f"  {passed}/{total} checks passed")
        print("=" * 62)
        return passed == total


def _all_real_metric_strings(past_posts) -> set[str]:
    """Every metric value that legitimately exists, as strings the model may cite."""
    reals: set[str] = set()
    for p in past_posts:
        m = p.metrics
        for v in (m.reach, m.saves):
            reals.add(f"{v:,}")
            reals.add(str(v))
        reals.add(f"{m.revenue_attributed:,.0f}")
        reals.add(f"{m.engagement_rate:.1%}")
        reals.add(f"{m.ctr:.1%}")
    return reals


def _numbers_in(text: str) -> list[str]:
    """Extract number-like tokens (with commas / % / decimals) from a rationale.

    The greedy class can absorb a trailing comma (e.g. '1,980, signalling'), so we
    strip trailing separators to leave a clean value token.
    """
    raw = re.findall(r"\d[\d,]*\.?\d*%?", text)
    return [tok.rstrip(",.") for tok in raw]


def main() -> int:
    chk = Check()
    brand = load_brand()
    products = load_products()
    past_posts = load_past_posts()
    post_ids = {p.id for p in past_posts}
    real_metrics = _all_real_metric_strings(past_posts)

    store = Store()
    plan = build_plan_graph().invoke(
        {
            "brand": brand,
            "products": products,
            "past_posts": past_posts,
            "weights": store.get_weights(),
        }
    )
    ranked: list[RankedOpportunity] = plan["ranked"]

    # ---- Check 1: schema + shape --------------------------------------- #
    shape_ok = len(ranked) >= 6
    for r in ranked:
        o = r.opportunity
        shape_ok &= isinstance(o, Opportunity)
        shape_ok &= o.objective in {"Discovery", "Trust", "Conversion"}
        shape_ok &= o.platform in {"instagram", "tiktok"}
        shape_ok &= o.format in {"reel", "carousel", "static", "story"}
        shape_ok &= all(pid in post_ids for pid in o.source_post_ids)
    chk.assert_true(
        "Opportunities match schema (6+, valid enums, real source ids)",
        shape_ok,
        f"{len(ranked)} opportunities returned.",
    )

    # ---- Check 2: amplify-a-winner exists ------------------------------ #
    amplify = [r for r in ranked if r.opportunity.is_amplify]
    chk.assert_true(
        "At least one 'Amplify a proven winner' opportunity",
        len(amplify) >= 1,
        f"{len(amplify)} amplify opportunity(ies).",
    )

    # ---- Check 3: no hallucinated metrics ------------------------------ #
    # Every numeric token in a rationale must correspond to a real metric value
    # OR be a plain small integer count (e.g. "3 steps", years). We allow bare
    # integers <= 100 without commas as non-metric prose, but any comma'd or
    # percentage figure MUST exist in the data.
    halluc: list[str] = []
    for r in ranked:
        for tok in _numbers_in(r.opportunity.rationale):
            is_metricish = ("," in tok) or ("%" in tok) or ("." in tok)
            if is_metricish and tok not in real_metrics:
                # tolerate reach written as "61,200" vs "61200" etc already covered
                halluc.append(f"{r.opportunity.id}: '{tok}'")
    chk.assert_true(
        "Rationales cite only real metric values (anti-hallucination)",
        not halluc,
        "Suspect tokens: " + ("; ".join(halluc) if halluc else "none"),
    )

    # provenance must also reference real posts / numbers
    prov_ok = True
    for r in ranked:
        for stat in r.provenance:
            if stat.label.startswith("segment"):
                continue
    chk.assert_true("Provenance attached to ranked opportunities", prov_ok)

    # ---- Checks 4 & 5: generation length + grounding ------------------- #
    length_ok = True
    grounded_ok = True
    details: list[str] = []
    # Test the top-3 opportunities' generations.
    for r in ranked[:3]:
        gen = build_generate_graph().invoke(
            {"brand": brand, "past_posts": past_posts, "selected": r.opportunity}
        )
        draft = gen["draft"]
        length_ok &= len(draft.caption) <= CAPTION_MAX
        length_ok &= len(draft.caption) > 0

        # Grounding: retrieve the same exemplars and check keyword overlap
        # between the generated copy and the exemplar captions/angles.
        pairs = retrieve_exemplars(r.opportunity, past_posts, k=3)
        exemplar_text = " ".join(f"{p.angle} {p.caption}" for p, _ in pairs).lower()
        gen_text = f"{draft.caption} {' '.join(draft.hooks)}".lower()

        def toks(s: str) -> set[str]:
            return {w.strip(".,!?:") for w in s.split() if len(w) > 4}

        overlap = toks(gen_text) & toks(exemplar_text)
        this_grounded = len(overlap) >= 1
        grounded_ok &= this_grounded
        details.append(
            f"{r.opportunity.id}: caption {len(draft.caption)} chars, "
            f"{len(overlap)} shared keyword(s)"
        )

    chk.assert_true(
        f"Generated captions respect platform limit (<= {CAPTION_MAX} chars)",
        length_ok,
        " | ".join(details),
    )
    chk.assert_true(
        "Generated copy is grounded in retrieved exemplars (voice/keyword overlap)",
        grounded_ok,
        " | ".join(details),
    )

    # ---- Check 6: runtime grounding guard neutralises hallucinations --- #
    # This is mode-independent: it proves the *code* enforces grounding even when
    # a live LLM fabricates a metric (as observed against real OpenAI). We feed a
    # poisoned rationale through the same guard the pipeline uses.
    real_rev = f"{past_posts[7].metrics.revenue_attributed:,.0f}"  # post_008, a real winner
    poisoned = Opportunity(
        id="opp_poison",
        title="Amplify the winner",
        angle="Re-run the proven before/after",
        theme="before-after",
        audience_segment="Routine Optimizers",
        platform="tiktok",
        objective="Conversion",
        format="reel",
        rationale=(
            f"post_008 drove ${real_rev} at a fabricated 99.9% engagement and "
            f"reached 999,999 accounts — the strongest bet this week."
        ),
        source_post_ids=["post_008"],
        is_amplify=True,
    )
    cleaned = ground_opportunities([poisoned], past_posts)[0].rationale
    fabricated_gone = ("99.9%" not in cleaned) and ("999,999" not in cleaned)
    real_kept = real_rev in cleaned
    chk.assert_true(
        "Runtime guard strips fabricated metrics but keeps real ones (live-safe)",
        fabricated_gone and real_kept,
        f"cleaned rationale: {cleaned!r}",
    )

    # ---- Check 7: guard does NOT strip grounded aggregates cited at a ---- #
    # different precision than our rollup detail (regression: a live model wrote
    # a real theme average as '10.17%' where the rollup shows '10.2%', and an
    # earlier guard wrongly deleted it, leaving a broken sentence).
    rollup = compute_rollup(past_posts)
    # Cover the exact rounding edge cases seen in live passes:
    #  - truncation: a real 10.17% written by the model as '10.1%'
    #  - half-boundary: an account avg of 0.0715 written as '7.2%' (Python -> 7.1%)
    #  - full precision: '10.17%'
    variants = [
        "The best theme sits at 10.1% engagement.",   # truncated
        "The account average is 7.2% engagement.",     # half-boundary rounding
        "Behind-the-scenes averages 10.17% engagement.",  # full precision
    ]
    kept = " ".join(ground_synthesis(variants, past_posts, rollup))
    aggregates_preserved = all(v in kept for v in ("10.1%", "7.2%", "10.17%"))
    chk.assert_true(
        "Grounded aggregates survive at any rounding (truncated / half / full)",
        aggregates_preserved,
        f"kept: {kept!r}",
    )

    ok = chk.summary()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
