from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import yaml

from .schemas import BundleConfig, OutputSchema


PathLike = Union[str, Path]


def load_bundle_config(path: PathLike) -> BundleConfig:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    
    # Support both YAML and JSON
    if p.suffix.lower() in ('.yaml', '.yml'):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    
    return BundleConfig.model_validate(data)


def load_output_schema(path: PathLike) -> OutputSchema:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return OutputSchema.model_validate(data)

