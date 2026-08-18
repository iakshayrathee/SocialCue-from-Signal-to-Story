"""Pre-baked, realistic LLM outputs for MOCK_MODE.

Everything here is written to be consistent with the seed data so the full flow
runs end-to-end with zero API key and zero cost. Rationales reference only
numbers that actually exist in past_posts.json.
"""
from __future__ import annotations

from .schemas import Brand, Draft, Opportunity, PastPost, Product


def mock_synthesis(brand: Brand, rollup) -> list[str]:
    """Plain-English takeaways that cite only computed rollup numbers."""
    lines: list[str] = []
    if rollup.best_formats:
        top = rollup.best_formats[0]
        lines.append(
            f"Your {top.label} posts average {top.value:.1%} engagement — the "
            f"strongest format, well above your {rollup.avg_engagement_rate:.1%} account average."
        )
    if rollup.best_themes:
        t = rollup.best_themes[0]
        lines.append(
            f"'{t.label}' is your best-performing theme at {t.value:.1%} average engagement."
        )
    if rollup.best_day_time_by_platform:
        # Timing is platform-specific — say so, so it matches the per-card
        # recommended times (which are computed per platform).
        parts = []
        for platform, buckets in rollup.best_day_time_by_platform.items():
            if buckets:
                label = platform.replace("tiktok", "TikTok").replace("instagram", "Instagram")
                parts.append(f"{label} peaks {buckets[0].label} ({buckets[0].value:.1%})")
        if parts:
            lines.append("Best posting time is platform-specific: " + "; ".join(parts) + ".")
    elif rollup.best_day_time:
        d = rollup.best_day_time[0]
        lines.append(f"{d.label} is your best slot — {d.detail}.")
    lines.append(
        f"Static product shots trail badly; lean into short-form video against your "
        f"{rollup.avg_reach:,.0f} average reach."
    )
    return lines


def mock_opportunities(
    brand: Brand,
    products: list[Product],
    past_posts: list[PastPost],
) -> list[Opportunity]:
    seg = {s.name for s in brand.target_audience}
    optimizers = "Routine Optimizers" if "Routine Optimizers" in seg else next(iter(seg))
    minimalists = "Conscious Minimalists" if "Conscious Minimalists" in seg else optimizers
    firsttimers = "Curious First-Timers" if "Curious First-Timers" in seg else optimizers

    return [
        Opportunity(
            id="opp_amplify_beforeafter",
            title="Amplify your top converter: re-run the 8-week barrier before/after",
            angle="Fresh cut of the 8-week Barrier Serum transformation with a new customer and a bolder hook",
            theme="before-after",
            audience_segment=optimizers,
            platform="tiktok",
            objective="Conversion",
            format="reel",
            rationale="post_008 drove the highest revenue of any post ($7,840) at 9.9% engagement and a 5.2% CTR. Re-running a proven winner with a new face is the cheapest high-confidence bet this week.",
            source_post_ids=["post_008"],
            is_amplify=True,
        ),
        Opportunity(
            id="opp_bts_refill",
            title="Behind-the-scenes: refill day, packed by hand",
            angle="Fly-on-the-wall of refill pods being packed, tying less-waste to the sustainability promise",
            theme="behind-the-scenes",
            audience_segment=minimalists,
            platform="tiktok",
            objective="Trust",
            format="reel",
            rationale="Behind-the-scenes reels are your standout theme — post_002 hit 61,200 reach and 10.8% engagement, post_014 hit 57,400 reach. This format compounds trust with the sustainability audience.",
            source_post_ids=["post_002", "post_014", "post_001"],
        ),
        Opportunity(
            id="opp_ugc_startset",
            title="Repost a customer unboxing of the Simple Start Set",
            angle="Duet/stitch a customer's unboxing as social proof for first-timers",
            theme="ugc",
            audience_segment=firsttimers,
            platform="instagram",
            objective="Conversion",
            format="reel",
            rationale="post_015 (customer unboxing) reached 46,800 with 9.5% engagement and $6,920 attributed revenue. UGC converts first-timers who need reassurance.",
            source_post_ids=["post_015"],
        ),
        Opportunity(
            id="opp_founder_story",
            title="Founder story: the barrier damage that started Lumen",
            angle="Short, honest founder reel connecting personal history to the Barrier Serum",
            theme="founder-story",
            audience_segment=minimalists,
            platform="instagram",
            objective="Trust",
            format="reel",
            rationale="post_009 (founder story) reached 44,100 at 9.1% engagement, proving personal narrative builds trust for this brand.",
            source_post_ids=["post_009"],
        ),
        Opportunity(
            id="opp_barrier_explainer",
            title="Carousel: your skin barrier, explained without jargon",
            angle="Save-worthy educational carousel on barrier repair and where the serum fits",
            theme="education",
            audience_segment=optimizers,
            platform="instagram",
            objective="Trust",
            format="carousel",
            rationale="Educational posts earn heavy saves — post_004 collected 2,180 saves and post_017 collected 1,980, signalling reference value that keeps the brand top-of-mind.",
            source_post_ids=["post_004", "post_017"],
        ),
        Opportunity(
            id="opp_spf_myths",
            title="Carousel: 3 SPF myths that won't die",
            angle="Myth-busting SPF carousel driving discovery of the Invisible SPF 50",
            theme="myth-busting",
            audience_segment=firsttimers,
            platform="instagram",
            objective="Discovery",
            format="carousel",
            rationale="post_012 (SPF myths) reached 35,900 with 2,270 saves — myth-busting is a reliable discovery driver for newcomers.",
            source_post_ids=["post_012"],
        ),
        Opportunity(
            id="opp_evening_routine",
            title="Reel: the 3-step evening routine for a stressed barrier",
            angle="Quick, calming PM routine reel showing cleanser, serum, moisturizer",
            theme="routine",
            audience_segment=firsttimers,
            platform="instagram",
            objective="Discovery",
            format="reel",
            rationale="Routine reels like post_003 (39,800 reach) and post_011 (41,300 reach) discover well and naturally feature the hero products.",
            source_post_ids=["post_003", "post_011"],
        ),
        Opportunity(
            id="opp_bts_squalane",
            title="Behind-the-scenes: sourcing squalane for the Overnight Mask",
            angle="Where our ingredients come from — transparency reel for the Overnight Recovery Mask",
            theme="behind-the-scenes",
            audience_segment=minimalists,
            platform="tiktok",
            objective="Trust",
            format="reel",
            rationale="post_014 (sourcing behind-the-scenes) reached 57,400 at 10.3% engagement, your second-highest reach — sourcing transparency clearly resonates.",
            source_post_ids=["post_014"],
        ),
    ]


def _fallback_hashtags(opp: Opportunity) -> list[str]:
    base = ["#skincare", "#skinbarrier", "#cleanbeauty"]
    if opp.objective == "Conversion":
        base.append("#skincaretips")
    if opp.theme == "behind-the-scenes":
        base.append("#behindthescenes")
    if opp.theme == "ugc":
        base.append("#customerlove")
    base.append("#lumenskincare")
    return base[:6]


def mock_draft(
    brand: Brand,
    opp: Opportunity,
    exemplars: list[PastPost],
) -> Draft:
    """Produce a platform-appropriate draft grounded in the exemplar voice."""
    if opp.theme == "before-after":
        caption = (
            "8 weeks. One serum. Watch the redness quietly fade. Our Barrier "
            "Repair Serum does the slow, real work your skin actually needs. "
            "Swipe up when you're ready to start yours."
        )
        hooks = [
            "8 weeks of Barrier Serum on reactive skin — real results",
            "Redness didn't stand a chance",
            "The 'quiet' serum everyone's switching to",
        ]
        cta = "Shop the Barrier Repair Serum — link in bio."
        image_prompt = (
            "Split-screen before/after of calm, healthy skin, soft natural light, "
            "minimalist beige background, a single amber serum bottle, editorial skincare"
        )
    elif opp.theme == "behind-the-scenes":
        caption = (
            "Come behind the scenes at Lumen. This is refill day — every pod "
            "packed by hand, because less waste isn't a tagline for us, it's the "
            "whole point. Small batch, big care."
        )
        hooks = [
            "POV: it's refill day at Lumen",
            "What 'small batch' actually looks like",
            "The part of skincare nobody shows you",
        ]
        cta = "Meet the refillable range — link in bio."
        image_prompt = (
            "Hands packing aluminum refill pods on a bright workbench, warm natural "
            "light, sustainable minimalist studio, documentary style"
        )
    elif opp.theme == "ugc":
        caption = (
            "When a customer unboxes the Simple Start Set better than we ever "
            "could. Reposting with love — this is the routine we wish everyone "
            "started with. Three steps, zero guesswork."
        )
        hooks = [
            "Your first real routine, sorted",
            "A customer said it better than we could",
            "The set first-timers keep repurchasing",
        ]
        cta = "Start simple — shop the Simple Start Set."
        image_prompt = (
            "Cozy unboxing flat lay of a 3-product skincare set, warm tones, hands "
            "in frame, authentic UGC feel, soft daylight"
        )
    else:
        caption = (
            f"{opp.angle}. Clear, science-backed, and made for real routines — "
            "here's how it fits into yours."
        )
        hooks = [
            opp.title,
            "Save this for your next skin decision",
            "The simple version, explained",
        ]
        cta = "Learn more — link in bio."
        image_prompt = (
            "Clean minimalist skincare editorial, soft natural light, beige palette, "
            "single product in focus"
        )

    return Draft(
        caption=caption,
        hooks=hooks,
        hashtags=_fallback_hashtags(opp),
        cta=cta,
        image_prompt=image_prompt,
    )


def mock_critique(brand: Brand, draft: Draft) -> tuple[bool, str]:
    """Deterministic tone check against a few brand 'don't' rules."""
    banned = ["miracle", "cure", "guaranteed", "flawless forever"]
    text = f"{draft.caption} {' '.join(draft.hooks)} {draft.cta}".lower()
    hit = [w for w in banned if w in text]
    if hit:
        return False, f"Contains discouraged claim(s): {', '.join(hit)}."
    return True, "On-tone: warm, clear, no over-promising."
