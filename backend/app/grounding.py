"""Runtime anti-hallucination guard.

The prompts *instruct* the LLM to cite only real numbers, but instruction is not
enforcement. This module is the enforcement: a deterministic pass that removes any
metric-like number from LLM prose that does not correspond to a real value in the
seed data. For a data company an AI that fabricates a metric is disqualifying, so
the guarantee lives in code, not in a system prompt.

Why numeric (not string) matching: a live model rounds and formats differently
than we do — it reads 0.1017 and writes '10.1%' (truncated) where our rollup
rounds to '10.2%', and it writes '7.2%' for an account average of 0.0715 that
Python renders as '7.1%'. Both are the SAME real number. Enumerating string forms
is brittle and wrongly strips these, leaving broken sentences ("engagement at,").
So we parse every number in the text and keep it if it is within a small epsilon
of a real value — otherwise it is fabricated and gets removed. 'AI proposes, code
disposes', extended to the digits themselves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .schemas import MetricsRollup, Opportunity, PastPost

# Matches number-like tokens: 61,200 · 10.8% · 0.094 · 7840 · 5,120.00 · 10.1%
_NUM_RE = re.compile(r"\d[\d,]*\.?\d*%?")

# A real percentage cited to 1 decimal / truncated is off by at most ~0.1; we
# allow 0.15 percentage points of slack. This comfortably covers rounding and
# truncation while still rejecting anything fabricated (max real rate here ~10.8%).
_PCT_EPS = 0.15
# Counts (reach, saves, revenue) are cited as integers; require an exact match
# after rounding, so a fabricated 999,999 can never slip through.


def _is_metricish(token: str) -> bool:
    """A token only needs grounding if it looks like a metric — it carries a
    thousands separator, a percent sign, or a decimal point. Plain integers are
    prose (counts, step numbers, weeks, "20:00" times) and are always allowed."""
    return ("," in token) or ("%" in token) or ("." in token)


@dataclass
class FactSet:
    """The real numbers, in comparable numeric form."""

    rates_pct: list[float] = field(default_factory=list)  # engagement/ctr as PERCENT (×100)
    counts: set[int] = field(default_factory=set)          # reach / saves / revenue


def _facts_from_posts(past_posts: list[PastPost]) -> FactSet:
    facts = FactSet()
    for p in past_posts:
        m = p.metrics
        facts.rates_pct.append(m.engagement_rate * 100)
        facts.rates_pct.append(m.ctr * 100)
        facts.counts.add(int(round(m.reach)))
        facts.counts.add(int(round(m.saves)))
        facts.counts.add(int(round(m.revenue_attributed)))
    return facts


def _facts_with_rollup(past_posts: list[PastPost], rollup: MetricsRollup) -> FactSet:
    """Per-post facts plus the aggregate figures the insight synthesis may cite."""
    facts = _facts_from_posts(past_posts)
    groups = (
        rollup.best_formats
        + rollup.best_themes
        + rollup.best_day_time
        + [s for stats in rollup.best_day_time_by_platform.values() for s in stats]
    )
    for stat in groups:
        # A stat value is either a rate (engagement, <1) or a count (avg reach).
        if stat.value < 1:
            facts.rates_pct.append(stat.value * 100)
        else:
            facts.counts.add(int(round(stat.value)))
    facts.rates_pct.append(rollup.avg_engagement_rate * 100)
    facts.counts.add(int(round(rollup.avg_reach)))
    return facts


def _matches_rate(value_pct: float, facts: FactSet) -> bool:
    return any(abs(value_pct - r) <= _PCT_EPS for r in facts.rates_pct)


def _token_is_grounded(token: str, facts: FactSet) -> bool:
    """True if the token is prose, or a number that corresponds to a real value."""
    norm = token.rstrip(",.")
    if not _is_metricish(norm):
        return True  # prose integer / time component — keep

    has_pct = norm.endswith("%")
    core = norm.rstrip("%").replace(",", "")
    try:
        num = float(core)
    except ValueError:
        return True  # not a number we can judge — leave it alone

    if has_pct:
        return _matches_rate(num, facts)

    # No percent sign: the figure could be a rate written raw (0.094), a percent
    # written without a sign (9.4), or a count (46,800 / 33,833).
    if num < 1 and _matches_rate(num * 100, facts):
        return True
    if _matches_rate(num, facts):
        return True
    return int(round(num)) in facts.counts


def sanitize_text(text: str, facts: FactSet) -> str:
    """Remove every fabricated metric, then tidy the leftovers so the sentence
    still reads (no dangling '$', empty parens, or stray punctuation)."""
    if not text:
        return text

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if _token_is_grounded(token, facts):
            return token
        # Fabricated: drop the number, keep any trailing sentence punctuation.
        return token[len(token.rstrip(",.")):]

    out = _NUM_RE.sub(repl, text)
    out = re.sub(r"\$(?!\d)", "", out)        # dangling currency symbol
    out = re.sub(r"\(\s*\)", "", out)          # empty parentheses
    out = re.sub(r"\s+([,.%)])", r"\1", out)  # space before punctuation
    out = re.sub(r"\s{2,}", " ", out)          # collapsed whitespace
    return out.strip()


def ground_opportunities(
    opportunities: list[Opportunity], past_posts: list[PastPost]
) -> list[Opportunity]:
    """Strip any ungrounded metric from each opportunity's rationale/angle/title.

    Runs in every mode. In MOCK_MODE the pre-baked copy is already grounded, so it
    is a no-op; against a live LLM it neutralises fabricated figures before they
    ever reach the ranker, the provenance chips, or the UI.
    """
    facts = _facts_from_posts(past_posts)
    for o in opportunities:
        o.rationale = sanitize_text(o.rationale, facts)
        o.angle = sanitize_text(o.angle, facts)
        o.title = sanitize_text(o.title, facts)
    return opportunities


def ground_synthesis(
    lines: list[str], past_posts: list[PastPost], rollup: MetricsRollup
) -> list[str]:
    """Ground the plain-English insight takeaways. Aggregate rollup figures are
    allowed here in addition to per-post metrics."""
    facts = _facts_with_rollup(past_posts, rollup)
    cleaned = [sanitize_text(line, facts) for line in lines]
    return [line for line in cleaned if line]
