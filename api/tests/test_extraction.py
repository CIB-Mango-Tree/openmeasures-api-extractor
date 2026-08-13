"""Golden-file tests for the hit -> Parquet projection.

These guard the one change in the Polars migration that could corrupt user data silently: if the
projection drops a column, reorders columns, or alters a cell, nothing raises -- the export is
just quietly wrong. The goldens were generated from the previous pandas implementation
(json_normalize -> strip '_source.' -> project onto PLATFORMS[platform]["columns"]) using real
bluesky payloads taken from a production database, plus a synthetic truth_social fixture that
covers the list-valued `mentions` column and a ragged record.
"""

import json
from pathlib import Path
from typing import Any

import polars as pl
import pytest

from src.storage.dataset import drop_empty_columns, extract_hits

FIXTURES = Path(__file__).parent / "fixtures"
PLATFORMS_UNDER_TEST = ("bluesky", "truth_social")


def _hits(platform: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / f"{platform}_hits.json").read_text())


def _golden_records(platform: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / f"{platform}_golden.json").read_text())


def _projected(platform: str) -> pl.DataFrame:
    return drop_empty_columns(extract_hits(platform, _hits(platform)))


@pytest.mark.parametrize("platform", PLATFORMS_UNDER_TEST)
def test_columns_match_golden_exactly(platform: str) -> None:
    """Column order is part of the contract: it is the column order of every export."""
    frame = _projected(platform)
    golden = pl.read_csv(FIXTURES / f"{platform}_golden.csv", infer_schema_length=None)

    assert frame.columns == golden.columns


@pytest.mark.parametrize("platform", PLATFORMS_UNDER_TEST)
def test_row_count_matches_golden(platform: str) -> None:
    assert _projected(platform).height == len(_golden_records(platform))


@pytest.mark.parametrize("platform", PLATFORMS_UNDER_TEST)
def test_every_cell_matches_golden(platform: str) -> None:
    frame = _projected(platform)

    for index, golden_row in enumerate(_golden_records(platform)):
        row = frame.row(index, named=True)

        for column in frame.columns:
            expected = golden_row.get(column)
            actual = row.get(column)

            if isinstance(actual, list):
                # Nested values (truth_social `mentions`) are compared structurally; empty and
                # missing are equivalent here, as they were under pandas.
                normalized = [dict(item) for item in actual] if actual else None
                assert normalized == (expected or None), f"row {index}, column {column!r}"
                continue

            if expected is None and actual is None:
                continue

            assert str(expected) == str(actual), f"row {index}, column {column!r}"


def test_raw_pages_keep_the_full_declared_schema() -> None:
    """Pages must be concatenable, so a raw page keeps declared columns even when unused.

    drop_empty_columns is applied to the processed output, not to raw pages -- otherwise two
    pages of the same query could write different schemas and fail to read back together.
    """
    from src.storage.dataset import platform_columns

    single = extract_hits("truth_social", _hits("truth_social")[:1])

    assert single.columns == platform_columns("truth_social")


def test_pages_with_differing_content_concatenate() -> None:
    hits = _hits("truth_social")
    first = extract_hits("truth_social", hits[:2])
    second = extract_hits("truth_social", hits[2:])

    combined = pl.concat([first, second], how="vertical_relaxed")

    assert combined.height == len(hits)
