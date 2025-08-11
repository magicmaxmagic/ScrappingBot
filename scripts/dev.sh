#!/usr/bin/env bash
set -euo pipefail

# Simple dev helper to run a local crawl and ETL
python -m pip install -r requirements.txt
python -m playwright install chromium

mkdir -p data
python -m scrapy crawl site_generic -s LOG_LEVEL=INFO -s FEEDS={"data/listings.json":{"format":"json","encoding":"utf8","overwrite":true}}

python - <<'PY'
import json, orjson
from pathlib import Path
from etl.normalize import to_sqm, normalize_currency
from etl.dedupe import dedupe_records
from extractor.schema import validate_listing

recs = json.loads(Path('data/listings.json').read_text()) if Path('data/listings.json').exists() else []
cleaned = []
for r in recs:
    r['currency'] = normalize_currency(r.get('currency'))
    if r.get('area') and r.get('area_unit'):
        r['area_sqm'] = to_sqm(r['area'], r['area_unit'])
    try:
        v = validate_listing(r)
        cleaned.append(v.model_dump())
    except Exception as e:
        print(orjson.dumps({"event":"validation_error","url":r.get('url'),"error":str(e)}).decode())

from etl.load_d1 import generate_upsert_sql
sql = generate_upsert_sql(deduped := dedupe_records(cleaned))
Path('data/upload.sql').write_text(sql)
print(f"Generated SQL with {len(deduped)} rows")
PY
