from pathlib import Path
import sys
import os
import json
import orjson

# Ensure project root is on sys.path when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from etl.normalize import to_sqm, normalize_currency
from etl.dedupe import dedupe_records
from extractor.schema import validate_listing
from etl.geocode import geocode_address, neighborhood_from_geojson
from extractor.llm_ollama import OllamaExtractor


def main() -> None:
    data_path = Path('data/listings.json')
    recs = json.loads(data_path.read_text()) if data_path.exists() else []
    total = len(recs)
    cleaned = []
    llm_attempts = 0
    llm_success = 0

    use_ollama = os.getenv("AI_SCRAPER_USE_OLLAMA", "1").lower() in ("1", "true", "yes", "on")
    ollama_timeout = int(os.getenv("AI_SCRAPER_OLLAMA_TIMEOUT", "5"))
    extractor = OllamaExtractor(timeout=ollama_timeout) if use_ollama else None

    for r in recs:
        r['currency'] = normalize_currency(r.get('currency'))
        if r.get('area') and r.get('area_unit'):
            r['area_sqm'] = to_sqm(r['area'], r['area_unit'])
        try:
            v = validate_listing(r)
        except Exception as e:
            v = None
            print(orjson.dumps({"event": "validation_error", "phase": "pre_llm", "url": r.get('url'), "error": str(e)}).decode())

        if v is None and extractor is not None:
            llm_attempts += 1
            html = None
            raw_path = r.get('raw_html_path')
            try:
                if raw_path and Path(raw_path).exists():
                    html = Path(raw_path).read_text(encoding='utf-8', errors='ignore')
            except Exception:
                html = None
            if html:
                out = extractor.extract(url=r.get('url', ''), title=r.get('title'), html=html)
                if out is not None:
                    llm_success += 1
                    v = out
                else:
                    print(orjson.dumps({"event": "llm_fallback_failed", "url": r.get('url')}).decode())

        if v is not None:
            cleaned.append(v.model_dump())

    for r in cleaned:
        if not r.get('latitude') and r.get('address'):
            gc = geocode_address(r['address'])
            if gc:
                r['latitude'], r['longitude'] = gc

    gj_path = Path('config/neighborhoods.geojson')
    if gj_path.exists():
        for r in cleaned:
            if r.get('latitude') and r.get('longitude'):
                n = neighborhood_from_geojson(r['latitude'], r['longitude'], str(gj_path))
                if n:
                    r['neighborhood'] = n

    deduped = dedupe_records(cleaned)
    report = {"total": total, "cleaned": len(cleaned), "deduped": len(deduped), "llm_attempts": llm_attempts, "llm_success": llm_success}
    Path('data/report.json').write_text(orjson.dumps(report).decode())
    print(orjson.dumps({"event": "report", "report": report}).decode())

    from etl.load_d1 import generate_upsert_sql
    sql = generate_upsert_sql(deduped)
    Path('data/upload.sql').write_text(sql)


if __name__ == '__main__':
    main()
