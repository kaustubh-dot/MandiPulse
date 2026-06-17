from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.config import ALLOWED_ORIGINS, API_VERSION  # noqa: E402
from api.errors import ApiError, api_error_handler, validation_error_handler  # noqa: E402
from api.routes import router  # noqa: E402

app = FastAPI(
    title="MandiPulse India API",
    description=(
        "Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers. "
        "Exposes precomputed 7-day price forecasts and transport-adjusted mandi rankings. "
        "See /docs for interactive exploration."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(router)
