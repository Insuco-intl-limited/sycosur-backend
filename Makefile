# Makefile pour le projet

.PHONY: help
help: ## Afficher l'aide
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

.PHONY: lint
lint: ## Lancer tous les outils de linting
	make isort-check
	make flake8-check
	make black-check

.PHONY: format
format: ## Formater automatiquement le code
	make isort-fix
	make black-fix

.PHONY: isort-check
isort-check: ## Vérifier l'ordre des imports avec isort
	isort --check-only --diff .

.PHONY: isort-fix
isort-fix: ## Corriger l'ordre des imports avec isort
	isort .

.PHONY: flake8-check
flake8-check: ## Vérifier le code avec flake8
	flake8 .

.PHONY: black-check
black-check: ## Vérifier le formatage avec black
	black --check .

.PHONY: black-fix
black-fix: ## Formater le code avec black
	black .

.PHONY: check-migrations
check-migrations: ## Vérifier si des migrations sont nécessaires
	python manage.py makemigrations --check --dry-run

.PHONY: test
test: ## Exécuter les tests
	python manage.py test

.PHONY: serve
serve: ## Lancer le serveur de développement
	python manage.py runserver

.PHONY: clean
clean: ## Nettoyer les fichiers temporaires et compilés
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
