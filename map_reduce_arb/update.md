# Update: Partner Shared Information (passthrough)

This note describes the **Partner Shared Information** section added to the `map_reduce_arb` pipeline. It is a **non-LLM passthrough**: text is built deterministically from the raw client payload and merged metadata.

## Behavior

- **Scope** (`group` | `legal_entity` | `business_relation`) selects which layout is rendered (group + legal entities, legal entity + business relations, or a single business relation).
- **Formatting** uses only fields present in the JSON (organization names, GPIDs, VAT, industry codes/descriptions, PD grade, CRIF score). Field names supported include API variants such as `vatNumber` / `VATNumber` and `bankingRelationNumber` / `bankingRelationshipNumber`.

## Files added

| File | Purpose |
|------|---------|
| `partner_shared_info.py` | `resolve_partner_shared_scope()`, `format_partner_shared_information()` — markdown body for the section |
| `tests/test_partner_shared_info.py` | Unit tests for scope resolution and the three layouts |

## Files changed

| File | Change |
|------|--------|
| `graph.py` | Resolves and stores `raw_obj` in `_enrich_node` when missing (default: `enrich_transform/raw.json`). Builds a `partner_shared_information` bundle first in `_build_bundles_node` with `PROMPT_NONE`. Merges graph `metadata` into `raw["metadata"]` before formatting so scope can be set from `invoke(..., metadata={...})`. |
| `bundle_config.yaml` | New first entry: **Partner Shared Information** (`partner_shared_information`), orders of other sections shifted. |
| `prompts.py` | `partner_shared_information` explicitly maps to `PROMPT_NONE`. |
| `run_summarizer.py` | `render_to_markdown` import corrected to `map_reduce_arb.graph`. |

## How to control summary level

1. **Metadata (preferred)** — set one of:
   - `metadata.creditSummaryScope`
   - `metadata.partnerSharedInformationScope`
   - `metadata.summaryScope`  

   Values (case-insensitive, flexible spelling): `group`, `legal_entity`, `business_relation` (and aliases such as `br`, `standalone`).

2. **Or** set `client.partnerType` (e.g. `GROUP`, `LEGAL_ENTITY`, `BUSINESS_RELATION`, `BR`, `STANDALONE_COMPANY`).

3. **Or** pass scope via the LangGraph invoke metadata (merged into `raw["metadata"]` for the formatter).

4. If nothing is set, **heuristics** apply (e.g. presence of a `Group` entity in `legalEntities` defaults toward group scope).

## Pipeline integration

- Section identifier: `partner_shared_information`.
- Same passthrough path as other `PROMPT_NONE` bundles: `summarize_passthrough()` in `_summarize_one_node`.
- LLM evaluation skips passthrough sections (unchanged behavior).

## Tests

From the repo root:

```bash
python -m pytest map_reduce_arb/tests -q
```

## Related documentation

For how **`enrich_transform`** and **`map_reduce_arb`** connect end-to-end (diagrams and sample flow), see **`METHODOLOGY.md`** in this folder.
