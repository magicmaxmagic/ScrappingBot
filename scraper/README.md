# Scraper CLI

Python 3.11 scraper with Playwright + httpx + Pydantic + shapely + geopandas.

Run:
```bash
make setup
python -m scraper.cli --where="Paris" --what="rent;size>=20;price<=1500" --when=2025-07-01 --polygon='{"type":"Polygon","coordinates":[...]}'
```
