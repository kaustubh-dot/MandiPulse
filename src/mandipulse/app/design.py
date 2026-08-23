"""MandiPulse "Market Atlas Workbench" design foundations for Streamlit surfaces.

This module is the SINGLE source of presentation helpers for every Streamlit
surface (shell and pages). Pages must import tokens, formatters, the Plotly
theme, and base CSS from here instead of re-declaring colors, CSS strings, or
number formats locally.

Canonical values mirror the Next.js web client token set (OKLCH). Because
Streamlit CSS targets sRGB, each token also carries a hex approximation
computed at author time via the standard OKLCH -> OKLab -> linear-sRGB ->
gamma-encoded conversion; conversions are approximate (8-bit rounded) but
visually faithful on standard displays.

Theme policy this release: Streamlit defaults to LIGHT. Dark-theme constants
are provided for parity with the web client but are not auto-activated.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Color tokens (light theme, default)
# ---------------------------------------------------------------------------
LIGHT_TOKENS: dict[str, dict[str, str]] = {
    "paper": {"oklch": "oklch(97.2% 0.008 235)", "hex": "#f1f7fa"},
    "paper-2": {"oklch": "oklch(94.5% 0.014 235)", "hex": "#e4eff5"},
    "surface": {"oklch": "oklch(99% 0.006 235)", "hex": "#f8fcff"},
    "surface-raised": {"oklch": "oklch(100% 0.004 235)", "hex": "#fdffff"},
    "ink": {"oklch": "oklch(21% 0.035 248)", "hex": "#0a1a28"},
    "ink-2": {"oklch": "oklch(42% 0.035 248)", "hex": "#3e4f60"},
    "muted": {"oklch": "oklch(52% 0.028 248)", "hex": "#5d6b79"},
    "rule": {"oklch": "oklch(82% 0.018 240)", "hex": "#bac6cf"},
    "rule-strong": {"oklch": "oklch(68% 0.025 245)", "hex": "#8c9aa7"},
    "accent": {"oklch": "oklch(69% 0.17 70)", "hex": "#dc8400"},
    "accent-ink": {"oklch": "oklch(21% 0.04 60)", "hex": "#251304"},
    "focus": {"oklch": "oklch(57% 0.19 255)", "hex": "#0074e3"},
    "success": {"oklch": "oklch(52% 0.14 150)", "hex": "#0a7e3a"},
    "warning": {"oklch": "oklch(63% 0.16 70)", "hex": "#c57300"},
    "danger": {"oklch": "oklch(55% 0.19 28)", "hex": "#c93029"},
    "info": {"oklch": "oklch(55% 0.15 250)", "hex": "#0f74c5"},
}

# Dark-theme equivalents (deep blue-black surfaces, near-white ink). Derived
# from the locked direction ("surfaces start oklch(15% 0.018 248), ink becomes
# oklch(94% ...)"); non-surface roles are brightened for dark-ground contrast.
DARK_TOKENS: dict[str, dict[str, str]] = {
    "paper": {"oklch": "oklch(15% 0.018 248)", "hex": "#060c12"},
    "paper-2": {"oklch": "oklch(18% 0.02 248)", "hex": "#0a121a"},
    "surface": {"oklch": "oklch(21% 0.022 248)", "hex": "#101922"},
    "surface-raised": {"oklch": "oklch(24% 0.024 248)", "hex": "#16202a"},
    "ink": {"oklch": "oklch(94% 0.012 248)", "hex": "#e5ecf3"},
    "ink-2": {"oklch": "oklch(78% 0.015 248)", "hex": "#b0b8c1"},
    "muted": {"oklch": "oklch(64% 0.02 248)", "hex": "#838e98"},
    "rule": {"oklch": "oklch(32% 0.022 245)", "hex": "#2a343e"},
    "rule-strong": {"oklch": "oklch(46% 0.028 245)", "hex": "#4b5a67"},
    "accent": {"oklch": "oklch(69% 0.17 70)", "hex": "#dc8400"},
    "accent-ink": {"oklch": "oklch(21% 0.04 60)", "hex": "#251304"},
    "focus": {"oklch": "oklch(72% 0.16 255)", "hex": "#59a6ff"},
    "success": {"oklch": "oklch(68% 0.14 150)", "hex": "#4eb068"},
    "warning": {"oklch": "oklch(75% 0.14 70)", "hex": "#e69c3a"},
    "danger": {"oklch": "oklch(65% 0.18 28)", "hex": "#e8594d"},
    "info": {"oklch": "oklch(68% 0.13 250)", "hex": "#549de5"},
}

# Convenience hex constants (light theme; hex approximations of OKLCH).
PAPER_HEX = LIGHT_TOKENS["paper"]["hex"]
PAPER_2_HEX = LIGHT_TOKENS["paper-2"]["hex"]
SURFACE_HEX = LIGHT_TOKENS["surface"]["hex"]
SURFACE_RAISED_HEX = LIGHT_TOKENS["surface-raised"]["hex"]
INK_HEX = LIGHT_TOKENS["ink"]["hex"]
INK_2_HEX = LIGHT_TOKENS["ink-2"]["hex"]
MUTED_HEX = LIGHT_TOKENS["muted"]["hex"]
RULE_HEX = LIGHT_TOKENS["rule"]["hex"]
RULE_STRONG_HEX = LIGHT_TOKENS["rule-strong"]["hex"]
ACCENT_HEX = LIGHT_TOKENS["accent"]["hex"]
ACCENT_INK_HEX = LIGHT_TOKENS["accent-ink"]["hex"]
FOCUS_HEX = LIGHT_TOKENS["focus"]["hex"]
SUCCESS_HEX = LIGHT_TOKENS["success"]["hex"]
WARNING_HEX = LIGHT_TOKENS["warning"]["hex"]
DANGER_HEX = LIGHT_TOKENS["danger"]["hex"]
INFO_HEX = LIGHT_TOKENS["info"]["hex"]

# ---------------------------------------------------------------------------
# Typography roles (font stacks tolerate local font availability)
# ---------------------------------------------------------------------------
DISPLAY_FONT_STACK = '"Barlow Condensed", "Arial Narrow", "IBM Plex Sans", sans-serif'
BODY_FONT_STACK = '"IBM Plex Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
MONO_FONT_STACK = '"IBM Plex Mono", "Cascadia Mono", Consolas, "Courier New", monospace'

# ---------------------------------------------------------------------------
# Radii / spacing / z-index / motion scales
# ---------------------------------------------------------------------------
RADII: dict[str, str] = {
    "control": "0.375rem",
    "panel": "0.5rem",
    "pill": "999px",
}

SPACING_SCALE_PX: tuple[int, ...] = (2, 4, 8, 12, 16, 24, 40, 64, 96, 144)

Z_INDEX: dict[str, int] = {
    "base": 0,
    "raised": 10,
    "sticky": 100,
    "overlay": 200,
    "toast": 300,
}

MOTION_DURATION_MS: dict[str, int] = {"fast": 120, "base": 220, "slow": 420}
MOTION_EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)"

# Risk levels map to status hues; color is never the sole signal — callers must
# render the level label alongside the color.
RISK_LEVEL_COLORS: dict[str, str] = {
    "low": SUCCESS_HEX,
    "medium": WARNING_HEX,
    "high": DANGER_HEX,
}

# ---------------------------------------------------------------------------
# Snapshot framing constants (exact strings required by product spec)
# ---------------------------------------------------------------------------
SNAPSHOT_LABEL = "Snapshot 30 Oct 2025"
FROZEN_NOTICE = (
    "Frozen demonstration data — all figures come from a fixed October 2025 "
    "offline snapshot; no live market feed is queried."
)

EM_DASH = "\u2014"

_MISSING_SENTINEL = object()


def _is_missing(value: Any) -> bool:
    """True for None and NaN-like floats."""
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False


def _grouped(value: float | None, decimals: int) -> str:
    if _is_missing(value):
        return EM_DASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    return f"{number:,.{decimals}f}"


# ---------------------------------------------------------------------------
# Numeric formatters (pure functions, shared by all pages)
# ---------------------------------------------------------------------------
def format_inr_per_qtl(value: Any, decimals: int = 0) -> str:
    """Format a price in INR per quintal, e.g. ``1,295 INR/qtl``."""
    return f"{_grouped(value, decimals)} INR/qtl"


def format_inr(value: Any, decimals: int = 2) -> str:
    """Format a rupee amount, e.g. ``1,295.50 INR``."""
    return f"{_grouped(value, decimals)} INR"


def format_km(value: Any, decimals: int = 1) -> str:
    """Format a distance, e.g. ``12.3 km``."""
    return f"{_grouped(value, decimals)} km"


def format_pct(value: Any, decimals: int = 1) -> str:
    """Format a percentage already expressed in percent units, e.g. ``74.4%``."""
    if _is_missing(value):
        return EM_DASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    return f"{number:.{decimals}f}%"


def format_quantity(qtl: Any, decimals: int = 1) -> str:
    """Format a quantity denominated in quintals, e.g. ``1,234.5 qtl``."""
    return f"{_grouped(qtl, decimals)} qtl"


_DATE_PARSE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S")


def format_date_iso(iso: Any) -> str:
    """Format an ISO date (string or date/datetime) as ``30 Oct 2025``.

    Unparseable non-empty strings are returned unchanged; missing input
    returns an em dash.
    """
    if _is_missing(iso):
        return EM_DASH
    if isinstance(iso, datetime):
        parsed: date | None = iso.date()
    elif isinstance(iso, date):
        parsed = iso
    else:
        text = str(iso).strip()
        if not text:
            return EM_DASH
        parsed = None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            for fmt in _DATE_PARSE_FORMATS:
                try:
                    parsed = datetime.strptime(text, fmt).date()
                    break
                except ValueError:
                    continue
        if parsed is None:
            return text
    return f"{parsed.day} {parsed:%b %Y}"


def format_interval(lower: Any, upper: Any, unit: str = "INR/qtl", decimals: int = 0) -> str:
    """Format a bounded interval, e.g. ``1,250–1,340 INR/qtl``."""
    if _is_missing(lower) or _is_missing(upper):
        return EM_DASH
    return f"{_grouped(lower, decimals)}\u2013{_grouped(upper, decimals)} {unit}"


# ---------------------------------------------------------------------------
# Plotly theme derived from tokens (for F5 charts)
# ---------------------------------------------------------------------------
def plotly_theme() -> dict[str, Any]:
    """Return a layout template dict derived from the light-theme tokens.

    Apply with ``fig.update_layout(**plotly_theme())``. Uses the structured
    palette only (no rainbow defaults); gridlines stay subtle at the rule hue.
    """
    return {
        "font": {"family": BODY_FONT_STACK, "size": 13, "color": INK_HEX},
        "paper_bgcolor": SURFACE_HEX,
        "plot_bgcolor": SURFACE_HEX,
        "colorway": [INK_HEX, ACCENT_HEX, FOCUS_HEX, INFO_HEX, SUCCESS_HEX, MUTED_HEX],
        "hoverlabel": {
            "bgcolor": SURFACE_RAISED_HEX,
            "bordercolor": RULE_HEX,
            "font": {"family": MONO_FONT_STACK, "size": 12, "color": INK_HEX},
        },
        "margin": {"l": 8, "r": 8, "t": 24, "b": 8},
        "legend": {"bgcolor": "rgba(0,0,0,0)"},
        "xaxis": {
            "gridcolor": RULE_HEX,
            "zerolinecolor": RULE_STRONG_HEX,
            "linecolor": RULE_STRONG_HEX,
            "tickfont": {"family": MONO_FONT_STACK, "size": 11, "color": INK_2_HEX},
        },
        "yaxis": {
            "gridcolor": RULE_HEX,
            "zerolinecolor": RULE_STRONG_HEX,
            "linecolor": RULE_STRONG_HEX,
            "tickfont": {"family": MONO_FONT_STACK, "size": 11, "color": INK_2_HEX},
        },
    }


# ---------------------------------------------------------------------------
# Base CSS injection (one scoped block for the whole app)
# ---------------------------------------------------------------------------
def _base_css() -> str:
    """Compose the scoped stylesheet. Keep it narrow; add comments per rule."""
    t = {name: entry["hex"] for name, entry in LIGHT_TOKENS.items()}
    dt = {name: entry["hex"] for name, entry in DARK_TOKENS.items()}
    fast, base = MOTION_DURATION_MS["fast"], MOTION_DURATION_MS["base"]
    ease = MOTION_EASE_OUT
    return f"""
/* MandiPulse "Market Atlas Workbench" base styles (source: mandipulse.app.design) */
:root {{
  --mp-paper: {t["paper"]}; --mp-paper-2: {t["paper-2"]};
  --mp-surface: {t["surface"]}; --mp-surface-raised: {t["surface-raised"]};
  --mp-ink: {t["ink"]}; --mp-ink-2: {t["ink-2"]}; --mp-muted: {t["muted"]};
  --mp-rule: {t["rule"]}; --mp-rule-strong: {t["rule-strong"]};
  --mp-accent: {t["accent"]}; --mp-accent-ink: {t["accent-ink"]};
  --mp-focus: {t["focus"]}; --mp-success: {t["success"]};
  --mp-warning: {t["warning"]}; --mp-danger: {t["danger"]}; --mp-info: {t["info"]};
  --mp-font-display: {DISPLAY_FONT_STACK};
  --mp-font-body: {BODY_FONT_STACK};
  --mp-font-num: {MONO_FONT_STACK};
}}
/* Dark tokens ship dormant; Streamlit stays LIGHT this release. Opt in by
   setting data-mp-theme="dark" on <html>. */
html[data-mp-theme="dark"] {{
  --mp-paper: {dt["paper"]}; --mp-paper-2: {dt["paper-2"]};
  --mp-surface: {dt["surface"]}; --mp-surface-raised: {dt["surface-raised"]};
  --mp-ink: {dt["ink"]}; --mp-ink-2: {dt["ink-2"]}; --mp-muted: {dt["muted"]};
  --mp-rule: {dt["rule"]}; --mp-rule-strong: {dt["rule-strong"]};
  --mp-focus: {dt["focus"]}; --mp-success: {dt["success"]};
  --mp-warning: {dt["warning"]}; --mp-danger: {dt["danger"]}; --mp-info: {dt["info"]};
}}
/* Canvas + body text */
body, .stApp {{ background-color: var(--mp-paper); color: var(--mp-ink);
  font-family: var(--mp-font-body); }}
/* Sidebar: paper-2 panel with a single rule edge */
[data-testid="stSidebar"] {{ background-color: var(--mp-paper-2);
  border-right: 1px solid var(--mp-rule); }}
/* Display headings use the condensed role */
h1, h2 {{ font-family: var(--mp-font-display); font-weight: 700;
  letter-spacing: 0.01em; }}
/* Numeric role for metric values (generic testid match) + .mp-num utility */
[data-testid*="MetricValue"], .mp-num {{ font-family: var(--mp-font-num);
  font-weight: 500; font-variant-numeric: tabular-nums; }}
/* Keyboard focus ring in the focus hue */
.stApp :focus-visible {{ outline: 2px solid var(--mp-focus);
  outline-offset: 2px; border-radius: {RADII["control"]}; }}
/* Sentence case everywhere: never small caps, never uppercase transforms */
h1, h2, h3, h4, h5, h6, button, a, label, summary, th, [data-testid] {{
  font-variant-caps: normal; text-transform: none; letter-spacing: normal; }}
/* Motion: animate transform/opacity only, short ease-out transitions on UI */
.stApp button, .stApp a, .stApp [data-baseweb="tag"],
.stApp [role="tab"] {{ transition-property: transform, opacity;
  transition-duration: {base}ms; transition-timing-function: {ease}; }}
.mp-wordmark {{ font-family: var(--mp-font-display); font-weight: 700;
  color: var(--mp-ink); line-height: 1.1; margin: 0; font-size: 2rem; }}
.mp-snapshot-label {{ font-family: var(--mp-font-num); color: var(--mp-muted); }}
.mp-frozen-note {{ color: var(--mp-muted); font-size: 0.875rem;
  border-left: 2px solid var(--mp-rule-strong); padding-left: 0.625rem; }}
@media (prefers-reduced-motion: reduce) {{
  /* Collapse motion to opacity-only transitions, <=150ms; stop keyframes */
  *, *::before, *::after {{
    animation-name: none !important;
    transition-property: opacity !important;
    transition-duration: {fast}ms !important;
  }}
}}
"""


def inject_base_css() -> None:
    """Emit the single shared <style> block. Call once from the app shell."""
    st.markdown(f"<style>{_base_css()}</style>", unsafe_allow_html=True)
