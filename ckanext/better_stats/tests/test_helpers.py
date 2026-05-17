from __future__ import annotations

import pytest

from ckanext.better_stats import helpers


@pytest.mark.parametrize(
    ("viz_type", "expected"),
    [
        ("chart", "fa fa-line-chart"),
        ("table", "fa fa-table"),
        ("card", "fa fa-calculator"),
        ("progress", "fa fa-tasks"),
        ("unknown", "fa fa-question"),
        (None, "fa fa-question"),
    ],
)
def test_bs_get_viz_icon(viz_type: str, expected: str) -> None:
    assert helpers.bs_get_viz_icon(viz_type) == expected


@pytest.mark.parametrize(
    ("viz_type", "expected"),
    [
        ("chart", "Chart"),
        ("table", "Table"),
        ("card", "Card"),
        ("progress", "Progress"),
        ("custom", "custom"),
    ],
)
def test_bs_get_viz_label(viz_type: str, expected: str) -> None:
    assert helpers.bs_get_viz_label(viz_type) == expected


@pytest.mark.usefixtures("with_request_context")
def test_bs_get_embed_code_contains_url() -> None:
    snippet = helpers.bs_get_embed_code("dataset_count", width="800", height="600")
    assert 'width="800"' in snippet
    assert 'height="600"' in snippet
    assert "dataset_count" in snippet
    assert snippet.startswith("<iframe")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (512, "512.00 B"),
        (2048, "2.00 KB"),
        (5 * 1024**2, "5.00 MB"),
        (3 * 1024**3, "3.00 GB"),
        (1024**4, "1.00 TB"),
        (1024**5, "1.00 PB"),
    ],
)
def test_bs_format_bytes(value: float, expected: str) -> None:
    assert helpers.bs_format_bytes(value) == expected
