"""Load and validate seed JSON into typed Pydantic models (cached)."""
from __future__ import annotations

import json
from functools import lru_cache

from .config import get_settings
from .schemas import Brand, PastPost, Product


def _read_json(name: str):
    path = get_settings().data_dir / name
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_brand() -> Brand:
    return Brand.model_validate(_read_json("brand.json"))


@lru_cache(maxsize=1)
def load_products() -> list[Product]:
    return [Product.model_validate(p) for p in _read_json("products.json")]


@lru_cache(maxsize=1)
def load_past_posts() -> list[PastPost]:
    return [PastPost.model_validate(p) for p in _read_json("past_posts.json")]
