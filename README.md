# ScrappingBot

Application full‑stack auto‑hébergeable pour scrapper des annonces immo, normaliser/charger en base (Cloudflare D1), et les explorer via une UI carte + recherche (WHERE/WHAT/WHEN + polygone).

## Structure du projet

- `frontend/` UI React + Vite + MapLibre (dessin de polygones avec Mapbox Draw)
- `workers/` API Cloudflare Workers (Hono) + D1 (SQLite) + KV cache
- `crawler/` Scrapy (+ Playwright optionnel) spider générique configurable par `sources.yml`
- `etl/` Normalisation, déduplication, géocodage, génération de `upload.sql`
- `config/` Sources de dev (ex: `config/sources.yml` en `file://`)
- `data/` Artefacts générés (listings.json, HTML, report, SQL, etc.)
- `scripts/` utilitaires (serveur dev du scraper, etc.)
- `Makefile` commandes DX (up/down/status, crawl/etl, logs)

## Prérequis

- macOS avec Python 3.11
- Node.js 18+
- Cloudflare Wrangler (installé via npm dans `workers/`)

## Démarrage rapide

1) Installer dépendances de base

```bash
make setup
```

1) Lancer tout en local (Workers + Frontend + serveur HTTP du scraper)

```bash
make up
```

1) Ouvrir l’UI (port Vite indiqué dans `logs/frontend.log`, ex: <http://localhost:5173>)

- Dessinez un polygone, lancez une recherche.
- Cliquez sur « Run scrape + ETL ». Cochez « Use live sources » pour utiliser `sources.yml` (Internet) au lieu des pages de test `file://`.
- Les résultats rafraîchissent en purgeant le cache KV et en bypassant le cache une fois.

Arrêt rapide

```bash
make down
```

## Scraping & ETL

- `make crawl` lit `config/sources.yml` (dev `file://`) ou un chemin surchargé via `SOURCES_FILE`.
- `make etl` produit `data/upload.sql` (UPSERT sur D1, PK dérivée de l’URL/prix/surface).
- Le serveur dev `/dev-scrape/run` déclenche crawl+etl+chargement D1 et purge le cache KV.

Chargement D1 manuel (local Workers):

```bash
make d1-local
```

## Logs

- Tous les services écrivent dans `logs/`: `frontend.log`, `workers.log`, `scraper.log`.
- Visualiser rapidement:

```bash
make logs-tail
```

## Conseils sur les sources « live »

- Le fichier `sources.yml` au racine contient des exemples. Remplacez‑les par des sites réels et des `listing_patterns` corrects.
- Vous pouvez activer le rendu JS par site via `use_js: true`.
- Respectez robots.txt et les CGU. Configurez un throttling raisonnable.

## Développement

- Frontend seul: `make frontend-dev`
- API Workers seule: `make workers-dev`
- Serveur scraper HTTP: `make scraper-dev-server`

## Tests

```bash
make test
```

## Sécurité & secrets

- Les fichiers `.env` et les états locaux Wrangler sont ignorés par git. Ne commitez jamais vos secrets.
