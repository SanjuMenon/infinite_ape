# Replacing PyGlove: Analysis and Proposal

## Current PyGlove Usage

Based on the codebase analysis, PyGlove is being used for:

1. **Symbolic Objects** (`pg.Object`) - Base class for all spec classes
2. **Typed Dicts** (`pg.Dict[str, T]`) - Type-safe nested dictionaries
3. **In-place Mutation** (`rebind()`) - Modifying nested structures incrementally
4. **Serialization** - Saving/loading specs (though `to_dict()`/`from_dict()` don't work)

## The Problem

After 14 strategies, we've discovered that **PyGlove cannot initialize `None` Dict fields to typed Dicts**, regardless of how we create or pass them. This is a fundamental limitation that blocks our use case.

## Proposed Alternative: Pydantic v2

**Why Pydantic?**
- ✅ Already used in the codebase for `ChangeSet` validation
- ✅ Strong type safety and validation
- ✅ Built-in serialization (`model_dump()`, `model_validate()`)
- ✅ Supports nested structures with `Dict[str, T]`
- ✅ Mutable models (can modify fields directly)
- ✅ `model_copy()` for creating modified copies (similar to `rebind()`)
- ✅ Well-documented and widely used
- ✅ No issues with empty Dict initialization

## Migration Plan

### 1. Replace `pg.Object` with `pydantic.BaseModel`

**Before (PyGlove):**
```python
class FieldSpec(pg.Object):
    name: str
    type: str
    optional: bool = False
```

**After (Pydantic):**
```python
from pydantic import BaseModel

class FieldSpec(BaseModel):
    name: str
    type: str
    optional: bool = False
```

### 2. Replace `pg.Dict[str, T]` with `dict[str, T]`

**Before (PyGlove):**
```python
fields: pg.Dict[str, FieldSpec] | None = None
```

**After (Pydantic):**
```python
fields: dict[str, FieldSpec] | None = None
```

### 3. Replace `rebind()` with direct assignment or `model_copy()`

**Before (PyGlove):**
```python
spec.classes.rebind({change.class_name: class_spec})
```

**After (Pydantic):**
```python
# Option A: Direct assignment (if field exists)
if spec.classes is None:
    spec.classes = {change.class_name: class_spec}
else:
    spec.classes[change.class_name] = class_spec

# Option B: model_copy() for immutable-style updates
spec = spec.model_copy(update={"classes": {**spec.classes, change.class_name: class_spec}})
```

### 4. Replace serialization

**Before (PyGlove - doesn't work):**
```python
spec_dict = spec.to_dict()  # Doesn't exist
spec = SdkSpec.from_dict(spec_dict)  # Doesn't exist
```

**After (Pydantic):**
```python
spec_dict = spec.model_dump()  # Works!
spec = SdkSpec.model_validate(spec_dict)  # Works!
```

## Benefits

1. **No Dict initialization issues** - Regular Python dicts work fine
2. **Simpler code** - No need for `rebind()`, just direct assignment
3. **Better serialization** - Built-in `model_dump()`/`model_validate()`
4. **Consistent with existing code** - Already using Pydantic for ChangeSet
5. **Better error messages** - Pydantic has excellent validation errors
6. **Type safety** - Still maintains type safety with type hints

## Migration Steps

1. **Update `spec/model.py`** - Replace all `pg.Object` with `BaseModel`, `pg.Dict` with `dict`
2. **Update `patching/apply.py`** - Replace `rebind()` calls with direct assignment
3. **Update `storage/persistence.py`** - Replace serialization with `model_dump()`/`model_validate()`
4. **Update tests** - Adjust test code to use Pydantic patterns
5. **Remove PyGlove dependency** - Update `requirements.txt` and `pyproject.toml`

## Estimated Effort

- **Low** - Most changes are straightforward find/replace
- **Time**: ~2-3 hours for full migration
- **Risk**: Low - Pydantic is well-tested and widely used

## Alternative: Plain Python Classes

If we want even simpler, we could use plain Python classes with `@dataclass`:

**Pros:**
- No external dependencies (beyond standard library)
- Very simple and straightforward
- No type system complexity

**Cons:**
- No built-in validation
- No serialization (need to implement manually)
- Less type safety

## Recommendation

**Use Pydantic v2** - It's the best balance of features, simplicity, and compatibility with our existing codebase.
