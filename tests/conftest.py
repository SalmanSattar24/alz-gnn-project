"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def data_dir():
    """Fixture providing test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(autouse=True)
def set_seed():
    """Fixture to set random seeds for reproducibility."""
    import numpy as np
    import random

    random.seed(42)
    np.random.seed(42)


@pytest.fixture
def config_dict():
    """Fixture providing a basic config dictionary."""
    return {
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
        },
        "model": {
            "architecture": "GCN",
            "hidden_dims": [64, 32],
        },
        "training": {
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
        },
    }
