# ScrappingBot - Makefile principal
# Commandes simplifiées pour le développement et les tests

.PHONY: help test test-etl test-all clean install dev prod

# Variables
PYTHON := python
PIP := pip
VENV := .venv
PYTEST := python -m pytest

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

.DEFAULT_GOAL := help

help: ## Afficher cette aide
	@echo "$(GREEN)ScrappingBot - Commandes disponibles$(NC)"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Installer les dépendances Python
	@echo "$(BLUE)Installation des dépendances...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

test: ## Lancer tous les tests
	@echo "$(BLUE)🧪 Exécution de tous les tests...$(NC)"
	$(PYTEST) tests/ -v
	@echo "$(GREEN)✅ Tests terminés$(NC)"

test-etl: ## Lancer les tests ETL uniquement
	@echo "$(BLUE)🔧 Tests ETL...$(NC)"
	$(PYTEST) tests/test_*small.py -v
	@echo "$(GREEN)✅ Tests ETL terminés$(NC)"

test-coverage: ## Tests avec couverture
	@echo "$(BLUE)🧪 Tests avec couverture...$(NC)"
	$(PYTEST) tests/ --cov=etl --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Rapport de couverture généré$(NC)"

test-unit: ## Tests unitaires seulement
	@echo "$(BLUE)🧪 Tests unitaires...$(NC)"
	$(PYTEST) tests/ -m "not integration" -v
	@echo "$(GREEN)✅ Tests unitaires terminés$(NC)"

clean: ## Nettoyer les fichiers temporaires
	@echo "$(BLUE)🧹 Nettoyage...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

lint: ## Vérifier la qualité du code
	@echo "$(BLUE)🔍 Vérification du code...$(NC)"
	$(PYTHON) -m flake8 etl/ tests/ --max-line-length=100
	$(PYTHON) -m black --check etl/ tests/
	@echo "$(GREEN)✅ Code vérifié$(NC)"

format: ## Formater le code
	@echo "$(BLUE)🎨 Formatage du code...$(NC)"
	$(PYTHON) -m black etl/ tests/
	$(PYTHON) -m isort etl/ tests/
	@echo "$(GREEN)✅ Code formaté$(NC)"

# Docker commands
docker-build: ## Construire les images Docker
	@echo "$(BLUE)🐳 Construction des images Docker...$(NC)"
	make -f Makefile.docker build
	@echo "$(GREEN)✅ Images construites$(NC)"

docker-up: ## Démarrer les services Docker
	@echo "$(BLUE)🐳 Démarrage des services Docker...$(NC)"
	make -f Makefile.docker up
	@echo "$(GREEN)✅ Services démarrés$(NC)"

docker-down: ## Arrêter les services Docker
	@echo "$(BLUE)🐳 Arrêt des services Docker...$(NC)"
	make -f Makefile.docker down
	@echo "$(GREEN)✅ Services arrêtés$(NC)"

docker-test: ## Tests dans l'environnement Docker
	@echo "$(BLUE)🐳 Tests Docker...$(NC)"
	make -f Makefile.docker test-docker
	@echo "$(GREEN)✅ Tests Docker terminés$(NC)"

# Scripts management (remplacés par commandes Docker natives)
deploy: docker-up ## Déployer l'application (alias pour docker-up)

start: docker-up ## Démarrer l'application (alias pour docker-up)

stop: docker-down ## Arrêter l'application (alias pour docker-down)

health: ## Vérifier la santé des services
	@echo "$(BLUE)🏥 Vérification de santé...$(NC)"
	@docker-compose ps
	@echo "$(BLUE)Test de connectivité API...$(NC)"
	@curl -f http://localhost:8787/health || echo "$(RED)API non accessible$(NC)"

monitor: ## Monitoring basique
	@echo "$(BLUE)📊 État des services...$(NC)"
	@docker-compose ps
	@echo "$(BLUE)📊 Logs récents...$(NC)"
	@docker-compose logs --tail=10

dev: ## Mode développement
	@echo "$(BLUE)🛠️ Mode développement...$(NC)"
	make -f Makefile.docker dev

prod: ## Mode production
	@echo "$(BLUE)🏭 Mode production...$(NC)"
	make -f Makefile.docker prod
