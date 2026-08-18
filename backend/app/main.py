"""FastAPI app: single service that serves the built React SPA and /api/*."""
from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .data_loader import load_brand, load_past_posts, load_products
from .graph.build import build_generate_graph, build_plan_graph
from .schemas import (
    ApprovedPost,
    ApproveRequest,
    CalendarResponse,
    FeedbackRequest,
    FeedbackResponse,
    GenerateRequest,
    GenerateResponse,
    PlanResponse,
    Weights,
)
from .store import new_id, nudge_weights, simulate_result, store

settings = get_settings()
app = FastAPI(title="SocialCue", version="1.0.0")
api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mock_mode": settings.mock_mode,
        "using_real_llm": settings.use_real_llm,
    }


@api.post("/plan", response_model=PlanResponse)
def plan() -> PlanResponse:
    """Insights -> opportunities -> deterministic rank."""
    initial = {
        "brand": load_brand(),
        "products": load_products(),
        "past_posts": load_past_posts(),
        "weights": store.get_weights(),
    }
    result = build_plan_graph().invoke(initial)
    return PlanResponse(
        insights=result["insights"],
        opportunities=result["ranked"],
        weights=store.get_weights(),
    )


@api.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    """Grounded draft for a selected opportunity + guardrail check."""
    initial = {
        "brand": load_brand(),
        "products": load_products(),
        "past_posts": load_past_posts(),
        "selected": req.opportunity,
    }
    result = build_generate_graph().invoke(initial)
    return GenerateResponse(
        draft=result["draft"],
        exemplars=result.get("exemplars", []),
        guardrail_passed=result.get("guardrail_passed", True),
        guardrail_notes=result.get("guardrail_notes", ""),
    )


@api.post("/approve", response_model=ApprovedPost)
def approve(req: ApproveRequest) -> ApprovedPost:
    post = ApprovedPost(
        id=new_id("cal"),
        opportunity=req.opportunity,
        draft=req.draft,
        slot=req.slot,
        status="scheduled",
    )
    return store.add_post(post)


@api.get("/calendar", response_model=CalendarResponse)
def calendar() -> CalendarResponse:
    return CalendarResponse(posts=store.list_posts())


@api.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    post = store.get_post(req.post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")

    result = req.outcome or simulate_result(post)
    previous = store.get_weights()
    updated, note = nudge_weights(previous, post, result)
    store.set_weights(updated)

    post.status = "published"
    post.result = result
    store.add_post(post)

    return FeedbackResponse(
        post=post,
        previous_weights=previous,
        updated_weights=updated,
        change_note=note,
    )


@api.get("/weights", response_model=Weights)
def get_weights() -> Weights:
    return store.get_weights()


@api.put("/weights", response_model=Weights)
def put_weights(weights: Weights) -> Weights:
    return store.set_weights(weights)


app.include_router(api)


# --------------------------------------------------------------------------- #
# Serve the built React SPA from "/" (single service, no CORS, one URL).
# --------------------------------------------------------------------------- #
if settings.static_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=settings.static_dir / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def spa(full_path: str):  # noqa: ANN201
        # Never shadow the API.
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="not found")
        candidate = settings.static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = settings.static_dir / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="frontend not built")
