.PHONY: help install dev lint format test clean download preprocess graph train explain stability report

# Default target
help:
	@echo "Proteomics-Driven GNN for Alzheimer's Protein Prioritization"
	@echo "============================================================"
	@echo ""
	@echo "Installation:"
	@echo "  make install      Install dependencies via conda"
	@echo "  make dev          Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run flake8 and mypy linting"
	@echo "  make format       Format code with black and isort"
	@echo "  make test         Run pytest suite"
	@echo ""
	@echo "Pipeline:"
	@echo "  make download     Download data from Synapse"
	@echo "  make preprocess   Preprocess and normalize data"
	@echo "  make graph        Construct protein interaction graphs"
	@echo "  make train        Train GNN models"
	@echo "  make explain      Generate model explanations (SHAP, CAPTUM)"
	@echo "  make stability    Run stability and robustness analysis"
	@echo "  make report       Generate comprehensive analysis report"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        Remove cache, logs, and temporary files"
	@echo "  make all          Run complete pipeline"
	@echo ""

# Installation targets
install:
	@echo "Installing dependencies with conda..."
	conda env create -f environment.yml || conda env update -f environment.yml
	@echo "✓ Dependencies installed. Activate with: conda activate alz-gnn"

dev: install
	@echo "Installing development dependencies..."
	pip install -e .
	pre-commit install || true
	@echo "✓ Development setup complete"

# Code quality targets
lint:
	@echo "Running flake8..."
	flake8 src tests --max-line-length=100 --ignore=E203,W503,E266,E501
	@echo "✓ Flake8 passed"
	@echo ""
	@echo "Running type checking with mypy..."
	mypy src --ignore-missing-imports --no-error-summary 2>/dev/null || true
	@echo "✓ Type checking complete"

format:
	@echo "Formatting code with black..."
	black src tests --line-length=100
	@echo "✓ Black formatting complete"
	@echo ""
	@echo "Sorting imports with isort..."
	isort src tests --profile black
	@echo "✓ Import sorting complete"

test:
	@echo "Running pytest suite..."
	pytest tests -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "✓ Tests passed. Coverage report: htmlcov/index.html"

# Pipeline targets
download:
	@echo "Downloading data from Synapse..."
	python src/download/download_data.py --config config.yaml
	@echo "✓ Data download complete"

preprocess:
	@echo "Preprocessing and normalizing data..."
	python src/preprocess/preprocess.py --config config.yaml
	@echo "✓ Preprocessing complete"

graph:
	@echo "Constructing protein interaction graphs..."
	python src/graphs/build_graphs.py --config config.yaml
	@echo "✓ Graph construction complete"

train:
	@echo "Training GNN models..."
	python src/models/train.py --config config.yaml
	@echo "✓ Model training complete"

explain:
	@echo "Generating model explanations..."
	python src/explain/explain_model.py --config config.yaml
	@echo "✓ Explainability analysis complete"

stability:
	@echo "Running stability and robustness analysis..."
	python src/analysis/stability_analysis.py --config config.yaml
	@echo "✓ Stability analysis complete"

report:
	@echo "Generating comprehensive analysis report..."
	python src/analysis/generate_report.py --config config.yaml
	@echo "✓ Report generation complete. Check results/report.pdf"

# Utility targets
clean:
	@echo "Cleaning project..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build
	rm -f *.log
	@echo "✓ Cleanup complete"

all: download preprocess graph train explain stability report
	@echo ""
	@echo "✓ Complete pipeline executed successfully!"
	@echo "Check results/ directory for outputs"

# Quick start for development
quickstart:
	@echo "Quick start setup..."
	make install
	make download
	make preprocess
	@echo "✓ Quick setup complete. Next: make graph"
