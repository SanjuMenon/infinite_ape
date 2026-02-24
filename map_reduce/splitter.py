from __future__ import annotations

from typing import List

from .schemas import Bundle


def split_bundle(bundle: Bundle) -> List[Bundle]:
    """General splitter (currently no-op).

    Later you can replace/extend this with configurable splitting rules per bundle type.
    """

    return [bundle]

