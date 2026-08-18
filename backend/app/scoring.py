"""Pure-Python, explainable opportunity scorer. NO LLM here.

'AI proposes, code disposes.' Every factor is deterministic and traceable so a
marketer can audit exactly why one idea outranks another.
"""
from __future__ import annotations

from .schemas import (
    Insights,
    LabeledStat,
    Opportunity,
    PostedAt,
    PostFormat,
    RankedOpportunity,
    ScoreBreakdown,
    Weights,
)

# Relative production cost per format (0 = cheap, 1 = expensive).
_EFFORT_BY_FORMAT: dict[PostFormat, float] = {
    "story": 0.15,
    "static": 0.25,
    "carousel": 0.55,
    "reel": 0.80,
}

# Format-fit bias: short-form vertical video is prioritised (2026 trend).
_FORMAT_FIT: dict[PostFormat, float] = {
    "reel": 1.0,
    "story": 0.5,
    "carousel": 0.45,
    "static": 0.25,
}

# Platform reach multiplier (short-form-video-native platforms skew higher).
_PLATFORM_FIT: dict[str, float] = {"tiktok": 1.0, "instagram": 0.85}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _performance_fit(opp: Opportunity, insights: Insights) -> tuple[float, LabeledStat | None]:
    """Similarity to proven winners: does this format/theme/objective show up
    among the brand's top performers?"""
    score = 0.0
    proof: LabeledStat | None = None

    top_formats = {s.label: s.value for s in insights.rollup.best_formats}
    top_themes = {s.label: s.value for s in insights.rollup.best_themes}

    # Format match against best-performing formats (normalised by avg engagement).
    avg_er = insights.rollup.avg_engagement_rate or 1e-9
    if opp.format in top_formats:
        fmt_er = top_formats[opp.format]
        ratio = fmt_er / avg_er
        contrib = _clamp((ratio - 1.0) + 0.5)
        score += 0.4 * contrib
        proof = LabeledStat(
            label=f"{opp.format} avg engagement",
            value=round(fmt_er, 4),
            detail=f"{ratio:.2f}x the {avg_er:.3f} account average",
        )

    # Theme match against best-performing themes.
    if opp.theme and opp.theme in top_themes:
        theme_er = top_themes[opp.theme]
        theme_ratio = theme_er / avg_er
        score += 0.2 * _clamp((theme_ratio - 1.0) + 0.5)
        if proof is None:
            proof = LabeledStat(
                label=f"theme '{opp.theme}' avg engagement",
                value=round(theme_er, 4),
                detail=f"{theme_ratio:.2f}x the account average",
            )

    # Objective presence among top posts.
    top_by_obj = insights.rollup.top_posts_by_objective.get(opp.objective, [])
    if opp.source_post_ids and any(pid in top_by_obj for pid in opp.source_post_ids):
        score += 0.3
    elif top_by_obj:
        score += 0.15

    # Grounded in specific winning posts.
    if opp.source_post_ids:
        score += min(0.2, 0.1 * len(opp.source_post_ids))

    return _clamp(score), proof


def _audience_reach(
    opp: Opportunity, segment_sizes: dict[str, int], max_segment: int
) -> tuple[float, LabeledStat]:
    size = segment_sizes.get(opp.audience_segment, max_segment // 2)
    size_norm = size / max_segment if max_segment else 0.5
    platform = _PLATFORM_FIT.get(opp.platform, 0.7)
    value = _clamp(0.6 * size_norm + 0.4 * platform)
    return value, LabeledStat(
        label=f"segment '{opp.audience_segment}'",
        value=float(size),
        detail=f"size proxy {size:,} x {opp.platform} fit {platform:.2f}",
    )


def _novelty(
    opp: Opportunity, recent_themes: list[str]
) -> tuple[float, LabeledStat | None]:
    """Penalise repeating very recent themes."""
    if opp.is_amplify:
        # Amplify is deliberately a re-run of a winner; modest novelty, not zero.
        return 0.55, None
    if opp.theme in recent_themes:
        return 0.25, LabeledStat(
            label="theme freshness",
            value=0.25,
            detail=f"'{opp.theme}' posted recently; lower novelty",
        )
    return 0.9, None


def score_opportunity(
    opp: Opportunity,
    insights: Insights,
    weights: Weights,
    segment_sizes: dict[str, int],
    max_segment: int,
    recent_themes: list[str],
) -> tuple[float, ScoreBreakdown, list[LabeledStat]]:
    provenance: list[LabeledStat] = []

    perf, perf_proof = _performance_fit(opp, insights)
    if perf_proof:
        provenance.append(perf_proof)

    reach, reach_proof = _audience_reach(opp, segment_sizes, max_segment)
    provenance.append(reach_proof)

    obj_value = _clamp(weights.obj_value.get(opp.objective, 0.6))

    fmt_fit = _FORMAT_FIT.get(opp.format, 0.3)

    novelty, nov_proof = _novelty(opp, recent_themes)
    if nov_proof:
        provenance.append(nov_proof)

    effort = _EFFORT_BY_FORMAT.get(opp.format, 0.5)

    breakdown = ScoreBreakdown(
        performance_fit=round(perf, 4),
        audience_reach=round(reach, 4),
        objective_value=round(obj_value, 4),
        format_fit=round(fmt_fit, 4),
        novelty=round(novelty, 4),
        effort_cost=round(effort, 4),
    )

    score = (
        weights.w_perf * perf
        + weights.w_reach * reach
        + weights.w_obj * obj_value
        + weights.w_fmt * fmt_fit
        + weights.w_nov * novelty
        - weights.w_eff * effort
    )

    return round(score, 4), breakdown, provenance


def recommended_time(opp: Opportunity, insights: Insights) -> PostedAt:
    """Timing derived from the brand's own best day/time buckets for the
    opportunity's platform (falls back to the account-wide best slot)."""
    by_platform = insights.rollup.best_day_time_by_platform or {}
    buckets = by_platform.get(opp.platform) or insights.rollup.best_day_time
    if buckets:
        # Labels look like "Thursday 19:00".
        parts = buckets[0].label.split(" ")
        if len(parts) == 2:
            return PostedAt(day=parts[0], time=parts[1])
    # Fallback default (and the UI says so).
    return PostedAt(day="Thursday", time="19:00")


def rank_opportunities(
    opportunities: list[Opportunity],
    insights: Insights,
    weights: Weights,
    segment_sizes: dict[str, int],
    recent_themes: list[str],
) -> list[RankedOpportunity]:
    max_segment = max(segment_sizes.values()) if segment_sizes else 1
    ranked: list[RankedOpportunity] = []
    for opp in opportunities:
        score, breakdown, provenance = score_opportunity(
            opp, insights, weights, segment_sizes, max_segment, recent_themes
        )
        ranked.append(
            RankedOpportunity(
                opportunity=opp,
                score=score,
                breakdown=breakdown,
                recommended_time=recommended_time(opp, insights),
                provenance=provenance,
            )
        )
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked
