// Mirrors the FastAPI Pydantic schemas (backend/app/schemas.py).

export type Objective = "Discovery" | "Trust" | "Conversion";
export type Platform = "instagram" | "tiktok";
export type PostFormat = "reel" | "carousel" | "static" | "story";

export interface LabeledStat {
  label: string;
  value: number;
  detail: string;
}

export interface MetricsRollup {
  best_formats: LabeledStat[];
  best_themes: LabeledStat[];
  best_day_time: LabeledStat[];
  best_day_time_by_platform: Record<string, LabeledStat[]>;
  top_posts_by_objective: Record<string, string[]>;
  top_posts_by_platform: Record<string, string[]>;
  avg_engagement_rate: number;
  avg_reach: number;
}

export interface Insights {
  rollup: MetricsRollup;
  synthesis: string[];
}

export interface Opportunity {
  id: string;
  title: string;
  angle: string;
  theme: string;
  audience_segment: string;
  platform: Platform;
  objective: Objective;
  format: PostFormat;
  rationale: string;
  source_post_ids: string[];
  is_amplify: boolean;
}

export interface ScoreBreakdown {
  performance_fit: number;
  audience_reach: number;
  objective_value: number;
  format_fit: number;
  novelty: number;
  effort_cost: number;
}

export interface PostedAt {
  day: string;
  time: string;
}

export interface RankedOpportunity {
  opportunity: Opportunity;
  score: number;
  breakdown: ScoreBreakdown;
  recommended_time: PostedAt;
  provenance: LabeledStat[];
}

export interface Weights {
  w_perf: number;
  w_reach: number;
  w_obj: number;
  w_fmt: number;
  w_nov: number;
  w_eff: number;
  obj_value: Record<string, number>;
}

export interface PlanResponse {
  insights: Insights;
  opportunities: RankedOpportunity[];
  weights: Weights;
}

export interface Draft {
  caption: string;
  hooks: string[];
  hashtags: string[];
  cta: string;
  image_prompt: string;
}

export interface ExemplarRef {
  post_id: string;
  angle: string;
  reason: string;
}

export interface GenerateResponse {
  draft: Draft;
  exemplars: ExemplarRef[];
  guardrail_passed: boolean;
  guardrail_notes: string;
}

export interface MockResult {
  reach: number;
  engagement_rate: number;
  revenue_attributed: number;
  note: string;
}

export interface ApprovedPost {
  id: string;
  opportunity: Opportunity;
  draft: Draft;
  slot: PostedAt;
  status: "scheduled" | "published";
  result: MockResult | null;
}

export interface CalendarResponse {
  posts: ApprovedPost[];
}

export interface FeedbackResponse {
  post: ApprovedPost;
  previous_weights: Weights;
  updated_weights: Weights;
  change_note: string;
}
