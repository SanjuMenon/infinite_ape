# Why “Declarative Field Pipelines” + “Map-Reduce” Works Well

This approach combines **two complementary ideas**:

- A **declarative, field-by-field pipeline** that decides *what to do* for each field (validate, normalize, calculate, etc.) based on configuration.
- A **map-reduce workflow** that can *scale out* processing (summarize many fields in parallel) and then *scale in* to assemble a single coherent report.

The result is a system that is **highly configurable and reusable**, and that can evolve with **minimal rewrites**.

## The separation of concerns (the key design principle)

### Declarative field pipelines answer: “How do we produce a clean, usable payload per field?”

Each field has an ordered series of “states” or “steps” that run **sequentially**. Each step can:

- check completeness (“do we have enough data?”)
- validate type/format/constraints (“is the data usable?”)
- normalize into a canonical shape (“make downstream stable”)
- compute derived values (“add calculated metrics”)
- decide a preferred presentation (“table vs narrative”)

Because the pipeline is **configuration-driven**, evolving requirements usually mean changing the *configuration of steps* (add a step, reorder steps, tune validation), rather than rewriting downstream logic.

### Map-reduce answers: “How do we turn many field payloads into one report efficiently?”

Map-reduce treats each field payload as a unit of work:

- **Map**: optionally split a field into smaller subtasks (useful when one field contains multiple independent sub-entities)
- **Process in parallel**: run the appropriate “agent” (table-style vs freeform) for each unit of work
- **Reduce**: merge partial results deterministically into a single structured report
- **Optional evaluation**: score quality (per-field and overall) as a separate, sequential post-step

This keeps summarization/reporting independent from how the field payloads were produced.

## Why this makes the whole system more configurable and reusable

### 1) Adding or changing fields becomes mostly configuration work

In many systems, “new field” means new bespoke code paths. Here, a new field is typically:

- a new pipeline definition (what validations/calculations/normalizations should run)
- a decision about its summary format (table vs narrative)
- a placement decision in the final report (which section, which order)

The core summarization and aggregation mechanics don’t need to know what the field “means”.

### 2) A stable “bundle” contract prevents downstream churn

A critical trick is to treat each field’s output as a **bundle** with a clear contract:

- **The “most current” canonical data** that downstream should summarize
- **The requested output format** (table vs freeform)
- Optional evaluation instructions (metrics to score)
- Any extra metadata (allowed, but not required for summarization)

If you keep summarization focused on the canonical “most current” data, upstream changes (new validation flags, extra context, debugging metadata) don’t break downstream prompts, tables, or report assembly.

### 3) Parallelism is a natural fit (and it stays simple as you scale)

As you add more fields—or eventually split a field into multiple subtasks—you don’t want processing time to grow linearly.

Map-reduce keeps the structure stable:

- fan out work units
- process independently (often in parallel)
- fan in results with deterministic merging

That makes the system more robust as the number of fields grows.

### 4) Evaluation becomes a clean “post-processing” layer

Quality evaluation (e.g., scoring readability/completeness/accuracy) is valuable, but it can easily tangle the main workflow.

Treating evaluation as a **separate step after aggregation** makes it:

- optional (only runs when requested)
- replaceable (you can change metrics/prompting without touching the core)
- safe (failures in evaluation need not break report generation)

### 5) Report structure stays configurable as stakeholder needs change

Report organization changes constantly: new sections, reordered sections, renamed headings, grouped fields, etc.

When report structure is driven by configuration (rather than hard-coded), you can reorganize the output without rewriting summarizers or field logic.

## What “evolution without rewrites” looks like in practice

- **New calculation requested**: add a calculation step to the field pipeline; summarization automatically sees the computed outputs in the canonical payload.
- **A field should become a table**: change the field’s requested format to “table”; the rest of the system stays the same.
- **A field should be split into multiple subtasks**: define the splitting rule; map-reduce naturally handles many subtasks and merges them.
- **The report needs a new section layout**: change the configuration for grouping and ordering; no core logic changes.


