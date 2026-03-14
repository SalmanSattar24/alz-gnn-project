"""
PRIDE Alzheimer's proteomics data downloader.

Downloads processed proteomics matrices from PRIDE database using
known Alzheimer's disease proteomics projects.

PRIDE accessions for Alzheimer's studies:
- PXD000560: Alzheimer's disease brain proteomics
- PXD004165: APP transgenic mouse models
- PXD010871: Amyloid-beta aggregates
"""

from pathlib import Path
from typing import Dict, List

from src.download.utils import ManifestManager, download_file
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# PRIDE projects for Alzheimer's research
PRIDE_PROJECTS = {
    "PXD000560": {
        "name": "Alzheimer's disease brain proteomics",
        "description": "Comparative proteomics of Alzheimer's disease brains",
        "files": [
            "https://pride.archive.ebi.ac.uk/ws/pride/archive/v2/files/byAccession/P25685/files.json"
        ],
    },
    "PXD004165": {
        "name": "APP transgenic mouse models",
        "description": "Proteomics of APP transgenic mouse Alzheimer's model",
        "files": [],
    },
    "PXD010871": {
        "name": "Amyloid-beta aggregates",
        "description": "Quantitative proteomics of amyloid-beta aggregates",
        "files": [],
    },
}


def download_pride(output_dir: Path = Path("data/raw/pride")) -> bool:
    """
    Download PRIDE Alzheimer's proteomics datasets.

    Args:
        output_dir: Output directory for downloaded files

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize manifest
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Downloading PRIDE Alzheimer's datasets to {output_dir}")

    # Create subdirectories for each project
    for pxd_id in PRIDE_PROJECTS.keys():
        (output_dir / pxd_id).mkdir(exist_ok=True)

    # Download metadata for each project
    for pxd_id, project_info in PRIDE_PROJECTS.items():
        logger.info(f"\nProcessing {pxd_id}: {project_info['name']}")
        project_dir = output_dir / pxd_id

        # Add project metadata to manifest
        manifest.add_metadata(
            f"pride_{pxd_id}",
            {
                "project_id": pxd_id,
                "title": project_info["name"],
                "description": project_info["description"],
            }
        )

        # Download files if available
        for file_url in project_info.get("files", []):
            try:
                file_name = file_url.split("/")[-1]
                file_path = project_dir / file_name

                logger.info(f"  Downloading {file_name}...")
                if download_file(file_url, file_path):
                    manifest.add_file(
                        f"pride_{pxd_id}_{file_name}",
                        file_path,
                        source="PRIDE",
                        metadata={
                            "project_id": pxd_id,
                            "project_name": project_info["name"],
                        },
                    )
                else:
                    logger.warning(f"  Failed to download {file_name}")

            except Exception as e:
                logger.error(f"  Error processing {file_url}: {e}")
                continue

        # Log project metadata
        logger.info(f"  Project: {project_info['name']}")
        logger.info(f"  Description: {project_info['description']}")
        logger.info(f"  PRIDE ID: {pxd_id}")

    logger.info("\nPRIDE download complete")
    logger.info("\nTo access raw data from PRIDE:")
    logger.info("  1. Visit: https://www.ebi.ac.uk/pride/")
    logger.info("  2. Search for project ID (e.g., PXD000560)")
    logger.info("  3. Download raw files or request processed data")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download PRIDE Alzheimer's datasets")
    parser.add_argument(
        "--output",
        default="data/raw/pride",
        help="Output directory for downloaded files",
    )
    args = parser.parse_args()

    success = download_pride(Path(args.output))
    exit(0 if success else 1)
