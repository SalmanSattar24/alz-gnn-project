"""
Data download orchestrator for Alzheimer's proteomics project.

Downloads and integrates multiple proteomics and network datasets:
- AMP-AD: Synapse
- PRIDE: EBI PRIDE database
- STRING: PPI network
- GTEx: Tissue expression reference
"""

import argparse
import os
from pathlib import Path

from src.config import load_config
from src.download.download_ampad import download_ampad
from src.download.download_gtex import download_gtex
from src.download.download_pride import download_pride
from src.download.download_string import download_string
from src.download.mock_data import generate_all_mock_data
from src.download.utils import ManifestManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def download_data(config_path: str = "config.yaml", use_mock: bool = False):
    """
    Download and integrate multi-omics datasets.

    Args:
        config_path: Path to configuration file
        use_mock: Use mock data instead of real datasets
    """
    config = load_config(config_path)
    raw_dir = Path(config["data"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("ALZHEIMER'S MULTI-OMICS DATA DOWNLOAD PIPELINE")
    logger.info("=" * 70)

    # Check for Synapse credentials if trying to download real AMP-AD data
    if not use_mock and not os.getenv("SYNAPSE_USER"):
        logger.warning(
            "\nSYNAPSE_USER environment variable not set."
        )
        logger.warning("Cannot download real AMP-AD data without Synapse authentication.")
        logger.info("Options:")
        logger.info("  1. Set SYNAPSE_USER and SYNAPSE_PASS environment variables:")
        logger.info("     $env:SYNAPSE_USER='your_username'")
        logger.info("     $env:SYNAPSE_PASS='your_password'")
        logger.info("  2. Use mock data for testing: python run.py download --mock")
        logger.info("\nUsing mock data for pipeline testing...\n")
        use_mock = True

    if use_mock:
        logger.info("USING MOCK DATASETS FOR DEVELOPMENT/TESTING")
        logger.info("-" * 70)
        success = generate_all_mock_data(raw_dir)
        if not success:
            logger.error("Mock data generation failed")
            return False
    else:
        logger.info("DOWNLOADING REAL DATASETS")
        logger.info("-" * 70)

        # Download each dataset
        datasets_to_download = [
            ("AMP-AD Proteomics", lambda: download_ampad(raw_dir / "ampad")),
            ("PRIDE Datasets", lambda: download_pride(raw_dir / "pride")),
            ("STRING PPI Network", lambda: download_string(raw_dir / "string")),
            ("GTEx Expression", lambda: download_gtex(raw_dir / "gtex")),
        ]

        for dataset_name, download_func in datasets_to_download:
            logger.info(f"\n{dataset_name}")
            logger.info("-" * 70)
            try:
                success = download_func()
                if not success:
                    logger.warning(f"Failed to download {dataset_name}")
            except Exception as e:
                logger.error(f"Error downloading {dataset_name}: {e}")

    # Verify manifest
    logger.info("\n" + "=" * 70)
    logger.info("MANIFEST VERIFICATION")
    logger.info("=" * 70)

    manifest = ManifestManager(raw_dir / "../manifest.json")
    file_count = len(manifest.data.get("files", {}))
    logger.info(f"Total files tracked: {file_count}")
    logger.info(f"Manifest location: {manifest.path}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("DATA DOWNLOAD COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Data location: {raw_dir}")
    logger.info(f"Manifest: {manifest.path}")
    logger.info("\nNext steps:")
    logger.info("  1. Review downloaded files in data/raw/")
    logger.info("  2. Run preprocessing: python run.py preprocess")
    logger.info("  3. Build graphs: python run.py graph")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download multi-omics datasets for Alzheimer's research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/download/download_data.py                # Download with real data
  python src/download/download_data.py --mock         # Use mock data
  python src/download/download_data.py --config config.yaml --mock

Environment variables (for real data):
  SYNAPSE_USER: Your Synapse username
  SYNAPSE_PASS: Your Synapse password
        """,
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use synthetic mock data instead of real datasets",
    )
    args = parser.parse_args()

    success = download_data(args.config, use_mock=args.mock)
    exit(0 if success else 1)
