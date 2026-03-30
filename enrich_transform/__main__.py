from __future__ import annotations

import argparse
import json

from enrich_transform.cli import main

if __name__ == "__main__":
    # Running as a module: we intentionally do not persist anything by default.
    # If you need files, pass `--write-enriched-json` / `--write-downstream-dir`.
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--quiet",
        action="store_true",
        help="If set, do not print the returned payload to stdout.",
    )
    known, _unknown = p.parse_known_args()

    result = main()
    if not known.quiet:
        print(json.dumps(result, ensure_ascii=True, indent=2))

