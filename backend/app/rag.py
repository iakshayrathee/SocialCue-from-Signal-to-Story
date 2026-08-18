"""RAG-lite: retrieve top relevant, high-performing past posts as exemplars.

No heavy vector DB. A transparent relevance score over structured fields plus a
performance weight is enough for the MVP and keeps grounding auditable.
"""
from __future__ import annotations

from .schemas import ExemplarRef, Opportunity, PastPost


def _keyword_overlap(a: str, b: str) -> float:
    sa = {w for w in a.lower().split() if len(w) > 3}
    sb = {w for w in b.lower().split() if len(w) > 3}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _relevance(opp: Opportunity, post: PastPost, max_er: float) -> float:
    score = 0.0
    if post.platform == opp.platform:
        score += 0.25
    if post.format == opp.format:
        score += 0.2
    if post.objective == opp.objective:
        score += 0.2
    if opp.theme and post.theme == opp.theme:
        score += 0.25
    # Text similarity between the opportunity angle and post angle/caption.
    score += 0.2 * _keyword_overlap(opp.angle, f"{post.angle} {post.caption}")
    # Performance weight: reward proven winners.
    perf = (post.metrics.engagement_rate / max_er) if max_er else 0.0
    score += 0.35 * perf
    # Directly cited source posts are the strongest signal.
    if post.id in opp.source_post_ids:
        score += 0.5
    return score


def retrieve_exemplars(
    opp: Opportunity, past_posts: list[PastPost], k: int = 3
) -> list[tuple[PastPost, ExemplarRef]]:
    if not past_posts:
        return []
    max_er = max(p.metrics.engagement_rate for p in past_posts)
    scored = sorted(
        past_posts, key=lambda p: _relevance(opp, p, max_er), reverse=True
    )
    top = scored[:k]
    out: list[tuple[PastPost, ExemplarRef]] = []
    for p in top:
        reasons = []
        if p.id in opp.source_post_ids:
            reasons.append("cited as source")
        if p.format == opp.format:
            reasons.append(f"same format ({p.format})")
        if opp.theme and p.theme == opp.theme:
            reasons.append(f"same theme ({p.theme})")
        reasons.append(f"{p.metrics.engagement_rate:.1%} engagement")
        out.append(
            (
                p,
                ExemplarRef(
                    post_id=p.id,
                    angle=p.angle,
                    reason=", ".join(reasons),
                ),
            )
        )
    return out
