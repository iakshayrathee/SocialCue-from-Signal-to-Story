"""Assemble the LangGraph state graph.

The full decision pipeline is:

    extract_insights -> generate_opportunities -> score_and_rank
        -> (human selects) -> generate_content -> guardrail_check
        -> (human approves) -> log_feedback -> (edge back into score_and_rank)

Because HTTP calls are stateless and the frontend holds the plan/selection, we
compile two runnable sub-pipelines: PLAN (insights -> opportunities -> rank) and
GENERATE (content -> guardrail). The feedback edge is realised at the API layer
by nudging the weights that feed the next PLAN run. LangGraph composes each
pipeline as an explicit node/edge graph.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes import (
    extract_insights,
    generate_content,
    generate_opportunities,
    guardrail_check,
    score_and_rank,
)
from .state import GraphState


@lru_cache(maxsize=1)
def build_plan_graph():
    g = StateGraph(GraphState)
    g.add_node("extract_insights", extract_insights)
    g.add_node("generate_opportunities", generate_opportunities)
    g.add_node("score_and_rank", score_and_rank)
    g.add_edge(START, "extract_insights")
    g.add_edge("extract_insights", "generate_opportunities")
    g.add_edge("generate_opportunities", "score_and_rank")
    g.add_edge("score_and_rank", END)
    return g.compile()


@lru_cache(maxsize=1)
def build_generate_graph():
    g = StateGraph(GraphState)
    g.add_node("generate_content", generate_content)
    g.add_node("guardrail_check", guardrail_check)
    g.add_edge(START, "generate_content")
    g.add_edge("generate_content", "guardrail_check")
    g.add_edge("guardrail_check", END)
    return g.compile()
