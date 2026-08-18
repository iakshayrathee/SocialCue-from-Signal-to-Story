import { useState } from "react";
import type { Weights } from "../types";
import { Button } from "./ui";

const FACTORS: { key: keyof Weights; label: string; hint: string }[] = [
  { key: "w_perf", label: "Performance fit", hint: "Similarity to past winners" },
  { key: "w_reach", label: "Audience reach", hint: "Segment size × platform fit" },
  { key: "w_obj", label: "Objective value", hint: "Business weight of the goal" },
  { key: "w_fmt", label: "Format fit", hint: "Short-form video bias" },
  { key: "w_nov", label: "Novelty", hint: "Reward fresh themes" },
  { key: "w_eff", label: "Effort cost", hint: "Penalty for expensive formats" },
];

export function WeightsDrawer({
  open,
  weights,
  onClose,
  onSave,
}: {
  open: boolean;
  weights: Weights;
  onClose: () => void;
  onSave: (w: Weights) => void;
}) {
  const [local, setLocal] = useState<Weights>(weights);

  if (!open) return null;

  const setFactor = (key: keyof Weights, value: number) =>
    setLocal((w) => ({ ...w, [key]: value }));

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/30 backdrop-blur-sm">
      <div className="fade-in h-full w-full max-w-sm overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-ink">Tune your strategy</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
            ✕
          </button>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Advanced: adjust how the engine weighs each factor when ranking ideas.
        </p>

        <div className="mt-5 space-y-5">
          {FACTORS.map((f) => (
            <div key={f.key}>
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-slate-700">{f.label}</label>
                <span className="text-xs font-mono text-brand-600">
                  {(local[f.key] as number).toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={2}
                step={0.05}
                value={local[f.key] as number}
                onChange={(e) => setFactor(f.key, parseFloat(e.target.value))}
                className="mt-1 w-full accent-brand-600"
              />
              <div className="text-[11px] text-slate-400">{f.hint}</div>
            </div>
          ))}

          <div className="rounded-xl bg-slate-50 p-3">
            <div className="text-xs font-semibold text-slate-600">
              Objective business value
            </div>
            <div className="mt-2 space-y-1 text-xs text-slate-500">
              {Object.entries(local.obj_value).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span>{k}</span>
                  <span className="font-mono text-brand-600">{v.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="mt-1 text-[11px] text-slate-400">
              These are nudged automatically by the feedback loop.
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-2">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button onClick={() => onSave(local)} className="flex-1">
            Save & re-rank
          </Button>
        </div>
      </div>
    </div>
  );
}
