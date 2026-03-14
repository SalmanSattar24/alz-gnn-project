"""
STRING protein interaction network downloader.

Downloads STRING protein interaction edges filtered by confidence score.
STRING v11.5 includes human protein interactions from multiple sources.
"""

from pathlib import Path

from src.download.utils import ManifestManager, download_file
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# STRING database configuration
STRING_VERSION = "11.5"
STRING_SPECIES = "9606"  # Homo sapiens
STRING_EDGE_URL = f"https://stringdb-static.org/download/protein.links.v{STRING_VERSION}/{STRING_SPECIES}.protein.links.v{STRING_VERSION}.txt.gz"
STRING_INFO_URL = f"https://stringdb-static.org/download/protein.info.v{STRING_VERSION}/{STRING_SPECIES}.protein.info.v{STRING_VERSION}.txt.gz"


def download_string(
    output_dir: Path = Path("data/raw/string"),
    score_threshold: int = 700,
) -> bool:
    """
    Download STRING protein interaction network.

    Args:
        output_dir: Output directory for downloaded files
        score_threshold: Minimum combined score to include edges (0-1000)

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize manifest
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Downloading STRING PPI network (v{STRING_VERSION}) to {output_dir}")
    logger.info(f"Score threshold: {score_threshold}/1000")

    # Download protein interactions
    logger.info("\nDownloading protein interaction edges...")
    edges_file = output_dir / f"protein.links.v{STRING_VERSION}.txt.gz"
    edges_url = STRING_EDGE_URL

    if not edges_file.exists():
        if not download_file(edges_url, edges_file):
            logger.error(f"Failed to download STRING edges from {edges_url}")
            return False

        manifest.add_file(
            "string_edges",
            edges_file,
            source="STRING",
            metadata={
                "version": STRING_VERSION,
                "species": "Homo sapiens",
                "species_id": STRING_SPECIES,
                "url": edges_url,
            },
        )
        logger.info(f"Downloaded: {edges_file.name}")
    else:
        logger.info("STRING edges already downloaded")

    # Download protein information
    logger.info("Downloading protein information...")
    info_file = output_dir / f"protein.info.v{STRING_VERSION}.txt.gz"

    if not info_file.exists():
        if not download_file(STRING_INFO_URL, info_file):
            logger.warning(f"Failed to download STRING protein info from {STRING_INFO_URL}")
        else:
            manifest.add_file(
                "string_info",
                info_file,
                source="STRING",
                metadata={
                    "version": STRING_VERSION,
                    "species": "Homo sapiens",
                    "url": STRING_INFO_URL,
                },
            )
            logger.info(f"Downloaded: {info_file.name}")
    else:
        logger.info("STRING protein info already downloaded")

    # Log statistics and filtering info
    logger.info(f"\nSTRING Network Summary")
    logger.info(f"  Version: {STRING_VERSION}")
    logger.info(f"  Species: Homo sapiens")
    logger.info(f"  Score threshold: {score_threshold}")
    logger.info(f"  Downloaded files:")
    logger.info(f"    - {edges_file.name}")
    logger.info(f"    - {info_file.name}")

    logger.info("\nFiltering by score threshold will be done during preprocessing")
    manifest.add_metadata(
        "string_config",
        {
            "version": STRING_VERSION,
            "score_threshold": score_threshold,
            "species_id": STRING_SPECIES,
            "species_name": "Homo sapiens",
        },
    )

    logger.info("STRING download complete")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download STRING protein interaction network")
    parser.add_argument(
        "--output",
        default="data/raw/string",
        help="Output directory for downloaded files",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=700,
        help="Minimum combined score threshold (0-1000)",
    )
    args = parser.parse_args()

    success = download_string(Path(args.output), args.threshold)
    exit(0 if success else 1)
