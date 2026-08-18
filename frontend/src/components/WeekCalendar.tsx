import type { ApprovedPost } from "../types";
import { Button, ObjectiveBadge, cx, platformLabel } from "./ui";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function WeekCalendar({
  posts,
  onPublish,
  publishingId,
}: {
  posts: ApprovedPost[];
  onPublish: (id: string) => void;
  publishingId: string | null;
}) {
  const byDay: Record<string, ApprovedPost[]> = {};
  for (const d of DAYS) byDay[d] = [];
  for (const p of posts) {
    (byDay[p.slot.day] ??= []).push(p);
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-7">
      {DAYS.map((day) => (
        <div key={day} className="rounded-2xl border border-slate-100 bg-white/70 p-3">
          <div className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">
            {day.slice(0, 3)}
          </div>
          <div className="space-y-2">
            {byDay[day].length === 0 && (
              <div className="rounded-lg border border-dashed border-slate-200 py-6 text-center text-[11px] text-slate-300">
                —
              </div>
            )}
            {byDay[day]
              .sort((a, b) => a.slot.time.localeCompare(b.slot.time))
              .map((p) => (
                <CalendarCard
                  key={p.id}
                  post={p}
                  onPublish={() => onPublish(p.id)}
                  publishing={publishingId === p.id}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CalendarCard({
  post,
  onPublish,
  publishing,
}: {
  post: ApprovedPost;
  onPublish: () => void;
  publishing: boolean;
}) {
  const published = post.status === "published";
  return (
    <div
      className={cx(
        "fade-in rounded-xl border p-2.5 text-left",
        published ? "border-emerald-200 bg-emerald-50/60" : "border-slate-200 bg-white",
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-slate-500">{post.slot.time}</span>
        <ObjectiveBadge objective={post.opportunity.objective} />
      </div>
      <div className="mt-1 line-clamp-2 text-xs font-semibold text-ink">
        {post.opportunity.title}
      </div>
      <div className="mt-1 text-[10px] text-slate-400">
        {platformLabel(post.opportunity.platform)} · {post.opportunity.format}
      </div>

      {published && post.result ? (
        <div className="mt-2 rounded-lg bg-white/80 p-1.5 text-[10px] text-emerald-700 ring-1 ring-emerald-100">
          ✓ Published · {post.result.reach.toLocaleString()} reach ·{" "}
          ${post.result.revenue_attributed.toLocaleString()} rev
        </div>
      ) : (
        <Button
          variant="soft"
          onClick={onPublish}
          disabled={publishing}
          className="mt-2 w-full !px-2 !py-1 text-[11px]"
        >
          {publishing ? "Simulating…" : "Mark published"}
        </Button>
      )}
    </div>
  );
}
