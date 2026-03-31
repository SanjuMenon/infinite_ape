from __future__ import annotations

import re


def _titleize(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("_", " ")
    # collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s.title()


def prettify_section_table_md(section_name: str, table_md: str) -> str:
    """Make downstream `table_md` headings more human-friendly.

    Currently targets headings like:
      - "### collateral.aggregate" -> "### Aggregate"
      - "### collateral.grand_total" -> "### Grand Total"
      - "## real_estate" -> "## Real Estate"

    Only rewrites H3 headings that start with "{section_name}." to remove dot-notation.
    """
    sec = (section_name or "").strip()
    if not sec:
        return table_md

    out_lines: list[str] = []
    prefix_h3_dot = f"### {sec}."
    h2_exact = f"## {sec}"
    h3_exact = f"### {sec}"

    for line in (table_md or "").splitlines():
        stripped = line.strip()
        # Rewrite the section header itself (preserve heading level)
        if stripped == h2_exact:
            out_lines.append(f"## {_titleize(sec)}")
            continue
        if stripped == h3_exact:
            out_lines.append(f"### {_titleize(sec)}")
            continue

        # Rewrite dotted H3 headings like "### section.subkey"
        if stripped.startswith(prefix_h3_dot):
            suffix = stripped[len(prefix_h3_dot) :].strip()
            pretty = _titleize(suffix)
            out_lines.append(f"### {pretty}")
        else:
            out_lines.append(line)

    return "\n".join(out_lines).rstrip()

