from __future__ import annotations

import pandas as pd

from mandipulse.utils.formatting import dataframe_to_markdown
from mandipulse.utils.text import make_mandi_id, slugify


class TestDataframeToMarkdown:
    def test_header_row_present(self) -> None:
        df = pd.DataFrame({"a": [1], "b": [2]})
        md = dataframe_to_markdown(df)
        assert "| a | b |" in md

    def test_separator_row_present(self) -> None:
        df = pd.DataFrame({"x": [10]})
        md = dataframe_to_markdown(df)
        assert "| --- |" in md

    def test_data_values_present(self) -> None:
        df = pd.DataFrame({"metric": ["MAE"], "value": ["139.57"]})
        md = dataframe_to_markdown(df)
        assert "MAE" in md
        assert "139.57" in md

    def test_empty_dataframe_has_only_header(self) -> None:
        df = pd.DataFrame({"col": pd.Series([], dtype=str)})
        md = dataframe_to_markdown(df)
        lines = [ln for ln in md.splitlines() if ln.strip()]
        assert len(lines) == 2  # header + separator, no data rows

    def test_multiple_rows(self) -> None:
        df = pd.DataFrame({"n": [1, 2, 3]})
        md = dataframe_to_markdown(df)
        lines = md.splitlines()
        assert len(lines) == 5  # header, sep, 3 data rows


class TestSlugify:
    def test_lowercases(self) -> None:
        assert slugify("NASHIK") == "nashik"

    def test_strips_special_chars(self) -> None:
        # parens are stripped; no space between words, so no underscore injected
        assert slugify("Pune(Khadiki)") == "punekhadiki"

    def test_replaces_spaces_with_underscore(self) -> None:
        assert slugify("Vashi New Mumbai") == "vashi_new_mumbai"

    def test_collapses_multiple_underscores(self) -> None:
        assert "__" not in slugify("A  B")

    def test_strips_leading_trailing_underscores(self) -> None:
        result = slugify("  Nashik  ")
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_empty_string(self) -> None:
        assert slugify("") == ""


class TestMakeMandiId:
    def test_default_state(self) -> None:
        result = make_mandi_id("Nashik")
        assert result == "maharashtra__nashik"

    def test_custom_state(self) -> None:
        result = make_mandi_id("Nashik", state="karnataka")
        assert result == "karnataka__nashik"

    def test_special_chars_in_name(self) -> None:
        # parens strip without inserting underscore (no space before paren)
        result = make_mandi_id("Pune(Khadiki)")
        assert result == "maharashtra__punekhadiki"
