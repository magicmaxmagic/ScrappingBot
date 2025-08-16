from pathlib import Path
import sys
import os
import json
import orjson
from typing import Optional, Protocol, Any, cast, Iterable, List, Dict, Callable
from collections.abc import Mapping

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

    # initialize working state
    cleaned = []
    llm_attempts = 0
    llm_success = 0

    if use_ollama:
        try:
            # OllamaExtractor may be the class/function itself or a module that exposes the class
            if callable(OllamaExtractor):
                extractor = cast(ExtractorProtocol, OllamaExtractor(timeout=ollama_timeout))
            else:
                candidate = getattr(OllamaExtractor, "OllamaExtractor", None)
                if callable(candidate):
                    extractor = cast(ExtractorProtocol, candidate(timeout=ollama_timeout))
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
            # Accept pydantic v2 (model_dump) or v1 (dict), dataclasses, plain dicts, or objects with __dict__
            _method = getattr(v, "model_dump", None)
            if callable(_method):
                cleaned.append(_method())
            else:
                _method = getattr(v, "dict", None)
                if callable(_method):
                    cleaned.append(_method())
                elif isinstance(v, dict):
                    cleaned.append(v)
                else:
                    try:
                        import dataclasses as _dc
                        # Only call asdict on dataclass instances, not on dataclass types
                        if _dc.is_dataclass(v) and not isinstance(v, type):
                            cleaned.append(_dc.asdict(v))
                        elif _dc.is_dataclass(v) and isinstance(v, type):
                            # Convert a dataclass type to a dict of default values (or None if missing)
                            defaults = {}
                            for f in getattr(v, "__dataclass_fields__", {}).values():
                                name = f.name
                                if f.default is not _dc.MISSING:
                                    defaults[name] = f.default
                                elif getattr(f, "default_factory", _dc.MISSING) is not _dc.MISSING:
                                    try:
                                        defaults[name] = f.default_factory()
                                    except Exception:
                                        defaults[name] = None
                                else:
                                    defaults[name] = None
                            cleaned.append(defaults)
                        else:
                            # try to get a dict-like representation from the object
                            cleaned.append(vars(v))
                    except Exception:
                        # final fallback: append the raw value
                        cleaned.append(v)

    for r in cleaned:
        if not r.get('latitude') and r.get('address'):
            gc = None
            try:
                if callable(geocode_address):
                    gc = geocode_address(r['address'])
                elif hasattr(geocode_address, 'geocode_address') and callable(getattr(geocode_address, 'geocode_address')):
                    gc = geocode_address.geocode_address(r['address'])
                elif hasattr(geocode_address, 'geocode') and callable(getattr(geocode_address, 'geocode')):
                    gc = geocode_address.geocode(r['address'])
                else:
                    # As a last resort try importing the expected function directly from the module.
                    mod = _import("etl.geocode")
                    func = getattr(mod, "geocode_address", None) or getattr(mod, "geocode", None)
                    if callable(func):
                        gc = func(r['address'])
                    else:
                        raise TypeError("geocode_address is not callable")
            except Exception as e:
                print(orjson.dumps({"event": "geocode_error", "address": r.get('address'), "error": str(e)}).decode())
                gc = None
            if gc:
                # Accept a variety of shapes from geocode: (lat, lon), [lat, lon], {'lat':..,'lon':..}, {'latitude':..,'longitude':..}
                lat = lon = None
                try:
                    if isinstance(gc, (list, tuple)) and len(gc) >= 2:
                        lat = float(gc[0])
                        lon = float(gc[1])
                    elif isinstance(gc, dict):
                        # try common key pairs
                        if 'latitude' in gc and 'longitude' in gc:
                            try:
                                lat = float(gc['latitude'])
                                lon = float(gc['longitude'])
                            except Exception:
                                lat = lon = None
                        elif 'lat' in gc and ('lon' in gc or 'lng' in gc):
                            # ensure we don't pass None (or unknown) into float()
                            lon_val = gc.get('lon', gc.get('lng'))
                            try:
                                if lon_val is None:
                                    raise ValueError("missing longitude value")
                                lat = float(gc['lat'])
                                lon = float(lon_val)
                            except Exception:
                                lat = lon = None
                    else:
                        # object with attributes
                        if hasattr(gc, 'latitude') and hasattr(gc, 'longitude'):
                            lat = float(getattr(gc, 'latitude'))
                            lon = float(getattr(gc, 'longitude'))
                        elif hasattr(gc, 'lat') and (hasattr(gc, 'lon') or hasattr(gc, 'lng')):
                            lat = float(getattr(gc, 'lat'))
                            lon = float(getattr(gc, 'lon') if hasattr(gc, 'lon') else getattr(gc, 'lng'))
                except Exception:
                    lat = lon = None

                if lat is not None and lon is not None:
                    r['latitude'] = lat
                    r['longitude'] = lon

    gj_path = Path('config/neighborhoods.geojson')
    if gj_path.exists():
        for r in cleaned:
            if r.get('latitude') and r.get('longitude'):
                try:
                    if callable(neighborhood_from_geojson):
                        n = neighborhood_from_geojson(r['latitude'], r['longitude'], str(gj_path))
                    elif hasattr(neighborhood_from_geojson, 'neighborhood_from_geojson') and callable(getattr(neighborhood_from_geojson, 'neighborhood_from_geojson')):
                        n = neighborhood_from_geojson.neighborhood_from_geojson(r['latitude'], r['longitude'], str(gj_path))
                    elif hasattr(neighborhood_from_geojson, 'from_geojson') and callable(getattr(neighborhood_from_geojson, 'from_geojson')):
                        n = neighborhood_from_geojson.from_geojson(r['latitude'], r['longitude'], str(gj_path))
                    else:
                        mod = _import("etl.geocode")
                        func = getattr(mod, "neighborhood_from_geojson", None) or getattr(mod, "from_geojson", None)
                        if callable(func):
                            n = func(r['latitude'], r['longitude'], str(gj_path))
                        else:
                            raise TypeError("neighborhood_from_geojson is not callable")
                except Exception as e:
                    print(orjson.dumps({"event": "neighborhood_error", "lat": r.get('latitude'), "lon": r.get('longitude'), "error": str(e)}).decode())
                    n = None
                if n:
                    r['neighborhood'] = n

    try:
        if callable(dedupe_records):
            deduped = dedupe_records(cleaned)
        elif hasattr(dedupe_records, 'dedupe_records') and callable(getattr(dedupe_records, 'dedupe_records')):
            deduped = dedupe_records.dedupe_records(cleaned)
        elif hasattr(dedupe_records, 'dedupe') and callable(getattr(dedupe_records, 'dedupe')):
            deduped = dedupe_records.dedupe(cleaned)
        else:
            # As a last resort try importing the expected function directly from the module.
            mod = _import("etl.dedupe")
            func = getattr(mod, "dedupe_records", None) or getattr(mod, "dedupe", None)
            if callable(func):
                deduped = func(cleaned)
            else:
                raise TypeError("dedupe_records is not callable")
    except Exception as e:
        print(orjson.dumps({"event": "dedupe_error", "error": str(e)}).decode())
        # On error, fall back to using the cleaned list as-is
        deduped = cleaned

    # Ensure we have a list-like value for sizing and further processing so type checkers are satisfied.
    if isinstance(deduped, list):
        final_deduped = deduped
    else:
        # If deduped isn't a list, fall back to cleaned (which is a list), or try to coerce if it's iterable.
        if isinstance(cleaned, list):
            final_deduped = cleaned
        else:
            try:
                if hasattr(deduped, '__iter__') and not isinstance(deduped, (str, bytes)):
                    # cast to Iterable[Any] so static type checkers accept passing to list(...)
                    final_deduped = list(cast(Iterable[Any], deduped))
                else:
                    final_deduped = [deduped]
            except Exception:
                final_deduped = list(cleaned)

    report = {"total": total, "cleaned": len(cleaned), "deduped": len(final_deduped), "llm_attempts": llm_attempts, "llm_success": llm_success}
    Path('data/report.json').write_text(orjson.dumps(report).decode())
    print(orjson.dumps({"event": "report", "report": report}).decode())

    from etl.load_d1 import generate_upsert_sql

    # Coerce final_deduped into a List[Dict[str, Any]] so the generate_upsert_sql signature is satisfied.
    listings: List[Dict[str, Any]] = []
    for item in final_deduped:
        if isinstance(item, dict):
            listings.append(item)
            continue

        # Try common conversions: dataclass -> asdict, mapping -> dict(item), vars(...)
        converted = None
        try:
            import dataclasses as _dc
            if _dc.is_dataclass(item) and not isinstance(item, type):
                converted = _dc.asdict(item)
        except Exception:
            converted = None
        if converted is None:
            try:
                # Prefer Mapping (safe)
                if isinstance(item, Mapping):
                    converted = dict(item)
                else:
                    # If it has an items() method but isn't a Mapping, retrieve it via getattr and ensure it's callable
                    items_attr = getattr(item, "items", None)
                    if callable(items_attr):
                        try:
                            # Cast the callable to a zero-argument callable that returns an iterable of pairs,
                            # so static type checkers accept dict(...) call.
                            items_callable = cast(Callable[[], Iterable[Any]], items_attr)
                            res = items_callable()
                            if hasattr(res, "__iter__"):
                                converted = dict(res)
                            else:
                                converted = None
                        except Exception:
                            converted = None
                    else:
                        # Only attempt dict(item) if it's an actual iterable of pairs and not a str/bytes
                        if hasattr(item, "__iter__") and not isinstance(item, (str, bytes, bytearray)):
                            try:
                                # Tell the type checker we intend this to be an iterable of pairs.
                                converted = dict(cast(Iterable[Any], item))
                            except Exception:
                                converted = None
                        else:
                            converted = None
            except Exception:
                converted = None

        if converted is None:
            try:
                converted = vars(item)
            except Exception:
                converted = None

        if isinstance(converted, dict):
            listings.append(converted)
        else:
            # Last resort: store the raw value under a key to preserve data
            listings.append({"value": item})

    sql = generate_upsert_sql(listings)
    Path('data/upload.sql').write_text(sql)


if __name__ == '__main__':
    main()
