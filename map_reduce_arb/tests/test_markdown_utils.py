from __future__ import annotations

from map_reduce_arb.markdown_utils import prettify_section_table_md


def test_prettify_section_table_md_removes_dot_notation_for_h3() -> None:
    md = "## collateral\n\n### collateral.aggregate\nx\n### collateral.grand_total\ny\n"
    out = prettify_section_table_md("collateral", md)
    assert "## Collateral" in out
    assert "### Aggregate" in out
    assert "### Grand Total" in out
    assert "### collateral.aggregate" not in out


def test_prettify_section_table_md_titleizes_real_estate_h2() -> None:
    md = "## real_estate\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
    out = prettify_section_table_md("real_estate", md)
    assert "## Real Estate" in out

