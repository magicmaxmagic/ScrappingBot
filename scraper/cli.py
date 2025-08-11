from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field

# Minimal schema for the CLI (align with extractor.schema if desired)
class Filters(BaseModel):
    kind: str | None = None
    min_size: float | None = None
    max_size: float | None = None
    min_price: float | None = None
    max_price: float | None = None


def parse_what(what: str | None) -> Filters:
    # e.g., "rent;size>=20;price<=1500"
    f = Filters()
    if not what:
        return f
    parts = [p.strip() for p in what.split(';') if p.strip()]
    for p in parts:
        if p in ("rent", "sale"):
            f.kind = p
        elif p.startswith("size>="):
            f.min_size = float(p.split(">=")[1])
        elif p.startswith("size<="):
            f.max_size = float(p.split("<=")[1])
        elif p.startswith("price>="):
            f.min_price = float(p.split(">=")[1])
        elif p.startswith("price<="):
            f.max_price = float(p.split("<=")[1])
    return f


def load_sources(path: str | None) -> Dict[str, Any]:
    import yaml
    p = Path(path or 'sources.yml')
    return yaml.safe_load(p.read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--where')
    ap.add_argument('--what')
    ap.add_argument('--when')
    ap.add_argument('--polygon')
    ap.add_argument('--sources', default='sources.yml')
    ap.add_argument('--out', default='data/listings.json')
    args = ap.parse_args()

    filters = parse_what(args.what)
    sources = load_sources(args.sources)

    # Placeholder: in a real run, we'd orchestrate playwright/httpx per source
    # For now, just read existing data/listings.json and filter to demonstrate flow
    out_path = Path(args.out)
    if out_path.exists():
        recs = json.loads(out_path.read_text())
    else:
        recs = []

    def match(r: Dict[str, Any]) -> bool:
        if filters.kind and r.get('kind') != filters.kind:
            return False
        if filters.min_size and (r.get('area_sqm') or 0) < filters.min_size:
            return False
        if filters.max_size and (r.get('area_sqm') or 0) > filters.max_size:
            return False
        if filters.min_price and (r.get('price') or 0) < filters.min_price:
            return False
        if filters.max_price and (r.get('price') or 0) > filters.max_price:
            return False
        return True

    filtered = [r for r in recs if match(r)]
    Path(args.out).write_text(json.dumps(filtered, indent=2))
    print(json.dumps({"event": "scraper_done", "count": len(filtered)}))


if __name__ == '__main__':
    main()
