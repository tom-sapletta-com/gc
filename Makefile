# Makefile for gc package

.PHONY: help install install-dev test test-verbose lint format type-check clean build upload docs run-example

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  upload       - Upload to PyPI"
	@echo "  docs         - Generate documentation"
	@echo "  run-example  - Run example script"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test]"

# Testing
test:
	pytest

test-verbose:
	pytest -v -s

test-coverage:
	pytest --cov=gc --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 gc/ tests/
	black --check gc/ tests/
	mypy gc/

format:
	black gc/ tests/
	isort gc/ tests/

type-check:
	mypy gc/

# Build and distribution
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	python -m twine upload dist/*

upload-test: build
	python -m twine upload --repository testpypi dist/*

# Documentation
docs:
	@echo "Documentation generation not yet implemented"

# Example usage
run-example:
	python -c "from gc import GarbageCollector, MemoryProfiler; from gc.utils import analyze_memory_usage; print('=== Garbage Collection Demo ==='); gc_manager = GarbageCollector(); summary = gc_manager.get_memory_summary(); print(f'Memory Summary: {summary}'); print('\n=== Memory Profiling Demo ==='); profiler = MemoryProfiler(); profiler.take_snapshot('start'); data = [list(range(1000)) for _ in range(10)]; profiler.take_snapshot('after_data_creation'); comparison = profiler.compare_snapshots(0, 1); print(f'Memory change: {comparison[\"rss_diff\"]} bytes'); print('\n=== Memory Analysis Demo ==='); analysis = analyze_memory_usage(); print(f'Total objects: {analysis[\"objects\"][\"total_count\"]}'); print(f'Memory usage: {analysis[\"memory\"][\"rss\"]} bytes')"

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"

ci: lint test-coverage
	@echo "CI checks passed!"

# Quick commands
quick-test:
	python -m pytest tests/ -v

quick-lint:
	flake8 gc/ tests/

# Package information
info:
	@echo "Package: gc"
	@echo "Version: $$(python -c 'import gc; print(gc.__version__)')"
	@echo "Python: $$(python --version)"
	@echo "Location: $$(python -c 'import gc; print(gc.__file__)')"

# Dependencies check
check-deps:
	pip check
	pip list | grep -E "(psutil|pytest|black|mypy)"

# Performance testing
perf-test:
	python -c "import time; from gc import GarbageCollector, MemoryProfiler; print('Performance Test...'); gc_manager = GarbageCollector(); profiler = MemoryProfiler(); start_time = time.time(); [data for i in range(1000) for data in [[list(range(100)) for _ in range(10)]]]; gc_time = time.time() - start_time; print(f'Garbage collection time: {gc_time:.4f}s'); start_time = time.time(); [profiler.take_snapshot(f'snapshot_{i}') for i in range(100)]; prof_time = time.time() - start_time; print(f'Memory profiling time: {prof_time:.4f}s')"

# Security check
security:
	bandit -r gc/
	safety check

# All checks
all-checks: lint test-coverage security
	@echo "All checks completed successfully!"
