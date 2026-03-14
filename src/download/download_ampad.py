"""
AMP-AD proteomics data downloader.

Downloads preprocessed proteomics matrices from ROSMAP, MSBB, and MAYO cohorts
from Synapse project syn3157322.

Uses environment variables for authentication:
- SYNAPSE_USER: Synapse username
- SYNAPSE_PASS: Synapse password
"""

import os
from pathlib import Path
from typing import Dict, List

from src.download.utils import ManifestManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# AMP-AD Synapse project and file mappings
AMP_AD_PROJECT = "syn3157322"

# Dataset configurations
DATASETS = {
    "ROSMAP": {
        "cohort_id": "ROSMAP",
        "synapse_ids": {
            "proteomics": "syn25811207",  # ROSMAP proteomics
            "metadata": "syn25811208",
        },
    },
    "MSBB": {
        "cohort_id": "MSBB",
        "synapse_ids": {
            "proteomics": "syn25811209",  # MSBB proteomics
            "metadata": "syn25811210",
        },
    },
    "MAYO": {
        "cohort_id": "MAYO",
        "synapse_ids": {
            "proteomics": "syn25811211",  # MAYO proteomics
            "metadata": "syn25811212",
        },
    },
}


def authenticate_synapse(username: str = None, password: str = None) -> bool:
    """
    Authenticate with Synapse.

    Args:
        username: Synapse username (uses env var if None)
        password: Synapse password (uses env var if None)

    Returns:
        True if authentication successful
    """
    try:
        import synapseclient
    except ImportError:
        logger.error("synapseclient not installed. Install with: pip install synapseclient")
        return False

    username = username or os.getenv("SYNAPSE_USER")
    password = password or os.getenv("SYNAPSE_PASS")

    if not username or not password:
        logger.error(
            "Synapse credentials not found. Set SYNAPSE_USER and SYNAPSE_PASS environment variables"
        )
        return False

    try:
        syn = synapseclient.Synapse()
        syn.login(username, password)
        logger.info("Successfully authenticated with Synapse")
        return True
    except Exception as e:
        logger.error(f"Synapse authentication failed: {e}")
        return False


def download_ampad(output_dir: Path = Path("data/raw/ampad")) -> bool:
    """
    Download AMP-AD proteomics datasets.

    Args:
        output_dir: Output directory for downloaded files

    Returns:
        True if successful
    """
    try:
        import synapseclient
    except ImportError:
        logger.error("synapseclient required. Install with: pip install synapseclient")
        return False

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize manifest
    manifest = ManifestManager(Path("data/manifest.json"))

    # Create subdirectories
    for cohort in DATASETS.keys():
        (output_dir / cohort).mkdir(exist_ok=True)

    logger.info(f"Downloading AMP-AD proteomics datasets to {output_dir}")

    # Authenticate
    if not authenticate_synapse():
        logger.error("Failed to authenticate with Synapse. Use mock data instead.")
        return False

    try:
        syn = synapseclient.Synapse()
        syn.login(os.getenv("SYNAPSE_USER"), os.getenv("SYNAPSE_PASS"))
    except Exception as e:
        logger.error(f"Synapse login failed: {e}")
        return False

    # Download each dataset
    for cohort_name, cohort_info in DATASETS.items():
        logger.info(f"\nDownloading {cohort_name}...")
        cohort_dir = output_dir / cohort_name

        for file_type, synapse_id in cohort_info["synapse_ids"].items():
            file_id = f"ampad_{cohort_name}_{file_type}"

            # Skip if already downloaded and verified
            if manifest.file_exists(file_id):
                file_path = Path(manifest.get_file(file_id)["path"])
                if file_path.exists() and manifest.verify_file(file_id, file_path):
                    logger.info(f"  {file_id} already downloaded (verified)")
                    continue

            try:
                logger.info(f"  Downloading {file_type} from Synapse...")
                entity = syn.get(synapse_id, downloadLocation=str(cohort_dir))
                file_path = Path(entity.path)

                if file_path.exists():
                    manifest.add_file(
                        file_id,
                        file_path,
                        source="Synapse",
                        metadata={
                            "cohort": cohort_name,
                            "file_type": file_type,
                            "synapse_id": synapse_id,
                        },
                    )
                    logger.info(f"  Downloaded: {file_path.name}")
                else:
                    logger.warning(f"  File not found after download: {synapse_id}")

            except Exception as e:
                logger.error(f"  Failed to download {file_type}: {e}")
                continue

    logger.info("\nAMP-AD download complete")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download AMP-AD proteomics datasets")
    parser.add_argument(
        "--output",
        default="data/raw/ampad",
        help="Output directory for downloaded files",
    )
    args = parser.parse_args()

    success = download_ampad(Path(args.output))
    exit(0 if success else 1)
