import { useState } from "react";
import type { Draft, GenerateResponse, PostedAt, RankedOpportunity } from "../types";
import { Button, Chip, platformLabel } from "./ui";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function DraftView({
  ranked,
  generated,
  onApprove,
  onClose,
  approving,
}: {
  ranked: RankedOpportunity;
  generated: GenerateResponse;
  onApprove: (draft: Draft, slot: PostedAt) => void;
  onClose: () => void;
  approving: boolean;
}) {
  const o = ranked.opportunity;
  const [draft, setDraft] = useState<Draft>(generated.draft);
  const [slot, setSlot] = useState<PostedAt>(ranked.recommended_time);

  const update = (patch: Partial<Draft>) => setDraft((d) => ({ ...d, ...patch }));

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-ink/40 p-4 backdrop-blur-sm">
      <div className="fade-in my-8 w-full max-w-2xl rounded-2xl bg-white shadow-2xl">
        {/* header */}
        <div className="flex items-start justify-between border-b border-slate-100 p-5">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-brand-600">
              {platformLabel(o.platform)} · {o.format} · {o.objective}
            </div>
            <h2 className="mt-1 text-lg font-bold text-ink">{o.title}</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
            ✕
          </button>
        </div>

        <div className="space-y-4 p-5">
          {/* grounding */}
          <div className="rounded-xl bg-brand-50 p-3">
            <div className="text-xs font-semibold text-brand-700">
              🎯 Grounded in your proven winners
            </div>
            <div className="mt-2 space-y-1">
              {generated.exemplars.map((e) => (
                <div key={e.post_id} className="text-xs text-slate-600">
                  <span className="font-mono text-[10px] text-slate-500">{e.post_id}</span>{" "}
                  — {e.angle} <span className="text-slate-400">({e.reason})</span>
                </div>
              ))}
            </div>
          </div>

          {/* guardrail */}
          <div className="flex items-center gap-2 text-xs">
            <Chip tone={generated.guardrail_passed ? "indigo" : "rose"}>
              {generated.guardrail_passed ? "✓ Tone check passed" : "⚠ Tone check"}
            </Chip>
            <span className="text-slate-500">{generated.guardrail_notes}</span>
          </div>

          {/* editable fields */}
          <Field label="Caption">
            <textarea
              value={draft.caption}
              onChange={(e) => update({ caption: e.target.value })}
              rows={4}
              className="w-full resize-none rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            />
          </Field>

          <Field label="Hooks">
            <div className="space-y-1.5">
              {draft.hooks.map((h, i) => (
                <input
                  key={i}
                  value={h}
                  onChange={(e) => {
                    const hooks = [...draft.hooks];
                    hooks[i] = e.target.value;
                    update({ hooks });
                  }}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
                />
              ))}
            </div>
          </Field>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Hashtags">
              <input
                value={draft.hashtags.join(" ")}
                onChange={(e) => update({ hashtags: e.target.value.split(/\s+/).filter(Boolean) })}
                className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
              />
            </Field>
            <Field label="Call to action">
              <input
                value={draft.cta}
                onChange={(e) => update({ cta: e.target.value })}
                className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
              />
            </Field>
          </div>

          <Field label="Image prompt (for your designer or an image model)">
            <textarea
              value={draft.image_prompt}
              onChange={(e) => update({ image_prompt: e.target.value })}
              rows={2}
              className="w-full resize-none rounded-xl border border-slate-200 p-3 text-sm text-slate-600 focus:border-brand-400 focus:outline-none"
            />
          </Field>

          {/* Schedule — pre-filled with the data-recommended slot, editable */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Schedule
              </label>
              {(slot.day !== ranked.recommended_time.day ||
                slot.time !== ranked.recommended_time.time) && (
                <button
                  onClick={() => setSlot(ranked.recommended_time)}
                  className="text-[11px] font-semibold text-brand-600 hover:text-brand-700"
                >
                  ↺ Reset to recommended
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <select
                value={slot.day}
                onChange={(e) => setSlot((s) => ({ ...s, day: e.target.value }))}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
              >
                {DAYS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <input
                type="time"
                value={slot.time}
                onChange={(e) => setSlot((s) => ({ ...s, time: e.target.value }))}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>
            <div className="mt-1.5 text-[11px] text-slate-400">
              Recommended from your {platformLabel(o.platform)} history:{" "}
              <span className="font-semibold text-slate-500">
                {ranked.recommended_time.day} {ranked.recommended_time.time}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 p-5">
          <span className="text-xs text-slate-400">
            Will schedule for{" "}
            <span className="font-semibold text-slate-600">
              {slot.day} {slot.time}
            </span>
          </span>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={() => onApprove(draft, slot)} disabled={approving}>
              {approving ? "Scheduling…" : "Approve & schedule →"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </label>
      {children}
    </div>
  );
}
