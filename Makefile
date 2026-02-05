.PHONY: help install install-dev test test-cov clean docker-up docker-down format lint

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make clean        - Clean up generated files"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Run code linters"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest test_integration.py -v

test-cov:
	pytest test_integration.py --cov=. --cov-report=html --cov-report=term

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services are ready!"
	@echo "Vault UI: http://localhost:8200 (token: dev-root-token)"
	@echo "Consul UI: http://localhost:8500"

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build

format:
	@command -v black >/dev/null 2>&1 && black *.py || echo "black not installed, skipping format"

lint:
	@command -v flake8 >/dev/null 2>&1 && flake8 *.py --max-line-length=120 || echo "flake8 not installed, skipping lint"
	@command -v pylint >/dev/null 2>&1 && pylint *.py --max-line-length=120 || echo "pylint not installed, skipping lint"
