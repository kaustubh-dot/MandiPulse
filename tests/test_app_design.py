"""Tests for the shared Streamlit presentation helpers."""

import pytest

from mandipulse.app import design


def test_snapshot_label_matches_product_contract():
    assert design.SNAPSHOT_LABEL == "Snapshot 30 Oct 2025"
    assert "Frozen demonstration data" in design.FROZEN_NOTICE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1295.7151, "1,296 INR/qtl"),
        (1439.29, "1,439 INR/qtl"),
        (0, "0 INR/qtl"),
        (None, "\u2014 INR/qtl"),
    ],
)
def test_format_inr_per_qtl(value, expected):
    assert design.format_inr_per_qtl(value) == expected


def test_format_inr_two_decimals():
    assert design.format_inr(1144.751) == "1,144.75 INR"


def test_format_km_and_pct():
    assert design.format_km(12.34) == "12.3 km"
    assert design.format_pct(74.41) == "74.4%"
    assert design.format_pct(None) == "\u2014"


def test_format_quantity_defaults_to_one_decimal():
    assert design.format_quantity(100) == "100.0 qtl"


def test_format_date_iso_short_month():
    assert design.format_date_iso("2025-10-30") == "30 Oct 2025"
    assert design.format_date_iso("not-a-date") == "not-a-date"


def test_format_interval_bounds():
    assert design.format_interval(1250, 1340) == "1,250\u20131,340 INR/qtl"
    assert design.format_interval(120, None) == "\u2014"


def test_risk_level_colors_use_all_three_levels():
    assert set(design.RISK_LEVEL_COLORS) == {"low", "medium", "high"}


def test_light_and_dark_tokens_share_roles():
    assert set(design.LIGHT_TOKENS) == set(design.DARK_TOKENS)
    assert {"paper", "ink", "accent", "focus"} <= set(design.LIGHT_TOKENS)


def test_plotly_theme_uses_token_inks():
    theme = design.plotly_theme()
    assert theme["paper_bgcolor"] == design.SURFACE_HEX
    assert "IBM Plex Sans" in theme["font"]["family"]
    assert design.RULE_HEX in theme["xaxis"]["gridcolor"]


def test_base_css_contains_contract_rules():
    css = design._base_css()
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "--mp-paper" in css
