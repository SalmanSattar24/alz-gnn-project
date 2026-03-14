"""
GTEx tissue expression data downloader.

Downloads GTEx v8 median gene expression data across tissues.
Useful for cross-tissue protein expression reference.

GTEx Data Portal: https://www.gtexportal.org/
"""

from pathlib import Path

from src.download.utils import ManifestManager, download_file
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# GTEx configuration
GTEX_VERSION = "8"
GTEX_MEDIAN_EXPRESSION = "https://storage.googleapis.com/gtex_analysis_v8/rna_seq_data/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.8_gene_median_tpm.gct.gz"
GTEX_TISSUE_INFO = "https://storage.googleapis.com/gtex_analysis_v8/annotations/GTEx_Analysis_v8_Annotations_SampleAttributesDS.txt"


def download_gtex(
    output_dir: Path = Path("data/raw/gtex"),
) -> bool:
    """
    Download GTEx v8 median expression data.

    Args:
        output_dir: Output directory for downloaded files

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize manifest
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Downloading GTEx v{GTEX_VERSION} tissue expression data to {output_dir}")

    # Download median expression file
    logger.info("\nDownloading median gene expression across tissues...")
    expression_file = output_dir / f"GTEx_Analysis_2017-06-05_v{GTEX_VERSION}_gene_median_tpm.gct.gz"

    if not expression_file.exists():
        if not download_file(GTEX_MEDIAN_EXPRESSION, expression_file, max_retries=3):
            logger.warning("Failed to download GTEx expression data")
            logger.info("This file is large (~1.5 GB). Manual download from GTEx portal recommended.")
        else:
            manifest.add_file(
                "gtex_expression",
                expression_file,
                source="GTEx",
                metadata={
                    "version": GTEX_VERSION,
                    "data_type": "median_tpm",
                    "description": "Median gene expression TPM across tissues",
                    "url": GTEX_MEDIAN_EXPRESSION,
                },
            )
            logger.info(f"Downloaded: {expression_file.name}")
    else:
        logger.info("GTEx expression data already downloaded")

    # Download sample annotations
    logger.info("Downloading tissue sample annotations...")
    annotations_file = output_dir / f"GTEx_Analysis_v{GTEX_VERSION}_Annotations_SampleAttributesDS.txt"

    if not annotations_file.exists():
        if not download_file(GTEX_TISSUE_INFO, annotations_file):
            logger.warning("Failed to download GTEx annotations")
        else:
            manifest.add_file(
                "gtex_annotations",
                annotations_file,
                source="GTEx",
                metadata={
                    "version": GTEX_VERSION,
                    "data_type": "sample_annotations",
                    "description": "Sample attributes and tissue types",
                    "url": GTEX_TISSUE_INFO,
                },
            )
            logger.info(f"Downloaded: {annotations_file.name}")
    else:
        logger.info("GTEx annotations already downloaded")

    # Add configuration to manifest
    manifest.add_metadata(
        "gtex_config",
        {
            "version": GTEX_VERSION,
            "release": "v8",
            "download_date": str(Path(output_dir).stat().st_mtime),
            "data_types": ["median_tpm", "sample_annotations"],
        },
    )

    logger.info(f"\nGTEx Dataset Summary")
    logger.info(f"  Version: v{GTEX_VERSION}")
    logger.info(f"  Tissues: 54")
    logger.info(f"  Samples: 17,382")
    logger.info(f"  Genes: ~56,000")
    logger.info(f"\nNote: GTEx expression provides cross-tissue reference")
    logger.info(f"for protein abundance validation")

    logger.info("GTEx download complete")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download GTEx tissue expression data")
    parser.add_argument(
        "--output",
        default="data/raw/gtex",
        help="Output directory for downloaded files",
    )
    args = parser.parse_args()

    success = download_gtex(Path(args.output))
    exit(0 if success else 1)
