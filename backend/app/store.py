"""In-memory application state: scoring weights + approved calendar posts.

Stateless HTTP with a tiny module-level store is plenty for the MVP. The weights
here are what the feedback loop nudges, closing the self-improving cycle that
feeds the next /api/plan run.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime

from .data_loader import load_past_posts
from .schemas import ApprovedPost, MockResult, Weights


class Store:
    def __init__(self) -> None:
        self.weights = Weights()
        self.calendar: dict[str, ApprovedPost] = {}

    # -- weights ---------------------------------------------------------- #
    def get_weights(self) -> Weights:
        return self.weights

    def set_weights(self, weights: Weights) -> Weights:
        self.weights = weights
        return self.weights

    # -- calendar --------------------------------------------------------- #
    def add_post(self, post: ApprovedPost) -> ApprovedPost:
        self.calendar[post.id] = post
        return post

    def list_posts(self) -> list[ApprovedPost]:
        return list(self.calendar.values())

    def get_post(self, post_id: str) -> ApprovedPost | None:
        return self.calendar.get(post_id)


store = Store()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def simulate_result(post: ApprovedPost) -> MockResult:
    """Fabricate a plausible published result, biased by the post's objective
    and format so the demo feels alive. Grounded loosely in seed averages."""
    posts = load_past_posts()
    avg_reach = sum(p.metrics.reach for p in posts) / len(posts)
    avg_rev = sum(p.metrics.revenue_attributed for p in posts) / len(posts)

    fmt = post.opportunity.format
    obj = post.opportunity.objective
    reach_mult = {"reel": 1.4, "story": 0.7, "carousel": 0.9, "static": 0.5}.get(fmt, 1.0)
    rev_mult = {"Conversion": 1.6, "Trust": 1.0, "Discovery": 0.7}.get(obj, 1.0)

    jitter = random.uniform(0.85, 1.25)
    reach = int(avg_reach * reach_mult * jitter)
    er = round(random.uniform(0.05, 0.11) * reach_mult / 1.4, 4)
    revenue = round(avg_rev * rev_mult * jitter, 2)
    return MockResult(
        reach=reach,
        engagement_rate=er,
        revenue_attributed=revenue,
        note=f"Simulated {obj} {fmt} performance on {datetime.utcnow().date()}.",
    )


def nudge_weights(weights: Weights, post: ApprovedPost, result: MockResult) -> tuple[Weights, str]:
    """Self-improving loop: reward the objective that just performed well.

    If the published result beats the seed revenue average, bump the objective's
    business value so similar opportunities rank higher next week.
    """
    posts = load_past_posts()
    avg_rev = sum(p.metrics.revenue_attributed for p in posts) / len(posts)

    obj = post.opportunity.objective
    new = weights.model_copy(deep=True)
    before = new.obj_value.get(obj, 0.6)

    if result.revenue_attributed >= avg_rev:
        delta = 0.08
        new.obj_value[obj] = round(min(1.5, before + delta), 3)
        note = (
            f"'{obj}' beat your ${avg_rev:,.0f} average with ${result.revenue_attributed:,.0f} — "
            f"bumped its weight {before} -> {new.obj_value[obj]}. Similar ideas will rank higher next plan."
        )
    else:
        delta = 0.04
        new.obj_value[obj] = round(max(0.2, before - delta), 3)
        note = (
            f"'{obj}' underperformed your ${avg_rev:,.0f} average (${result.revenue_attributed:,.0f}) — "
            f"eased its weight {before} -> {new.obj_value[obj]}."
        )
    return new, note
