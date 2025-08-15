from pathlib import Path
import sys
import os
import json
import orjson
from typing import Optional, Protocol, Any

# Define a protocol so type checkers know the extractor exposes an extract(...) method.
class ExtractorProtocol(Protocol):
    def extract(self, url: str, title: Optional[str] = None, html: Optional[str] = None) -> Any: ...

# Ensure project root (and optional "src" dir) are on sys.path when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# If the repository uses a top-level "src" directory for packages, add it too
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import importlib

def _import(name: str, attr: Optional[str] = None):
    try:
        module = importlib.import_module(name)
        return getattr(module, attr) if attr else module
    except Exception as e:
        raise ImportError(f"Could not import {name}{'.' + attr if attr else ''}: {e}")
        raise ImportError(f"Could not import {name}{'.' + attr if attr else ''}: {e}")

def _resolve_callable(obj, *candidate_names):
    # If it's already callable, return it.
    if callable(obj):
        return obj
    # If it's a module-like object, try to find a callable attribute.
    for name in candidate_names:
        if hasattr(obj, name) and callable(getattr(obj, name)):
            return getattr(obj, name)
    # Fall back to the original object (may raise later if used incorrectly).
    return obj

to_sqm = _resolve_callable(_import("etl.normalize"), "to_sqm", "convert", "to_square_meters")
normalize_currency = _resolve_callable(_import("etl.normalize"), "normalize_currency", "normalize")
dedupe_records = _resolve_callable(_import("etl.dedupe"), "dedupe_records", "dedupe")
validate_listing = _resolve_callable(_import("extractor.schema"), "validate_listing")
geocode_address = _resolve_callable(_import("etl.geocode"), "geocode_address", "geocode")
neighborhood_from_geojson = _resolve_callable(_import("etl.geocode"), "neighborhood_from_geojson")
OllamaExtractor = _resolve_callable(_import("extractor.llm_ollama"), "OllamaExtractor", "Ollama")


def main() -> None:
    data_path = Path('data/listings.json')
    recs = json.loads(data_path.read_text()) if data_path.exists() else []
    total = len(recs)
    use_ollama = os.getenv("AI_SCRAPER_USE_OLLAMA", "1").lower() in ("1", "true", "yes", "on")
    ollama_timeout = int(os.getenv("AI_SCRAPER_OLLAMA_TIMEOUT", "5"))
    extractor: Optional[ExtractorProtocol] = None
    if use_ollama:
    use_ollama = os.getenv("AI_SCRAPER_USE_OLLAMA", "1").lower() in ("1", "true", "yes", "on")
    ollama_timeout = int(os.getenv("AI_SCRAPER_OLLAMA_TIMEOUT", "5"))
    extractor = None
    if use_ollama:
        try:
            # OllamaExtractor may be the class/function itself or a module that exposes the class
            if callable(OllamaExtractor):
                extractor = OllamaExtractor(timeout=ollama_timeout)
            else:
                candidate = getattr(OllamaExtractor, "OllamaExtractor", None)
                if callable(candidate):
                    extractor = candidate(timeout=ollama_timeout)
                else:
                    raise TypeError("OllamaExtractor is not callable and does not expose a callable 'OllamaExtractor'")
        except Exception as e:
            print(orjson.dumps({"event": "ollama_init_failed", "error": str(e)}).decode())
            extractor = None

    for r in recs:
        cur = r.get('currency')
        if callable(normalize_currency):
            r['currency'] = normalize_currency(cur)
        elif hasattr(normalize_currency, 'normalize_currency') and callable(getattr(normalize_currency, 'normalize_currency')):
            r['currency'] = normalize_currency.normalize_currency(cur)
        elif hasattr(normalize_currency, 'normalize') and callable(getattr(normalize_currency, 'normalize')):
            r['currency'] = normalize_currency.normalize(cur)
        else:
            # unknown shape (module without a callable); keep original value
            r['currency'] = cur
        if r.get('area') and r.get('area_unit'):
            area = r['area']
            unit = r['area_unit']
            if callable(to_sqm):
                r['area_sqm'] = to_sqm(area, unit)
            elif hasattr(to_sqm, 'to_sqm') and callable(getattr(to_sqm, 'to_sqm')):
                r['area_sqm'] = to_sqm.to_sqm(area, unit)
            elif hasattr(to_sqm, 'convert') and callable(getattr(to_sqm, 'convert')):
                r['area_sqm'] = to_sqm.convert(area, unit)
            elif hasattr(to_sqm, 'to_square_meters') and callable(getattr(to_sqm, 'to_square_meters')):
                r['area_sqm'] = to_sqm.to_square_meters(area, unit)
            else:
                # unknown shape (module without expected callable); try a safe fallback
                try:
                    r['area_sqm'] = float(area)
                except Exception:
                    r['area_sqm'] = None
        try:
            # validate_listing may be a direct callable, or a module exposing a function.
            if callable(validate_listing):
                v = validate_listing(r)
            elif hasattr(validate_listing, 'validate_listing') and callable(getattr(validate_listing, 'validate_listing')):
                v = validate_listing.validate_listing(r)
            elif hasattr(validate_listing, 'validate') and callable(getattr(validate_listing, 'validate')):
                v = validate_listing.validate(r)
            else:
                # As a last resort try importing the expected function directly from the module.
                mod = _import("extractor.schema")
                func = getattr(mod, "validate_listing", None)
                if callable(func):
                    v = func(r)
                else:
                    raise TypeError("validate_listing is not callable")
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
