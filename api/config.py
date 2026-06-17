from __future__ import annotations

import os

API_VERSION = "0.1.0"

# MVP scope guards — out-of-scope requests return typed 400/422 errors.
SUPPORTED_CROPS: frozenset[str] = frozenset({"onion"})
SUPPORTED_STATES: frozenset[str] = frozenset({"maharashtra"})
SUPPORTED_HORIZONS: frozenset[int] = frozenset({7})

# CORS origins. Default "*" is deliberate: the API is public, read-only, and carries no secrets.
# Set MANDIPULSE_ALLOWED_ORIGINS=https://your-frontend.vercel.app in production to tighten.
ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.environ.get("MANDIPULSE_ALLOWED_ORIGINS", "*").split(",") if o.strip()
]
