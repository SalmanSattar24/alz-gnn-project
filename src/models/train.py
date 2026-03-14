"""
Model training module for Alzheimer's proteomics project.

Handles baseline model training, validation, and GNN model training.
"""

import argparse
from pathlib import Path

from src.config import load_config
from src.models.baselines import BaselineModelEvaluator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def train_baselines(config_path: str = "config.yaml"):
    """
    Train baseline machine learning models.

    Args:
        config_path: Path to configuration file
    """
    logger.info("Training baseline ML models (Logistic Regression, Random Forest, MLP)")

    evaluator = BaselineModelEvaluator(config_path)
    results = evaluator.train_all_models(cohorts=["ROSMAP", "MSBB", "MAYO"])

    logger.info("Baseline model training complete")
    logger.info(f"Results saved to {evaluator.results_dir}/baseline_metrics.json")

    return results


def train_gnn(config_path: str = "config.yaml"):
    """
    Train Graph Attention Network models.

    Args:
        config_path: Path to configuration file
    """
    logger.info("Training Graph Attention Network models")

    from src.models.gnn_model import GNNTrainer

    trainer = GNNTrainer(config_path)
    results = trainer.train(cohorts=["ROSMAP", "MSBB", "MAYO"])

    logger.info("GNN model training complete")
    return results


def train_model(config_path: str = "config.yaml"):
    """
    Train models (baseline ML models and GNN).

    Args:
        config_path: Path to configuration file
    """
    config = load_config(config_path)
    processed_dir = Path(config["data"]["processed_dir"])
    checkpoint_dir = Path(config["logging"]["checkpoint_dir"])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Training models on data from {processed_dir}")
    logger.info(f"Checkpoint directory: {checkpoint_dir}")
    logger.info(f"Model architecture: {config['model']['architecture']}")

    # Train baseline models first
    train_baselines(config_path)

    # Train GNN models
    train_gnn(config_path)

    logger.info("Model training complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train models")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--baseline-only", action="store_true", help="Train only baseline models")
    parser.add_argument("--gnn-only", action="store_true", help="Train only GNN models")
    args = parser.parse_args()

    if args.baseline_only:
        train_baselines(args.config)
    elif args.gnn_only:
        train_gnn(args.config)
    else:
        train_model(args.config)
