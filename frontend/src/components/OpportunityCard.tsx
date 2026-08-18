import { useState } from "react";
import type { RankedOpportunity } from "../types";
import {
  Button,
  Chip,
  ConfidenceChip,
  ObjectiveBadge,
  cx,
  platformLabel,
} from "./ui";

export function OpportunityCard({
  ranked,
  rank,
  maxScore,
  onDraft,
  drafting,
}: {
  ranked: RankedOpportunity;
  rank: number;
  maxScore: number;
  onDraft: () => void;
  drafting: boolean;
}) {
  const [showProof, setShowProof] = useState(false);
  const o = ranked.opportunity;

  return (
    <div
      className={cx(
        "fade-in flex flex-col rounded-2xl border bg-white p-5 shadow-card transition hover:shadow-lg",
        o.is_amplify ? "border-amber-200 ring-1 ring-amber-100" : "border-slate-100",
      )}
    >
      {/* Header: rank + badges + confidence */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-900 text-xs font-bold text-white">
            {rank}
          </span>
          {o.is_amplify && <Chip tone="rose">♻ Amplify a winner</Chip>}
          <ObjectiveBadge objective={o.objective} />
        </div>
        <ConfidenceChip score={ranked.score} maxScore={maxScore} />
      </div>

      {/* Title + angle: reserved height so every card matches when collapsed */}
      <h3 className="line-clamp-2 min-h-[2.9rem] text-[17px] font-bold leading-snug text-ink">
        {o.title}
      </h3>
      <p className="mt-1 line-clamp-1 min-h-[1.25rem] text-sm text-slate-500">{o.angle}</p>

      {/* Why now */}
      <div className="mt-3 rounded-xl bg-slate-50 p-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Why now
        </div>
        <p
          className={cx(
            "mt-1 text-sm text-slate-700",
            showProof ? "" : "line-clamp-3 min-h-[3.9rem]",
          )}
        >
          {o.rationale}
        </p>
        <button
          onClick={() => setShowProof((s) => !s)}
          className="mt-2 text-xs font-semibold text-brand-600 hover:text-brand-700"
        >
          {showProof ? "Hide the proof" : "Show the proof →"}
        </button>
        {showProof && (
          <div className="mt-2 space-y-1.5 border-t border-slate-200 pt-2 fade-in">
            {ranked.provenance.map((p, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                <span className="mt-0.5 text-brand-500">•</span>
                <span>
                  <span className="font-semibold">{p.label}:</span> {p.detail}
                </span>
              </div>
            ))}
            {o.source_post_ids.length > 0 && (
              <div className="pt-1 text-xs text-slate-500">
                Grounded in past posts:{" "}
                {o.source_post_ids.map((id) => (
                  <span
                    key={id}
                    className="mr-1 rounded bg-white px-1.5 py-0.5 font-mono text-[10px] text-slate-500 ring-1 ring-slate-200"
                  >
                    {id}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Meta row: reserved height for consistent card shape */}
      <div className="mt-3 grid grid-cols-2 gap-y-1.5 text-xs text-slate-500">
        <span className="truncate" title={o.audience_segment}>
          👤 {o.audience_segment}
        </span>
        <span>📱 {platformLabel(o.platform)}</span>
        <span className="capitalize">🎬 {o.format}</span>
        <span>
          🕒 <span className="font-semibold text-slate-700">{ranked.recommended_time.day} {ranked.recommended_time.time}</span>
        </span>
      </div>

      {/* Footer pinned to the bottom so all cards align */}
      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
        <span className="text-xs text-slate-400">Best time to post</span>
        <Button onClick={onDraft} disabled={drafting} variant="primary">
          {drafting ? "Drafting…" : "Draft this ✨"}
        </Button>
      </div>
    </div>
  );
}
