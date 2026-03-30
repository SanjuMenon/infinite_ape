from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def read_json(path: str | Path) -> Any:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _to_iso_z(value: Any) -> Any:
    """Convert pandas Timestamp/datetime to an ISO-8601 string with a trailing 'Z'."""
    if isinstance(value, pd.Timestamp):
        dt = value.to_pydatetime()
    elif isinstance(value, datetime):
        dt = value
    else:
        return value

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    # Assume naive datetimes are UTC.
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def dataframe_to_json_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = df.to_dict(orient="records")
    out: list[dict[str, Any]] = []
    for r in records:
        row: dict[str, Any] = {}
        for k, v in r.items():
            if pd.isna(v):
                row[k] = None
            else:
                row[k] = _to_iso_z(v)
        out.append(row)
    return out

