.PHONY: help install install-dev test lint format type-check clean run run-web build docker-build docker-run deploy

help:
	@echo "Solairus Intelligence Report Generator - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run test suite"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Format code with black"
	@echo "  make type-check     Run type checking with mypy"
	@echo "  make clean          Remove build artifacts"
	@echo ""
	@echo "Running:"
	@echo "  make run            Run CLI in test mode"
	@echo "  make run-web        Run web interface"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy         Deploy to Google Cloud Run"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --cov=solairus_intelligence --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	flake8 solairus_intelligence tests
	black --check solairus_intelligence tests

format:
	black solairus_intelligence tests

type-check:
	mypy solairus_intelligence --ignore-missing-imports

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf outputs/*.docx outputs/*.pdf

run:
	python -m solairus_intelligence.cli --test

run-web:
	uvicorn solairus_intelligence.web.app:app --reload --host 0.0.0.0 --port 8080

build:
	python -m build

docker-build:
	docker build -t solairus-intelligence:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env solairus-intelligence:latest

deploy:
	bash scripts/deploy.sh

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files
