import type { ApprovedPost } from "../types";
import { Button, Chip, ObjectiveBadge, platformLabel } from "./ui";

export function PostDetail({
  post,
  onClose,
  onPublish,
  publishing,
}: {
  post: ApprovedPost;
  onClose: () => void;
  onPublish?: (id: string) => void;
  publishing?: boolean;
}) {
  const o = post.opportunity;
  const d = post.draft;
  const published = post.status === "published";

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-ink/40 p-4 backdrop-blur-sm">
      <div className="fade-in my-8 w-full max-w-2xl rounded-2xl bg-white shadow-2xl">
        {/* header */}
        <div className="flex items-start justify-between border-b border-slate-100 p-5">
          <div>
            <div className="flex items-center gap-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                {platformLabel(o.platform)} · {o.format}
              </div>
              <ObjectiveBadge objective={o.objective} className="!px-2 text-[10px]" />
              <Chip tone={published ? "indigo" : "slate"}>
                {published ? "✓ Published" : "Scheduled"}
              </Chip>
            </div>
            <h2 className="mt-1 text-lg font-bold text-ink">{o.title}</h2>
            <div className="mt-0.5 text-xs text-slate-400">
              {post.slot.day} · {post.slot.time}
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
            ✕
          </button>
        </div>

        <div className="space-y-4 p-5">
          {/* published result */}
          {published && post.result && (
            <div className="rounded-xl bg-emerald-50 p-3 ring-1 ring-emerald-100">
              <div className="text-xs font-semibold text-emerald-700">📈 Published result</div>
              <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                <Metric label="Reach" value={post.result.reach.toLocaleString()} />
                <Metric
                  label="Engagement"
                  value={`${(post.result.engagement_rate * 100).toFixed(1)}%`}
                />
                <Metric
                  label="Revenue"
                  value={`$${post.result.revenue_attributed.toLocaleString()}`}
                />
              </div>
            </div>
          )}

          {/* content */}
          <Field label="Caption">
            <p className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50/60 p-3 text-sm text-slate-700">
              {d.caption}
            </p>
          </Field>

          {d.hooks.length > 0 && (
            <Field label="Hooks">
              <ul className="space-y-1.5">
                {d.hooks.map((h, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700"
                  >
                    {h}
                  </li>
                ))}
              </ul>
            </Field>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {d.hashtags.length > 0 && (
              <Field label="Hashtags">
                <div className="flex flex-wrap gap-1.5">
                  {d.hashtags.map((h, i) => (
                    <span
                      key={i}
                      className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              </Field>
            )}
            <Field label="Call to action">
              <p className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700">
                {d.cta}
              </p>
            </Field>
          </div>

          {d.image_prompt && (
            <Field label="Image prompt">
              <p className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50/60 p-3 text-sm text-slate-600">
                {d.image_prompt}
              </p>
            </Field>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 p-5">
          <span className="text-xs text-slate-400">
            {published
              ? "This post has been published."
              : `Scheduled for ${post.slot.day} ${post.slot.time}.`}
          </span>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
            {!published && onPublish && (
              <Button onClick={() => onPublish(post.id)} disabled={publishing}>
                {publishing ? "Simulating…" : "Mark published"}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/80 py-2">
      <div className="text-sm font-bold text-emerald-700">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-emerald-600/70">{label}</div>
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
