"""MandiPulse Quiet Exchange design foundations for Streamlit surfaces.

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
    "paper": {"oklch": "oklch(96% 0.012 75)", "hex": "#f7f1e9"},
    "paper-2": {"oklch": "oklch(92% 0.016 75)", "hex": "#ebe3d9"},
    "surface": {"oklch": "oklch(98% 0.008 75)", "hex": "#fcf8f3"},
    "surface-raised": {"oklch": "oklch(99% 0.006 75)", "hex": "#fefbf7"},
    "ink": {"oklch": "oklch(20% 0.012 55)", "hex": "#1a1511"},
    "ink-2": {"oklch": "oklch(38% 0.012 55)", "hex": "#48413c"},
    "muted": {"oklch": "oklch(45% 0.012 55)", "hex": "#5b544f"},
    "rule": {"oklch": "oklch(82% 0.012 70)", "hex": "#c9c3bc"},
    "rule-strong": {"oklch": "oklch(68% 0.018 70)", "hex": "#a0978d"},
    "accent": {"oklch": "oklch(38% 0.13 18)", "hex": "#781827"},
    "accent-ink": {"oklch": "oklch(96% 0.012 75)", "hex": "#f7f1e9"},
    "focus": {"oklch": "oklch(48% 0.15 18)", "hex": "#a12e3c"},
    "success": {"oklch": "oklch(45% 0.13 145)", "hex": "#146720"},
    "warning": {"oklch": "oklch(48% 0.13 70)", "hex": "#8a4c00"},
    "danger": {"oklch": "oklch(48% 0.15 18)", "hex": "#a12e3c"},
    "info": {"oklch": "oklch(45% 0.06 235)", "hex": "#315b72"},
}

# Dark-theme equivalents (deep blue-black surfaces, near-white ink). Derived
# from the locked direction ("surfaces start oklch(15% 0.018 248), ink becomes
# oklch(94% ...)"); non-surface roles are brightened for dark-ground contrast.
DARK_TOKENS: dict[str, dict[str, str]] = {
    "paper": {"oklch": "oklch(16% 0.012 55)", "hex": "#110c08"},
    "paper-2": {"oklch": "oklch(20% 0.014 55)", "hex": "#1b1410"},
    "surface": {"oklch": "oklch(24% 0.012 55)", "hex": "#241e1a"},
    "surface-raised": {"oklch": "oklch(28% 0.014 55)", "hex": "#2f2722"},
    "ink": {"oklch": "oklch(94% 0.012 75)", "hex": "#f0eae3"},
    "ink-2": {"oklch": "oklch(78% 0.012 75)", "hex": "#bcb6af"},
    "muted": {"oklch": "oklch(68% 0.014 55)", "hex": "#9f9690"},
    "rule": {"oklch": "oklch(34% 0.018 55)", "hex": "#40362f"},
    "rule-strong": {"oklch": "oklch(48% 0.02 55)", "hex": "#675b53"},
    "accent": {"oklch": "oklch(72% 0.12 18)", "hex": "#e68488"},
    "accent-ink": {"oklch": "oklch(16% 0.012 55)", "hex": "#110c08"},
    "focus": {"oklch": "oklch(72% 0.14 18)", "hex": "#ef7d83"},
    "success": {"oklch": "oklch(70% 0.1 145)", "hex": "#76af77"},
    "warning": {"oklch": "oklch(76% 0.11 70)", "hex": "#dba25b"},
    "danger": {"oklch": "oklch(72% 0.14 18)", "hex": "#ef7d83"},
    "info": {"oklch": "oklch(70% 0.07 235)", "hex": "#7aa8bd"},
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
DISPLAY_FONT_STACK = '"Cormorant Garamond", Georgia, "Times New Roman", serif'
BODY_FONT_STACK = 'Manrope, "Segoe UI", "Helvetica Neue", Arial, sans-serif'
MONO_FONT_STACK = '"IBM Plex Mono", "Cascadia Mono", Consolas, monospace'

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
    """Compose the scoped stylesheet for Quiet Exchange Streamlit surfaces."""
    light = {name: entry["hex"] for name, entry in LIGHT_TOKENS.items()}
    dark = {name: entry["hex"] for name, entry in DARK_TOKENS.items()}
    return f"""
/* Quiet Exchange base styles (source: mandipulse.app.design) */
:root {{
  --mp-paper: {light["paper"]};
  --mp-paper-2: {light["paper-2"]};
  --mp-surface: {light["surface"]};
  --mp-surface-raised: {light["surface-raised"]};
  --mp-ink: {light["ink"]};
  --mp-ink-2: {light["ink-2"]};
  --mp-muted: {light["muted"]};
  --mp-rule: {light["rule"]};
  --mp-rule-strong: {light["rule-strong"]};
  --mp-accent: {light["accent"]};
  --mp-accent-ink: {light["accent-ink"]};
  --mp-focus: {light["focus"]};
  --mp-success: {light["success"]};
  --mp-warning: {light["warning"]};
  --mp-danger: {light["danger"]};
  --mp-info: {light["info"]};
  --mp-font-display: {DISPLAY_FONT_STACK};
  --mp-font-body: {BODY_FONT_STACK};
  --mp-font-num: {MONO_FONT_STACK};
  color-scheme: light;
}}
[data-theme="dark"] {{
  --mp-paper: {dark["paper"]};
  --mp-paper-2: {dark["paper-2"]};
  --mp-surface: {dark["surface"]};
  --mp-surface-raised: {dark["surface-raised"]};
  --mp-ink: {dark["ink"]};
  --mp-ink-2: {dark["ink-2"]};
  --mp-muted: {dark["muted"]};
  --mp-rule: {dark["rule"]};
  --mp-rule-strong: {dark["rule-strong"]};
  --mp-accent: {dark["accent"]};
  --mp-accent-ink: {dark["accent-ink"]};
  --mp-focus: {dark["focus"]};
  --mp-success: {dark["success"]};
  --mp-warning: {dark["warning"]};
  --mp-danger: {dark["danger"]};
  --mp-info: {dark["info"]};
  color-scheme: dark;
}}
.stApp,
body {{
  background: var(--mp-paper);
  color: var(--mp-ink);
  font-family: var(--mp-font-body);
}}
[data-testid="stSidebar"] {{
  background: var(--mp-paper-2);
  border-right: 1px solid var(--mp-rule);
}}
h1,
h2,
h3,
h4,
h5,
h6 {{
  font-family: var(--mp-font-display);
  font-weight: 400;
  letter-spacing: 0;
  text-transform: none;
}}
[data-testid="stMetric"] {{
  border-top: 1px solid var(--mp-rule);
  border-bottom: 1px solid var(--mp-rule);
  padding-block: 0.5rem;
}}
[data-testid="stMetricValue"] {{
  font-family: var(--mp-font-num);
  font-variant-numeric: tabular-nums;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [role="combobox"],
[data-baseweb="select"] [role="combobox"],
textarea,
input,
select {{
  background: var(--mp-surface);
  border: 1px solid var(--mp-rule-strong);
  color: var(--mp-ink);
  font-family: var(--mp-font-body);
}}
button,
[role="tab"],
a {{
  transition-property: transform, opacity;
  transition-duration: 120ms;
  transition-timing-function: {MOTION_EASE_OUT};
}}
button:hover,
[role="tab"]:hover,
a:hover {{
  opacity: 0.9;
}}
button:active,
[role="tab"]:active,
a:active {{
  transform: translateY(1px);
}}
table {{
  border-collapse: collapse;
}}
th,
td {{
  border-top: 1px solid var(--mp-rule);
  color: var(--mp-ink);
}}
details {{
  border-top: 1px solid var(--mp-rule);
  border-bottom: 1px solid var(--mp-rule);
}}
summary {{
  font-family: var(--mp-font-body);
  cursor: pointer;
}}
caption,
.stCaption {{
  color: var(--mp-muted);
}}
.mp-snapshot-label {{
  font-family: var(--mp-font-num);
  color: var(--mp-muted);
}}
.mp-frozen-note {{
  color: var(--mp-muted);
  border-top: 1px solid var(--mp-rule);
  border-bottom: 1px solid var(--mp-rule);
  padding-block: 0.75rem;
}}
.stApp :focus-visible {{
  outline: 2px solid var(--mp-focus);
  outline-offset: 2px;
}}
@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    animation: none !important;
    transition-duration: 0ms !important;
  }}
}}
"""


def inject_base_css() -> None:
    """Emit the single shared <style> block. Call once from the app shell."""
    st.markdown(f"<style>{_base_css()}</style>", unsafe_allow_html=True)


def render_page_header(title: str, intro: str) -> None:
    st.title(title)
    st.caption(intro)


def render_frozen_notice() -> None:
    st.markdown(
        f'<p class="mp-frozen-note"><span class="mp-snapshot-label">{SNAPSHOT_LABEL}</span>'
        f" — {FROZEN_NOTICE}</p>",
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, caption: str | None = None) -> None:
    st.header(title)
    if caption:
        st.caption(caption)
