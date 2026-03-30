"""
enrich_transform

Pydantic validation + Pandas relational operations over the nested `raw.json`,
then downstream actions that can split enriched payloads into table/summary outputs.
"""

from enrich_transform.cli import main

__all__ = ["main"]
