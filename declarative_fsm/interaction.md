## Declarative FSM — Interaction (Sequence Diagram)

This describes the **runtime interaction** between `demo.py`, the `FSMEngine`, and the `strategy` handlers using the **current** `declarative_fsm/example_config.yaml`.

### Key ideas reflected in the diagram

- **Per-field execution**: each field gets its own `context` (aka bundle), and all strategies/states for that field share it.
- **Linear state execution**: states execute in YAML order; fail-fast on first failure.
- **Nested/conditional execution**: a strategy’s nested strategies only run if the parent strategy passes.
- **Data tracking**:
  - `context["most_current_data"]` starts as a deep copy of the field’s raw input.
  - Handlers may update `most_current_data` **only on success**.
  - If a state fails, `most_current_data` is reverted to the previous successful snapshot.
- **Bundle output**: the final `context` is stored as `field_result["bundle"]` and also collected into `most_current_data_list` (later pickled by `demo.py`).

### Sequence diagram (Mermaid)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Demo as demo.py main
  participant Loader as loader.py load_config
  participant Engine as engine.py FSMEngine.execute
  participant Strategy as strategy.py execute_state
  participant H as state handler
  participant FS as filesystem most_current_data.pkl

  User->>Demo: run demo

  Demo->>Loader: load_config(example_config.yaml)
  Loader-->>Demo: config (validated)

  Demo->>Demo: load JSON data (sample_data.json)

  Demo->>Engine: engine.execute(data)

  loop for each field in config.fields
    Engine->>Engine: context = {}
    Engine->>Engine: context["most_current_data"] = deepcopy(raw_field_data)
    Engine->>Engine: context["canonical_mapping"] = canonical_mappings.get(field_name, {})

    Engine->>Strategy: field_selection_strategy / check_completeness
    Strategy->>H: check_completeness_handler
    alt completeness passes
      H-->>Strategy: True (sets required_fields_found, field_data)
      Strategy-->>Engine: True
      Engine->>Strategy: field_selection_strategy / convert_to_canon
      Strategy->>H: convert_to_canon_handler
      alt convert_to_canon passes
        H-->>Strategy: True (may rename keys in most_current_data)
        Strategy-->>Engine: True
      else convert_to_canon fails
        Strategy-->>Engine: False
        Engine->>Engine: revert most_current_data snapshot and stop branch
      end
    else completeness fails
      Strategy-->>Engine: False
      Engine->>Engine: revert most_current_data snapshot and stop branch
    end

    Engine->>Strategy: extraction_strategy / validate_type
    Strategy->>H: extraction_validate_type_handler
    alt validate_type passes
      H-->>Strategy: True (may convert numeric strings; updates most_current_data on success)
      Strategy-->>Engine: True
    else validate_type fails
      Strategy-->>Engine: False
      Engine->>Engine: revert most_current_data snapshot and stop branch
    end

    Engine->>Strategy: generation_strategy / format
    Strategy->>H: generation_format_handler
    alt format valid (enum)
      H-->>Strategy: True (sets context["format"] = table|freeform|fill_template)
      Strategy-->>Engine: True
    else format invalid
      Strategy-->>Engine: False
      Engine->>Engine: revert most_current_data snapshot and stop branch
    end

    Engine->>Strategy: validation_strategy / llm_eval
    Strategy->>H: validation_llm_eval_handler
    alt llm_eval description is list
      H-->>Strategy: True (sets context["eval_type"]=llm; context["metrics"]=list)
      Strategy-->>Engine: True
    else invalid metrics
      Strategy-->>Engine: False
      Engine->>Engine: revert most_current_data snapshot and stop branch
    end

    opt if calculation_strategy is present
      Engine->>Strategy: calculation_strategy / calculation
      Strategy->>H: calculation_handler
      alt description == "aggregation"
        H-->>Strategy: True (adds most_current_data["aggregation"] = grouped sums)
        Strategy-->>Engine: True
      else description == "debt_capacity"
        H-->>Strategy: True/False (calls debt_capacity(); updates most_current_data on success)
        Strategy-->>Engine: result
      end
    end

    Engine->>Engine: field_result["bundle"] = context
    Engine->>Engine: most_current_data_list.append({field_name, most_current_data, eval_type, metrics, format})
  end

  Engine-->>Demo: report (includes most_current_data_list)

  Demo->>FS: pickle.dump(most_current_data_list, map_reduce/most_current_data.pkl)
  FS-->>Demo: write OK

  Demo-->>User: console report + returns most_current_data_list
```

### What the current config implies (quick mapping)

- **All fields** run:
  - `field_selection_strategy.check_completeness` → `convert_to_canon`
  - `extraction_strategy.validate_type`
  - `generation_strategy.format` (sets `context["format"]`)
  - `validation_strategy.llm_eval` (sets `context["eval_type"]` + `context["metrics"]`)
- **`Financials`** additionally runs:
  - `calculation_strategy.calculation` with `description: "aggregation"` (writes `most_current_data["aggregation"]`)
- **`financials_debt`** additionally runs:
  - `calculation_strategy.calculation` with `description: "debt_capacity"` (calls `debt_capacity()` and updates `most_current_data` on success)

