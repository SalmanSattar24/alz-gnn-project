"""
Data download module for Alzheimer's proteomics project.

Downloads raw data from Synapse and other sources.
"""

import argparse
from pathlib import Path

from src.config import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def download_data(config_path: str = "config.yaml"):
    """
    Download data from configured sources.

    Args:
        config_path: Path to configuration file
    """
    config = load_config(config_path)
    raw_dir = Path(config["data"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading data to {raw_dir}")

    # TODO: Implement data download from Synapse
    # - Load Synapse client
    # - Download proteomics table
    # - Download PPI network
    # - Verify checksums

    logger.info("Data download complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download data from Synapse")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    download_data(args.config)
