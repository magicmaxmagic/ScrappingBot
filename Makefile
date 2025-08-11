SHELL := /bin/bash

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTHON ?= python3.11
LOG_DIR := logs

.PHONY: all setup install playwright crawl etl sql report d1 d1-local test clean venv \
	frontend-install frontend-dev frontend-dev-bg frontend-stop \
	workers-install workers-dev workers-dev-bg workers-stop \
	components componnent component dev components-stop components-status \
	logs-init logs-tail logs-clean up down status

all: setup crawl etl sql

setup: venv install playwright

venv:
	@# Create venv if missing, else recreate if Python version != 3.11.4
	@if [ ! -d "$(VENV)" ]; then \
		if command -v $(PYTHON) >/dev/null 2>&1; then \
			$(PYTHON) -m venv $(VENV); \
		else \
			echo "Python 3.11 requis. Installez-le (ex: brew install python@3.11) ou lancez make avec PYTHON=/chemin/python3.11"; \
			exit 1; \
		fi; \
	else \
		VER=`$(PY) -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo unknown`; \
		if [ "$$VER" != "3.11" ]; then \
			echo "Venv en $$VER détecté. Recréation avec $(PYTHON) (3.11)"; \
			rm -rf $(VENV); \
			if command -v $(PYTHON) >/dev/null 2>&1; then \
				$(PYTHON) -m venv $(VENV); \
			else \
				echo "Python 3.11 requis. Installez-le (ex: brew install python@3.11) ou lancez make avec PYTHON=/chemin/python3.11"; \
				exit 1; \
			fi; \
		fi; \
	fi

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt


playwright:
	$(PY) -m playwright install chromium

crawl:
	mkdir -p data
	$(PY) -m scrapy crawl site_generic -s LOG_LEVEL=INFO $${MAKE_CRAWL_EXTRA} -s 'FEEDS={"data/listings.json":{"format":"json","encoding":"utf8","overwrite":true}}'

etl:
	$(PY) scripts/run_etl.py

sql:
	@ls -lh data/upload.sql 2>/dev/null || echo "No SQL generated yet"

report:
	@cat data/report.json 2>/dev/null || echo "No report yet"

d1:
	@if [ -z "$$CF_D1_DB" ]; then echo "CF_D1_DB not set"; exit 1; fi
	wrangler d1 execute "$$CF_D1_DB" --command "$$(cat data/upload.sql)" $${CF_WRANGLER_PROFILE:+--profile $$CF_WRANGLER_PROFILE}

# Load generated SQL into local D1 (workers dev)
d1-local:
	@if [ ! -f data/upload.sql ]; then echo "data/upload.sql missing. Run 'make crawl etl' first."; exit 1; fi
	cd workers && npx wrangler d1 execute estate-db --local --file ../data/upload.sql

test:
	$(PY) -m pytest -q

clean:
	rm -rf data/listings.json data/upload.sql data/report.json data/html

# --- Dev Scraper HTTP endpoint (to trigger from UI) --------------------------

scraper-dev-server:
	$(PY) scripts/dev_scraper_server.py

scraper-dev-server-bg: logs-init
	@nohup $(PY) scripts/dev_scraper_server.py > $(LOG_DIR)/scraper.log 2>&1 & echo $$! > .scraper.pid && echo "Scraper dev server started (pid: $$(cat .scraper.pid)) at http://127.0.0.1:8000"

scraper-dev-stop:
	@if [ -f .scraper.pid ]; then kill `cat .scraper.pid` || true; rm -f .scraper.pid; echo "Stopped scraper dev server"; else echo "Scraper dev server not running"; fi

# --- JS/Workers dev helpers -------------------------------------------------

FRONTEND_DIR := frontend
WORKERS_DIR := workers

frontend-install:
	@cd $(FRONTEND_DIR) && if [ ! -d node_modules ]; then echo "Installing frontend deps"; npm install; else echo "Frontend deps OK"; fi

workers-install:
	@cd $(WORKERS_DIR) && if [ ! -d node_modules ]; then echo "Installing workers deps"; npm install; else echo "Workers deps OK"; fi

frontend-dev: frontend-install
	cd $(FRONTEND_DIR) && npm run dev

workers-dev: workers-install
	cd $(WORKERS_DIR) && npm run dev

# Background runners with PID and log files
frontend-dev-bg: frontend-install logs-init
	@mkdir -p $(FRONTEND_DIR)
	@cd $(FRONTEND_DIR) && nohup npm run dev > ../$(LOG_DIR)/frontend.log 2>&1 & echo $$! > .dev.pid && echo "Frontend dev started (pid: $$(cat .dev.pid))"

workers-dev-bg: workers-install logs-init
	@mkdir -p $(WORKERS_DIR)
	@cd $(WORKERS_DIR) && nohup npm run dev > ../$(LOG_DIR)/workers.log 2>&1 & echo $$! > .dev.pid && echo "Workers dev started (pid: $$(cat .dev.pid)) at http://127.0.0.1:8787"

frontend-stop:
	@if [ -f $(FRONTEND_DIR)/.dev.pid ]; then kill `cat $(FRONTEND_DIR)/.dev.pid` || true; rm -f $(FRONTEND_DIR)/.dev.pid; echo "Stopped frontend"; else echo "Frontend not running"; fi

workers-stop:
	@if [ -f $(WORKERS_DIR)/.dev.pid ]; then kill `cat $(WORKERS_DIR)/.dev.pid` || true; rm -f $(WORKERS_DIR)/.dev.pid; echo "Stopped workers"; else echo "Workers not running"; fi

# One-shot to start both components in background
components: workers-dev-bg frontend-dev-bg
	@echo "Components running. Logs: $(LOG_DIR)/frontend.log, $(LOG_DIR)/workers.log"

# Aliases
component: components
componnent: components
dev: components

components-stop: frontend-stop workers-stop

components-status:
	@echo "Workers PID: $$(cat $(WORKERS_DIR)/.dev.pid 2>/dev/null || echo '-')"
	@echo "Frontend PID: $$(cat $(FRONTEND_DIR)/.dev.pid 2>/dev/null || echo '-')"

# Simple one-liner: start everything for the web UI
up: workers-dev-bg frontend-dev-bg scraper-dev-server-bg
	@echo "All services up:"
	@echo "- Workers: http://127.0.0.1:8787"
	@echo "- Frontend: see Vite port in $(LOG_DIR)/frontend.log (e.g., http://localhost:5173)"
	@echo "- Scraper API: http://127.0.0.1:8000 (proxied as /dev-scrape)"

down: components-stop scraper-dev-stop
	@echo "All services stopped"

status: components-status
	@echo "Scraper PID: $$(cat .scraper.pid 2>/dev/null || echo '-')"

# Logs helpers
logs-init:
	@mkdir -p $(LOG_DIR)

logs-tail: logs-init
	@echo "Tailing logs in $(LOG_DIR)/ (Ctrl-C to stop)" && tail -n +1 -f $(LOG_DIR)/*.log

logs-clean:
	rm -f $(LOG_DIR)/*.log 2>/dev/null || true
