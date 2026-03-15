"""
STRING protein interaction network downloader.

Downloads protein.links.detailed.v11.5.txt.gz for Homo sapiens (taxid 9606)
from the STRING database, filters to combined_score >= 700, and writes a
clean TSV to:

    data/raw/networks/string_highconf.tsv

The detailed file includes individual evidence-channel scores
(neighbourhood, coexpression, experimental, database, text-mining, …)
in addition to the combined score, which are useful for edge feature
engineering in the GNN.

Output columns (tab-separated)
--------------------------------
protein1  protein2  neighborhood  neighborhood_transferred  fusion
cooccurence  homology  coexpression  coexpression_transferred
experimentally_determined_interaction
experimentally_determined_interaction_transferred
database_annotated  database_annotated_transferred
textmining  textmining_transferred  combined_score

Protein IDs have the taxon prefix (9606.) stripped so they read as
bare Ensembl protein IDs (ENSP…).

Usage
-----
    python -m src.download.download_string_network
    python -m src.download.download_string_network --threshold 900 --keep-gz
"""

import gzip
import sys
from pathlib import Path
from typing import Iterator, Optional

from src.download.utils import ManifestManager, download_file
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STRING_VERSION = "11.5"
STRING_TAXID = "9606"   # Homo sapiens

_GZ_FILENAME = f"{STRING_TAXID}.protein.links.detailed.v{STRING_VERSION}.txt.gz"
STRING_DETAIL_URL = (
    f"https://stringdb-static.org/download/"
    f"protein.links.detailed.v{STRING_VERSION}/"
    f"{_GZ_FILENAME}"
)

DEFAULT_OUTPUT_DIR = Path("data/raw/networks")
HIGHCONF_FILENAME = "string_highconf.tsv"

# Taxon prefix to strip from STRING protein IDs  (e.g. "9606.ENSP…" → "ENSP…")
_TAXON_PREFIX = f"{STRING_TAXID}."


# ---------------------------------------------------------------------------
# Streaming filter
# ---------------------------------------------------------------------------

def _iter_filtered_lines(gz_path: Path, score_threshold: int) -> Iterator[str]:
    """
    Stream the gzipped STRING detailed file and yield TSV lines.

    The source file is space-delimited.  We:
      • keep only rows where the last field (combined_score) >= score_threshold
      • strip the taxon prefix from protein IDs
      • convert spaces to tabs for standard TSV output
    """
    with gzip.open(gz_path, "rt") as fh:
        # Header line
        raw_header = next(fh).rstrip()
        cols = raw_header.split()
        yield "\t".join(cols)

        # Data lines
        for raw in fh:
            fields = raw.rstrip().split()
            if not fields:
                continue
            try:
                combined = int(fields[-1])
            except ValueError:
                continue
            if combined < score_threshold:
                continue

            # Strip taxon prefix from protein IDs
            fields[0] = fields[0].replace(_TAXON_PREFIX, "", 1)
            fields[1] = fields[1].replace(_TAXON_PREFIX, "", 1)

            yield "\t".join(fields)


# ---------------------------------------------------------------------------
# Main download function
# ---------------------------------------------------------------------------

def download_string_network(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    score_threshold: int = 700,
    keep_gz: bool = False,
) -> bool:
    """
    Download STRING detailed PPI network and write a filtered high-confidence TSV.

    Args:
        output_dir:       Directory for output files.
        score_threshold:  Minimum combined_score to keep (0-1000).  Default 700.
        keep_gz:          If True, keep the compressed source file after filtering.
                          Default False (saves ~1 GB of disk space).

    Returns:
        True on success.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = ManifestManager(Path("data/manifest.json"))

    # ------------------------------------------------------------------
    # Step 1: download the .gz (or reuse cached copy)
    # ------------------------------------------------------------------
    gz_path = output_dir / _GZ_FILENAME
    gz_manifest_key = "string_detailed_gz"

    if manifest.file_exists(gz_manifest_key):
        cached_info = manifest.get_file(gz_manifest_key)
        cached_path = Path(cached_info["path"])
        if cached_path.exists() and manifest.verify_file(gz_manifest_key, cached_path):
            gz_path = cached_path
            logger.info(f"STRING .gz already verified: {gz_path.name}")
        else:
            logger.info("STRING .gz hash mismatch or missing — re-downloading")
            manifest.data["files"].pop(gz_manifest_key, None)
            manifest.save()

    if not gz_path.exists():
        logger.info(f"Downloading {_GZ_FILENAME} …")
        logger.info(f"  URL : {STRING_DETAIL_URL}")
        logger.info(f"  Dest: {gz_path}")
        if not download_file(STRING_DETAIL_URL, gz_path):
            logger.error("STRING download failed.")
            return False

        manifest.add_file(
            gz_manifest_key,
            gz_path,
            source="STRING",
            metadata={
                "version": STRING_VERSION,
                "species": "Homo sapiens",
                "taxid": STRING_TAXID,
                "url": STRING_DETAIL_URL,
                "description": "Detailed PPI network with individual evidence channel scores",
            },
        )
        logger.info(f"  Saved: {gz_path.stat().st_size / 1e9:.2f} GB")

    # ------------------------------------------------------------------
    # Step 2: stream-filter and write string_highconf.tsv
    # ------------------------------------------------------------------
    out_path = output_dir / HIGHCONF_FILENAME
    logger.info(
        f"Filtering STRING edges (combined_score >= {score_threshold}) → {out_path}"
    )

    n_edges = 0
    with open(out_path, "w") as fh:
        for line in _iter_filtered_lines(gz_path, score_threshold):
            fh.write(line + "\n")
            n_edges += 1

    n_edges -= 1  # subtract header row
    logger.info(
        f"Wrote {n_edges:,} edges to {out_path}  "
        f"({out_path.stat().st_size / 1e6:.1f} MB)"
    )

    manifest.add_file(
        "string_highconf",
        out_path,
        source="STRING",
        metadata={
            "version": STRING_VERSION,
            "score_threshold": score_threshold,
            "n_edges": n_edges,
            "taxid": STRING_TAXID,
            "species": "Homo sapiens",
            "protein_id_format": "ENSP (Ensembl protein, taxon prefix stripped)",
        },
    )

    # ------------------------------------------------------------------
    # Step 3: optionally remove the large .gz to reclaim disk space
    # ------------------------------------------------------------------
    if not keep_gz and gz_path.exists():
        gz_path.unlink()
        manifest.data["files"].pop(gz_manifest_key, None)
        manifest.save()
        logger.info("Removed source .gz (pass --keep-gz to retain)")

    logger.info("STRING download complete.")
    return True


def string_network_present(output_dir: Path = DEFAULT_OUTPUT_DIR) -> tuple:
    """
    Return ``(True, path)`` if the high-confidence TSV already exists on disk.
    Used by the pipeline to skip the download step when real data is available.
    """
    tsv_path = Path(output_dir) / HIGHCONF_FILENAME
    if tsv_path.exists() and tsv_path.stat().st_size > 0:
        return True, tsv_path

    manifest = ManifestManager(Path("data/manifest.json"))
    if manifest.file_exists("string_highconf"):
        info = manifest.get_file("string_highconf")
        p = Path(info["path"])
        if p.exists():
            return True, p

    return False, tsv_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Download STRING v11.5 detailed PPI network (Homo sapiens) "
            "and write a high-confidence filtered edge list."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output:  data/raw/networks/string_highconf.tsv

Examples:
  python -m src.download.download_string_network
  python -m src.download.download_string_network --threshold 900
  python -m src.download.download_string_network --output data/raw/networks --keep-gz
""",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory (default: data/raw/networks)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=700,
        help="Minimum combined_score to keep (0-1000, default 700)",
    )
    parser.add_argument(
        "--keep-gz",
        action="store_true",
        help="Keep the source .gz after filtering (default: delete to save space)",
    )
    args = parser.parse_args()

    ok = download_string_network(
        output_dir=Path(args.output),
        score_threshold=args.threshold,
        keep_gz=args.keep_gz,
    )
    sys.exit(0 if ok else 1)
