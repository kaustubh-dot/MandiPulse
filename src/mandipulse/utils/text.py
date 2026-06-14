from __future__ import annotations

import re


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def make_mandi_id(market_name: str, state: str = "maharashtra") -> str:
    return f"{state}__{slugify(market_name)}"
