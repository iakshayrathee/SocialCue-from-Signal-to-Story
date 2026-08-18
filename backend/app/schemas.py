"""Pydantic v2 models: the typed contract for every AI I/O and API boundary."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Objective = Literal["Discovery", "Trust", "Conversion"]
Platform = Literal["instagram", "tiktok"]
PostFormat = Literal["reel", "carousel", "static", "story"]


# --------------------------------------------------------------------------- #
# Seed data models
# --------------------------------------------------------------------------- #
class ToneOfVoice(BaseModel):
    adjectives: list[str]
    do: list[str]
    dont: list[str]


class AudienceSegment(BaseModel):
    name: str
    description: str
    size_proxy: int


class Brand(BaseModel):
    name: str
    description: str
    tone_of_voice: ToneOfVoice
    target_audience: list[AudienceSegment]


class Product(BaseModel):
    id: str
    name: str
    description: str
    key_benefits: list[str]
    price: float
    tags: list[str]


class PostedAt(BaseModel):
    day: str
    time: str  # "HH:MM" 24h


class PostMetrics(BaseModel):
    reach: int
    engagement_rate: float
    saves: int
    ctr: float
    revenue_attributed: float


class PastPost(BaseModel):
    id: str
    platform: Platform
    format: PostFormat
    theme: str
    angle: str
    objective: Objective
    caption: str
    posted_at: PostedAt
    metrics: PostMetrics


# --------------------------------------------------------------------------- #
# Insights (metric rollups + LLM synthesis)
# --------------------------------------------------------------------------- #
class LabeledStat(BaseModel):
    label: str
    value: float
    detail: str = ""


class MetricsRollup(BaseModel):
    """Everything computed deterministically in Python from the seed data."""

    best_formats: list[LabeledStat]
    best_themes: list[LabeledStat]
    best_day_time: list[LabeledStat]
    # Best day/time buckets computed per platform, so recommended timing is
    # specific to where the post will actually run.
    best_day_time_by_platform: dict[str, list[LabeledStat]] = Field(default_factory=dict)
    top_posts_by_objective: dict[str, list[str]]  # objective -> post ids
    top_posts_by_platform: dict[str, list[str]]  # platform -> post ids
    avg_engagement_rate: float
    avg_reach: float


class Insights(BaseModel):
    rollup: MetricsRollup
    synthesis: list[str] = Field(
        default_factory=list,
        description="Short plain-English takeaways that reference ONLY computed numbers.",
    )


# --------------------------------------------------------------------------- #
# Opportunities + scoring
# --------------------------------------------------------------------------- #
class Opportunity(BaseModel):
    id: str
    title: str
    angle: str
    theme: str = ""
    audience_segment: str
    platform: Platform
    objective: Objective
    format: PostFormat
    rationale: str
    source_post_ids: list[str] = Field(default_factory=list)
    is_amplify: bool = False


class ScoreBreakdown(BaseModel):
    performance_fit: float
    audience_reach: float
    objective_value: float
    format_fit: float
    novelty: float
    effort_cost: float


class RankedOpportunity(BaseModel):
    opportunity: Opportunity
    score: float
    breakdown: ScoreBreakdown
    recommended_time: PostedAt
    provenance: list[LabeledStat] = Field(
        default_factory=list,
        description="Exact stats/post ids that justify this recommendation.",
    )


class Weights(BaseModel):
    w_perf: float = 1.0
    w_reach: float = 0.8
    w_obj: float = 1.0
    w_fmt: float = 0.7
    w_nov: float = 0.5
    w_eff: float = 0.6
    # Per-objective business value (tuned by the feedback loop).
    obj_value: dict[str, float] = Field(
        default_factory=lambda: {"Discovery": 0.6, "Trust": 0.8, "Conversion": 1.0}
    )


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
class Draft(BaseModel):
    caption: str
    hooks: list[str]
    hashtags: list[str]
    cta: str
    image_prompt: str


class ExemplarRef(BaseModel):
    post_id: str
    angle: str
    reason: str


# --------------------------------------------------------------------------- #
# API request/response bodies
# --------------------------------------------------------------------------- #
class PlanResponse(BaseModel):
    insights: Insights
    opportunities: list[RankedOpportunity]
    weights: Weights


class GenerateRequest(BaseModel):
    opportunity: Opportunity


class GenerateResponse(BaseModel):
    draft: Draft
    exemplars: list[ExemplarRef]
    guardrail_passed: bool
    guardrail_notes: str = ""


class ApproveRequest(BaseModel):
    opportunity: Opportunity
    draft: Draft
    slot: PostedAt


class ApprovedPost(BaseModel):
    id: str
    opportunity: Opportunity
    draft: Draft
    slot: PostedAt
    status: Literal["scheduled", "published"] = "scheduled"
    result: Optional["MockResult"] = None


class MockResult(BaseModel):
    reach: int
    engagement_rate: float
    revenue_attributed: float
    note: str = ""


class CalendarResponse(BaseModel):
    posts: list[ApprovedPost]


class FeedbackRequest(BaseModel):
    post_id: str
    # Optional explicit outcome; if omitted the backend simulates a plausible one.
    outcome: Optional[MockResult] = None


class FeedbackResponse(BaseModel):
    post: ApprovedPost
    previous_weights: Weights
    updated_weights: Weights
    change_note: str


ApprovedPost.model_rebuild()
