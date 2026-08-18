import type {
  ApprovedPost,
  CalendarResponse,
  Draft,
  FeedbackResponse,
  GenerateResponse,
  Opportunity,
  PlanResponse,
  PostedAt,
  Weights,
} from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => req<{ status: string; mock_mode: boolean; using_real_llm: boolean }>("/health"),

  plan: () => req<PlanResponse>("/plan", { method: "POST", body: "{}" }),

  generate: (opportunity: Opportunity) =>
    req<GenerateResponse>("/generate", {
      method: "POST",
      body: JSON.stringify({ opportunity }),
    }),

  approve: (opportunity: Opportunity, draft: Draft, slot: PostedAt) =>
    req<ApprovedPost>("/approve", {
      method: "POST",
      body: JSON.stringify({ opportunity, draft, slot }),
    }),

  calendar: () => req<CalendarResponse>("/calendar"),

  feedback: (postId: string) =>
    req<FeedbackResponse>("/feedback", {
      method: "POST",
      body: JSON.stringify({ post_id: postId }),
    }),

  getWeights: () => req<Weights>("/weights"),

  putWeights: (weights: Weights) =>
    req<Weights>("/weights", { method: "PUT", body: JSON.stringify(weights) }),
};
