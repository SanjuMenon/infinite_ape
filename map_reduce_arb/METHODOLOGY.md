# Methodology: `enrich_transform` and `map_reduce_arb`

This document explains how the **`enrich_transform`** package and the **`map_reduce_arb`** LangGraph pipeline fit together: what each layer owns, how data flows, and a concrete walkthrough.

---

## Roles at a glance

| Layer | Responsibility |
|--------|----------------|
| **`enrich_transform`** | Take nested **raw** JSON (credit / partner payload). **Validate** with Pydantic (`RawPayloadModel`). **Normalize** into relational rows (Pandas), **aggregate**, and emit a compact **enriched** JSON tree (`collateral`, `business_model`, `real_estate`). Then run **downstream actions** per section: markdown tables, summary dicts, and JSON strings for optional LLM input. |
| **`map_reduce_arb`** | Orchestrate **one graph run**: call enrich, **materialize bundles** (section-sized units with a prompt and/or passthrough payload), **map** them to parallel workers, **summarize** (LLM or passthrough), **reduce** into `CreditSummaryGenAIResponse`, optionally **evaluate** LLM sections. Ordering and report section titles come from **`bundle_config.yaml`**. |

`map_reduce_arb` does not duplicate enrich logic; it **imports** `enrich_transform.cli.run` inside the graph’s enrich node.

---

## Component diagram

High-level view of packages and the main internal pieces.

```mermaid
flowchart TB
  subgraph inputs["Inputs"]
    RAW["raw.json / raw_obj"]
    BC["bundle_config.yaml"]
    OS["output_schema.json"]
    META["metadata (optional)"]
  end

  subgraph ET["enrich_transform"]
    VAL["RawPayloadModel validation"]
    NORM["normalize.py\n(collateral / BM / RE rows)"]
    BE["build_enriched_payload"]
    DISP["run_downstream_actions\n(TableAction, SummaryAction)"]
    VAL --> BE
    NORM --> BE
    BE --> DISP
  end

  subgraph MR["map_reduce_arb"]
    G["LangGraph: build_map_reduce_graph"]
    EN["_enrich_node\n(enrich_run)"]
    BB["_build_bundles_node"]
    SP["split_bundle"]
    SM["_summarize_one_node\n(LLM / passthrough)"]
    RD["_reduce_node\n→ CreditSummaryGenAIResponse"]
    EV["_evaluate_node\n(optional)"]

    G --> EN --> BB --> SP --> SM --> RD --> EV
  end

  RAW --> EN
  EN --> ET
  ET -->|"enriched + downstream"| BB
  RAW --> BB
  META --> BB
  BC --> RD
  OS --> RD
```

**Bundle sources (conceptual):**

- **From enrich downstream:** `business_model` uses `json_str` (and table markdown for passthrough-style sections where configured).
- **From enrich enriched JSON:** `collateral`, `real_estate` passthrough bundles use the **enriched** subtree (not the downstream `json_str` mirror), for stable structured JSON in the report.
- **From raw only:** `partner_shared_information` is formatted in `map_reduce_arb` from **`raw_obj`** (plus merged `metadata`), without going through Pandas enrich.

---

## Sequence diagram

Typical run when `bundles` are **not** pre-injected (full pipeline).

```mermaid
sequenceDiagram
  participant Caller
  participant Graph as LangGraph (map_reduce_arb)
  participant Enrich as enrich_transform.run
  participant Build as _build_bundles_node
  participant Split as _split_node
  participant Map as _dispatch_node / summarize_one
  participant Reduce as _reduce_node
  participant Eval as _evaluate_node

  Caller->>Graph: invoke(raw_path / raw_obj, bundle_config, ...)
  Graph->>Graph: enrich
  Graph->>Enrich: run(raw_obj, no_downstream=false)
  Enrich->>Enrich: build_enriched_payload
  Enrich->>Enrich: run_downstream_actions
  Enrich-->>Graph: enriched, downstream

  Note over Graph: _enrich_node resolves raw_obj if missing

  Graph->>Build: build_bundles(state)
  Build->>Build: partner_shared_information (markdown from raw)
  Build->>Build: collateral / real_estate (JSON from enriched)
  Build->>Build: business_model (prompt + json_str)
  Build-->>Graph: bundles[]

  Graph->>Split: split (currently no-op per bundle)
  Graph->>Map: Send each subtask to summarize_one
  Map->>Map: passthrough OR LLM per bundle.prompt
  Map-->>Graph: partials[] (merged)

  Graph->>Reduce: aggregate → CreditSummaryGenAIResponse
  Reduce-->>Graph: report
  Graph->>Eval: optional scores if LLM available
  Eval-->>Graph: report + evaluation_scores
  Graph-->>Caller: final state
```

If the caller passes **`bundles`** directly, **`enrich`** and **`build_bundles`** are skipped (tests and custom integrations).

---

## Flow in prose

1. **Entry**  
   You call `build_map_reduce_graph().invoke({...})` with at least `raw_obj` or `raw_path`, plus `bundle_config` and `output_schema`. Optional `metadata` is merged into the raw view used for partner-facing text.

2. **Enrich (`_enrich_node`)**  
   - Resolves a full **`raw_obj`** (from state, `raw_path`, or default `enrich_transform/raw.json`).  
   - Calls **`enrich_transform.cli.run`**, which:  
     - Validates **`RawPayloadModel`**.  
     - Builds **enriched** sections via **`build_enriched_payload`** (collateral aggregates, business-model rows, real-estate rows).  
     - Runs **`run_downstream_actions`** for `collateral`, `business_model`, `real_estate`, producing per-section **`json_str`**, **`table_md`**, **`summary`**, **`summary_md`**.

3. **Build bundles (`_build_bundles_node`)**  
   For each configured section (order defined in code + `bundle_config`):  
   - **Partner Shared Information:** deterministic markdown from **`raw_obj`** / metadata (no LLM).  
   - **Collateral / real estate:** passthrough **enriched** JSON as string payload.  
   - **Business model:** LLM path uses **`downstream[...].json_str`**; passthrough path would use table markdown (per prompt rules in `prompts.py`).  
   Each item becomes a **`Bundle`** (`field_name`, `prompt`, `payload`).

4. **Split**  
   `split_bundle` may duplicate or shard bundles; today it returns a single bundle per input.

5. **Map–reduce**  
   LangGraph **`Send`**s each bundle to **`summarize_one`**:  
   - `prompt == PROMPT_NONE` → **`summarize_passthrough`** (payload copied to report text).  
   - Otherwise → **`summarize_with_prompt`** (LLM + payload).  
   Partials are merged, then **`_reduce_node`** builds **`CreditSummaryGenAIResponse`**: sections and subsections ordered by **`bundle_config.yaml`**.

6. **Evaluate**  
   If an LLM is configured, **`_evaluate_node`** scores LLM-produced sections and the rendered report; passthrough sections are not scored as LLM summaries.

7. **Output**  
   You get structured JSON (Pydantic) and can render markdown via **`render_to_markdown`**.

---

## Sample flow (concrete)

**Goal:** Produce a credit-style report from `enrich_transform/raw.json`.

| Step | What happens | Example artifact |
|------|----------------|------------------|
| 1 | `invoke({"raw_path": ".../enrich_transform/raw.json", "bundle_config": load_bundle_config(...), ...})` | Graph starts at `enrich`. |
| 2 | `enrich_run` validates nested `data.data.legalEntities[...]` | `RawPayloadModel` OK or validation error. |
| 3 | `build_enriched_payload` flattens collaterals → aggregates | `enriched["collateral"]` with `aggregate` + `grand_total`. |
| 4 | Same for business model / real estate rows | `enriched["business_model"]`, `enriched["real_estate"]`. |
| 5 | `run_downstream_actions` | `downstream["business_model"]["json_str"]` = indented JSON string; `table_md` = markdown table for that section. |
| 6 | `_build_bundles_node` | Bundle `partner_shared_information`: markdown string. Bundle `collateral`: `json.dumps(enriched["collateral"])`. Bundle `business_model`: prompt + `json_str`. |
| 7 | `summarize_one` | Partner + collateral + real_estate: text = payload. Business model: LLM summary (if keys set) or error path per config. |
| 8 | `reduce` | One **SummarySection** per distinct `section_title` in YAML; each **Bundle** → **SummarySubSection**. |
| 9 | `evaluate` | Optional numeric scores on LLM sections + full report markdown. |

**CLI mirror:**  
`python -m map_reduce_arb.run_summarizer` sets `raw_path` to `enrich_transform/raw.json`, loads `bundle_config.yaml`, invokes the graph, writes `map_reduce_arb/pydantic_output.json`, and prints markdown.

---

## Sample JSON evolution across the pipeline

The examples below are **pedagogical**: one small collateral and one business-model row, no real-estate rows. Shapes match what **`build_enriched_payload`** and **`run_downstream_actions`** produce; numeric and date serializations in your environment may differ slightly (e.g. pandas timestamp formatting).

### Stage 1 — Raw input (`raw_obj`)

What enters **`enrich_transform.cli.run`** (and is also kept on graph state as **`raw_obj`** for Partner Shared Information).

```json
{
  "requestId": "doc-example-001",
  "metadata": { "creditSummaryScope": "group" },
  "client": { "id": "GRP-1", "partnerType": "GROUP" },
  "data": {
    "data": {
      "id": "deal-1",
      "legalEntities": [
        {
          "legalEntityIdGPID": "GRP-1",
          "entityType": "GROUP",
          "organizationName": "Alpine Holdings AG",
          "bankingRelations": [
            {
              "bankingRelationNumber": "BR-100",
              "isMainBR": true,
              "businessModel": [
                {
                  "overview": { "activities": ["Wholesale trade"] }
                }
              ],
              "collaterals": [
                {
                  "collateralId": "COL-1",
                  "collateralType": "REAL_ESTATE",
                  "currency": "CHF",
                  "lendingValueAmount": 500000,
                  "nominalValueAmount": 600000,
                  "lendingValueDate": "2026-03-01T00:00:00Z"
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

### Stage 2 — Enriched payload (`enriched`)

Output of **`build_enriched_payload`**: nested JSON, **not** yet the string sent to the LLM.

- **`collateral.aggregate`**: one row per `collateralId` after Pandas `groupby` (totals + latest date + `currency` forced to `"CHF"` in aggregation).
- **`collateral.grand_total`**: single object summing across aggregates.
- **`business_model`**: list of flat dicts; nested BM fragments become **JSON strings** on each key (see `overview` below).
- **`real_estate`**: `[]` when no `mortgageDeed.realestates` exist (as in this sample).

```json
{
  "collateral": {
    "aggregate": [
      {
        "collateralId": "COL-1",
        "collateralType": "REAL_ESTATE",
        "latest_lendingValueDate": "2026-03-01T00:00:00Z",
        "total_nominal_value": 600000,
        "total_lending_value": 500000,
        "currency": "CHF"
      }
    ],
    "grand_total": {
      "total_nominal_value": 600000,
      "total_lending_value": 500000,
      "unique_collateral_count": 1,
      "latest_lendingValueDate": "2026-03-01T00:00:00Z",
      "currency": "CHF"
    }
  },
  "business_model": [
    {
      "legalEntityId": "GRP-1",
      "relationId": "BR-100",
      "isMainBR": true,
      "overview": "{\"activities\": [\"Wholesale trade\"]}"
    }
  ],
  "real_estate": []
}
```

### Stage 3 — Downstream artifacts (`downstream`)

Output of **`run_downstream_actions`**: per section, **`json_str`** (canonical JSON text), **`table_md`**, **`summary`**, **`summary_md`**. Only **`business_model.json_str`** is shown here (truncation indicated); **`collateral`** / **`real_estate`** follow the same pattern.

```json
{
  "business_model": {
    "json_str": "{\n  \"legalEntityId\": \"GRP-1\",\n  \"relationId\": \"BR-100\",\n  ...\n}",
    "table_md": "## business_model\n\n| legalEntityId | relationId | ... |\n| --- | --- | --- |\n| GRP-1 | BR-100 | ... |",
    "summary": { "section": "business_model", "...": "..." },
    "summary_md": "..."
  }
}
```

In **`map_reduce_arb`**, the **business model** LLM bundle uses **`downstream["business_model"]["json_str"]`** as the **`payload`**. **Collateral** and **real estate** passthrough bundles instead stringify the Stage 2 **`enriched`** subtrees (so the report shows the enriched structure, not necessarily the same whitespace as `json_str`).

### Stage 4 — Bundles (`bundles` before split)

Logical content after **`_build_bundles_node`** ( **`prompt`** is `__NONE__` for passthrough, or a long template string for LLM; shown as labels).

| `field_name` | `prompt` | `payload` source (conceptual) |
|--------------|----------|-------------------------------|
| `partner_shared_information` | `PROMPT_NONE` | Markdown built from **Stage 1** `raw_obj` + merged metadata (e.g. group header + “no legal entities” if none listed). |
| `collateral` | `PROMPT_NONE` | `json.dumps(enriched["collateral"], indent=2, sort_keys=True)` |
| `business_model` | LLM prompt text | `downstream["business_model"]["json_str"]` |
| `real_estate` | `PROMPT_NONE` | `json.dumps(enriched["real_estate"], ...)` → often `"[]"` |

### Stage 5 — After map–reduce (`report`)

**`reduce`** turns each bundle’s final text into **`SummarySubSection`** entries grouped by **`section_title`** from **`bundle_config.yaml`**. Aliased JSON shape (illustrative):

```json
{
  "requestId": "…",
  "summary-sections": [
    {
      "identifier": "partner-shared-information",
      "heading": "Partner Shared Information",
      "summary-sub-sections": [
        {
          "identifier": "partner_shared_information",
          "heading": "Partner Shared Information",
          "content-format": "MD",
          "content": "- **Name:** Alpine Holdings AG\n- **GPID:** GRP-1\n\n### Legal entities\n_No legal entities listed._"
        }
      ]
    },
    {
      "identifier": "collateral",
      "heading": "Collateral",
      "summary-sub-sections": [
        {
          "identifier": "collateral",
          "heading": "collateral",
          "content-format": "JSON",
          "content": "{ \"aggregate\": [ ... ], \"grand_total\": { ... } }"
        }
      ]
    }
  ]
}
```

The **`content`** strings for passthrough sections are **literally** the Stage 4 payloads (possibly with format inference for `content-format`). The **business model** subsection would contain **LLM narrative** when credentials are present, or raise/fallback depending on your **`agents.py`** configuration.

### End-to-end mental model

```text
Stage 1 raw_obj
    → enrich_transform validates + build_enriched_payload → Stage 2 enriched
    → run_downstream_actions → Stage 3 downstream
    → map_reduce_arb _build_bundles_node → Stage 4 bundles (raw + enriched + downstream)
    → summarize_one (passthrough / LLM) → partials
    → reduce → Stage 5 CreditSummaryGenAIResponse
```

You can paste **Stage 1** into a file and run `enrich_transform.cli.run(raw_path=...)` in a REPL to compare your machine’s **Stage 2–3** output to the shapes above.

---

## Configuration knobs

- **`map_reduce_arb/bundle_config.yaml`** — `field_name`, `section_title`, `order`, optional `display_name`. Must align with bundles produced in `_build_bundles_node`.
- **`map_reduce_arb/prompts.py`** — `get_prompt_for_section`: `PROMPT_NONE` = passthrough; otherwise LLM prompt text.
- **`enrich_transform`** — Section list in `run_downstream_actions(..., sections=[...])` defaults to `collateral`, `business_model`, `real_estate`; enrich keys must stay consistent with bundle builder expectations.

---

## Related files

| Area | Files |
|------|--------|
| Enrich pipeline | `enrich_transform/cli.py`, `enrich_transform/pipeline/build_enriched.py`, `enrich_transform/pipeline/normalize.py`, `enrich_transform/actions/dispatcher.py` |
| Graph | `map_reduce_arb/graph.py`, `map_reduce_arb/prompts.py`, `map_reduce_arb/agents.py` |
| Partner block | `map_reduce_arb/partner_shared_info.py`, `map_reduce_arb/update.md` |
| Report shape | `map_reduce_arb/report_schemas.py` |

Diagrams use [Mermaid](https://mermaid.js.org/); they render in GitHub, many IDEs, and static site generators that support fenced `mermaid` code blocks.
