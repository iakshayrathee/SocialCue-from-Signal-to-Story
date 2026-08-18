import { useEffect, useState } from "react";
import { api } from "./api";
import { DraftView } from "./components/DraftView";
import { OpportunityCard } from "./components/OpportunityCard";
import { WeekCalendar } from "./components/WeekCalendar";
import { WeightsDrawer } from "./components/WeightsDrawer";
import { Button, Spinner } from "./components/ui";
import type {
  ApprovedPost,
  Draft,
  GenerateResponse,
  Insights,
  PlanResponse,
  PostedAt,
  RankedOpportunity,
  Weights,
} from "./types";

export default function App() {
  const [planning, setPlanning] = useState(false);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [weights, setWeights] = useState<Weights | null>(null);

  const [selected, setSelected] = useState<RankedOpportunity | null>(null);
  const [generated, setGenerated] = useState<GenerateResponse | null>(null);
  const [drafting, setDrafting] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  const [calendar, setCalendar] = useState<ApprovedPost[]>([]);
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const [toast, setToast] = useState<string | null>(null);
  const [mockMode, setMockMode] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then((h) => setMockMode(h.mock_mode)).catch(() => setMockMode(null));
    refreshCalendar();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 6000);
    return () => clearTimeout(t);
  }, [toast]);

  async function refreshCalendar() {
    try {
      const c = await api.calendar();
      setCalendar(c.posts);
    } catch {
      /* ignore */
    }
  }

  async function runPlan() {
    setPlanning(true);
    setError(null);
    try {
      const p = await api.plan();
      setPlan(p);
      setInsights(p.insights);
      setWeights(p.weights);
    } catch (e) {
      setError(String(e));
    } finally {
      setPlanning(false);
    }
  }

  async function draftThis(ranked: RankedOpportunity) {
    setDrafting(ranked.opportunity.id);
    setError(null);
    try {
      const g = await api.generate(ranked.opportunity);
      setSelected(ranked);
      setGenerated(g);
    } catch (e) {
      setError(String(e));
    } finally {
      setDrafting(null);
    }
  }

  async function approve(draft: Draft, slot: PostedAt) {
    if (!selected) return;
    setApproving(true);
    try {
      await api.approve(selected.opportunity, draft, slot);
      await refreshCalendar();
      setSelected(null);
      setGenerated(null);
      setToast(`Scheduled for ${slot.day} ${slot.time}.`);
    } catch (e) {
      setError(String(e));
    } finally {
      setApproving(false);
    }
  }

  async function publish(id: string) {
    setPublishingId(id);
    try {
      const fb = await api.feedback(id);
      setWeights(fb.updated_weights);
      await refreshCalendar();
      setToast(`📈 Learning applied — ${fb.change_note}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setPublishingId(null);
    }
  }

  async function saveWeights(w: Weights) {
    try {
      const saved = await api.putWeights(w);
      setWeights(saved);
      setDrawerOpen(false);
      // Re-rank with the new weights if we already have a plan.
      if (plan) await runPlan();
      setToast("Strategy updated and ideas re-ranked.");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="min-h-screen">
      <Header
        mockMode={mockMode}
        onTune={() => weights && setDrawerOpen(true)}
        canTune={!!weights}
      />

      <main className="mx-auto max-w-6xl px-4 pb-24">
        {/* Hero / primary action */}
        {!plan && (
          <section className="fade-in mx-auto mt-10 max-w-2xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
              Decision engine · not a caption generator
            </div>
            <h1 className="mt-4 text-4xl font-extrabold leading-tight text-ink sm:text-5xl">
              Know what to post,
              <br /> and <span className="text-brand-600">exactly why.</span>
            </h1>
            <p className="mx-auto mt-4 max-w-lg text-slate-500">
              SocialCue reads your brand's own post performance, ranks the
              highest-value content opportunities, and explains every call with
              real numbers. Generation comes after the decision.
            </p>
            <div className="mt-8">
              <Button onClick={runPlan} disabled={planning} className="!px-6 !py-3 text-base">
                {planning ? (
                  <>
                    <Spinner /> Reading your data…
                  </>
                ) : (
                  "Plan my week →"
                )}
              </Button>
            </div>
          </section>
        )}

        {error && (
          <div className="mx-auto mt-6 max-w-2xl rounded-xl bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-100">
            {error}
          </div>
        )}

        {plan && insights && (
          <>
            <InsightsBar insights={insights} onReplan={runPlan} planning={planning} />

            <section className="mt-8">
              <h2 className="mb-1 text-xl font-bold text-ink">This week's opportunities</h2>
              <p className="mb-4 text-sm text-slate-500">
                Ranked by predicted value. Open “Show the proof” to see the data behind each call.
              </p>
              <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
                {plan.opportunities.map((r, i) => (
                  <OpportunityCard
                    key={r.opportunity.id}
                    ranked={r}
                    rank={i + 1}
                    maxScore={plan.opportunities[0]?.score ?? r.score}
                    drafting={drafting === r.opportunity.id}
                    onDraft={() => draftThis(r)}
                  />
                ))}
              </div>
            </section>

            <section className="mt-12">
              <div className="mb-4 flex items-end justify-between">
                <div>
                  <h2 className="text-xl font-bold text-ink">Your week</h2>
                  <p className="text-sm text-slate-500">
                    Approved posts at their data-recommended times. Mark one published to watch the engine learn.
                  </p>
                </div>
              </div>
              <WeekCalendar
                posts={calendar}
                onPublish={publish}
                publishingId={publishingId}
              />
            </section>
          </>
        )}
      </main>

      {selected && generated && (
        <DraftView
          ranked={selected}
          generated={generated}
          approving={approving}
          onApprove={approve}
          onClose={() => {
            setSelected(null);
            setGenerated(null);
          }}
        />
      )}

      {weights && (
        <WeightsDrawer
          open={drawerOpen}
          weights={weights}
          onClose={() => setDrawerOpen(false)}
          onSave={saveWeights}
        />
      )}

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 max-w-md -translate-x-1/2 fade-in">
          <div className="rounded-xl bg-ink px-4 py-3 text-sm text-white shadow-2xl">
            {toast}
          </div>
        </div>
      )}
    </div>
  );
}

function Header({
  mockMode,
  onTune,
  canTune,
}: {
  mockMode: boolean | null;
  onTune: () => void;
  canTune: boolean;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/70 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-brand-600 text-sm font-black text-white">
            SC
          </div>
          <div>
            <div className="text-sm font-bold leading-none text-ink">SocialCue</div>
            <div className="text-[11px] text-slate-400">Know what to post next</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {mockMode !== null && (
            <span
              className={
                "rounded-full px-2.5 py-1 text-[11px] font-semibold " +
                (mockMode ? "bg-slate-100 text-slate-500" : "bg-emerald-50 text-emerald-600")
              }
            >
              {mockMode ? "Mock mode" : "Live AI"}
            </span>
          )}
          {canTune && (
            <button
              onClick={onTune}
              className="text-xs font-semibold text-slate-500 hover:text-brand-600"
            >
              ⚙ Advanced
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

function InsightsBar({
  insights,
  onReplan,
  planning,
}: {
  insights: Insights;
  onReplan: () => void;
  planning: boolean;
}) {
  return (
    <section className="mt-6 rounded-2xl border border-slate-100 bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            What your data says
          </div>
          <ul className="mt-2 space-y-1.5">
            {insights.synthesis.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-brand-500">✦</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
        <Button variant="soft" onClick={onReplan} disabled={planning}>
          {planning ? "…" : "↻ Replan"}
        </Button>
      </div>
    </section>
  );
}
