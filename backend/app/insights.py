"""Deterministic metric rollups computed in Python from the seed data.

These are the ONLY numbers allowed into prompts. The LLM may reference them but
never invent its own. This is the anti-hallucination backbone.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from .schemas import LabeledStat, MetricsRollup, PastPost


def _avg_er_by(posts: list[PastPost], key) -> list[LabeledStat]:
    groups: dict[str, list[float]] = defaultdict(list)
    for p in posts:
        groups[key(p)].append(p.metrics.engagement_rate)
    stats = [
        LabeledStat(
            label=label,
            value=round(mean(vals), 4),
            detail=f"avg engagement across {len(vals)} post(s)",
        )
        for label, vals in groups.items()
    ]
    stats.sort(key=lambda s: s.value, reverse=True)
    return stats


def _best_day_time(posts: list[PastPost]) -> list[LabeledStat]:
    by_day: dict[str, list[PastPost]] = defaultdict(list)
    for p in posts:
        by_day[p.posted_at.day].append(p)

    stats: list[LabeledStat] = []
    for day, day_posts in by_day.items():
        avg_er = mean(pp.metrics.engagement_rate for pp in day_posts)
        # Representative time = the best-performing post's time on that day.
        best_post = max(day_posts, key=lambda pp: pp.metrics.engagement_rate)
        stats.append(
            LabeledStat(
                label=f"{day} {best_post.posted_at.time}",
                value=round(avg_er, 4),
                detail=(
                    f"{day} avg engagement {avg_er:.1%} "
                    f"across {len(day_posts)} post(s); top slot {best_post.posted_at.time}"
                ),
            )
        )
    stats.sort(key=lambda s: s.value, reverse=True)
    return stats


def _best_day_time_by_platform(posts: list[PastPost]) -> dict[str, list[LabeledStat]]:
    by_plat: dict[str, list[PastPost]] = defaultdict(list)
    for p in posts:
        by_plat[p.platform].append(p)
    return {plat: _best_day_time(items) for plat, items in by_plat.items()}


def _top_ids(posts: list[PastPost], group_key, n: int = 3) -> dict[str, list[str]]:
    groups: dict[str, list[PastPost]] = defaultdict(list)
    for p in posts:
        groups[group_key(p)].append(p)
    out: dict[str, list[str]] = {}
    for key, items in groups.items():
        items.sort(key=lambda pp: pp.metrics.engagement_rate, reverse=True)
        out[key] = [pp.id for pp in items[:n]]
    return out


def compute_rollup(posts: list[PastPost]) -> MetricsRollup:
    return MetricsRollup(
        best_formats=_avg_er_by(posts, lambda p: p.format),
        best_themes=_avg_er_by(posts, lambda p: p.theme),
        best_day_time=_best_day_time(posts),
        best_day_time_by_platform=_best_day_time_by_platform(posts),
        top_posts_by_objective=_top_ids(posts, lambda p: p.objective),
        top_posts_by_platform=_top_ids(posts, lambda p: p.platform),
        avg_engagement_rate=round(mean(p.metrics.engagement_rate for p in posts), 4),
        avg_reach=round(mean(p.metrics.reach for p in posts), 1),
    )
