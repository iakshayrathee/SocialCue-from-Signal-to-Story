"""LangGraph state definition.

We use a TypedDict (total=False) so the same state object flows through every
node and partial updates merge cleanly across LangGraph versions.
"""
from __future__ import annotations

from typing import TypedDict

from ..schemas import (
    Brand,
    Draft,
    ExemplarRef,
    Insights,
    Opportunity,
    PastPost,
    Product,
    RankedOpportunity,
    Weights,
)


class GraphState(TypedDict, total=False):
    # Inputs
    brand: Brand
    products: list[Product]
    past_posts: list[PastPost]
    weights: Weights

    # Produced by nodes
    insights: Insights
    opportunities: list[Opportunity]
    ranked: list[RankedOpportunity]

    # Generation path
    selected: Opportunity
    exemplars: list[ExemplarRef]
    draft: Draft
    guardrail_passed: bool
    guardrail_notes: str
