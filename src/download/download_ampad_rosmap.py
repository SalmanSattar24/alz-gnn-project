"""
ROSMAP proteomics downloader — AMP-AD Knowledge Portal (Synapse).

Downloads the ROSMAP TMT10 proteomics matrix and clinical sample metadata
from the AMP-AD project (syn2580853) via the Synapse REST API.

Access requirements
-------------------
1. Register a free account at https://www.synapse.org
2. Accept the AMP-AD data use agreement at:
   https://www.synapse.org/#!Synapse:syn2580853
3. Supply credentials via one of:
   a) Environment variable (Personal Access Token — recommended):
        SYNAPSE_AUTH_TOKEN=<your_PAT>
   b) Username + password env vars:
        SYNAPSE_USER=<username>   SYNAPSE_PASS=<password>
   c) Stored credentials in ~/.synapseConfig  (run `synapse login` once)

Key Synapse IDs used
--------------------
syn21261359  — ROSMAP TMT proteomics quantification matrix
syn21261360  — ROSMAP proteomics sample metadata
syn3191087   — ROSMAP clinical variables (broad use)

Output layout
-------------
data/raw/ampad/
  ROSMAP/
    <proteomics file downloaded from Synapse>
    <metadata file downloaded from Synapse>
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.download.utils import ManifestManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Synapse dataset registry
# ---------------------------------------------------------------------------

ROSMAP_SYNAPSE_IDS: Dict[str, str] = {
    # Primary proteomics quantification (TMT10, log2 protein abundances)
    "proteomics_tmt": "syn21261359",
    # Per-sample metadata (batch, PMI, age, sex, diagnosis, …)
    "proteomics_meta": "syn21261360",
    # Full ROSMAP clinical variables (optional but useful for covariate QC)
    "clinical": "syn3191087",
}

DEFAULT_OUTPUT_DIR = Path("data/raw/ampad")


# ---------------------------------------------------------------------------
# Synapse client helpers
# ---------------------------------------------------------------------------

def _build_syn_client(
    auth_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    """
    Return an authenticated Synapse client, or None on failure.

    Authentication priority:
      1. Explicit ``auth_token`` argument
      2. SYNAPSE_AUTH_TOKEN env var (Personal Access Token)
      3. SYNAPSE_USER + SYNAPSE_PASS env vars
      4. Cached credentials in ~/.synapseConfig
    """
    try:
        import synapseclient
    except ImportError:
        logger.error(
            "synapseclient is not installed.\n"
            "Install it:  pip install synapseclient"
        )
        return None

    auth_token = auth_token or os.getenv("SYNAPSE_AUTH_TOKEN")
    username = username or os.getenv("SYNAPSE_USER")
    password = password or os.getenv("SYNAPSE_PASS")

    syn = synapseclient.Synapse(silent=True)
    try:
        if auth_token:
            syn.login(authToken=auth_token, silent=True)
        elif username and password:
            syn.login(username, password, rememberMe=False, silent=True)
        else:
            # Fall back to cached credentials
            syn.login(silent=True)
        logger.info("Authenticated with Synapse")
        return syn
    except Exception as exc:
        logger.error(
            f"Synapse authentication failed: {exc}\n\n"
            "Options:\n"
            "  1. Set SYNAPSE_AUTH_TOKEN to a Personal Access Token\n"
            "  2. Set SYNAPSE_USER + SYNAPSE_PASS\n"
            "  3. Run `synapse login` to cache credentials\n"
            "  4. Use mock data: python execute_pipeline_direct.py --mock"
        )
        return None


# ---------------------------------------------------------------------------
# Main downloader
# ---------------------------------------------------------------------------

def download_rosmap_proteomics(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    synapse_ids: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    skip_clinical: bool = False,
) -> bool:
    """
    Download ROSMAP proteomics data from Synapse.

    Args:
        output_dir:     Root download directory; files land in output_dir/ROSMAP/
        synapse_ids:    Override the default ROSMAP_SYNAPSE_IDS mapping.
        auth_token:     Synapse Personal Access Token (overrides env var).
        username:       Synapse username (overrides env var).
        password:       Synapse password (overrides env var).
        skip_clinical:  Skip the clinical variable file if not needed.

    Returns:
        True if the primary proteomics matrix was downloaded successfully.
    """
    rosmap_dir = Path(output_dir) / "ROSMAP"
    rosmap_dir.mkdir(parents=True, exist_ok=True)

    ids = synapse_ids or ROSMAP_SYNAPSE_IDS
    manifest = ManifestManager(Path("data/manifest.json"))

    syn = _build_syn_client(auth_token, username, password)
    if syn is None:
        return False

    logger.info(f"Downloading ROSMAP proteomics -> {rosmap_dir}")

    proteomics_ok = False

    for key, syn_id in ids.items():
        if skip_clinical and key == "clinical":
            logger.info(f"  Skipping {key} (skip_clinical=True)")
            continue

        manifest_key = f"rosmap_{key}"

        # Resume: verify cache before re-downloading
        if manifest.file_exists(manifest_key):
            info = manifest.get_file(manifest_key)
            cached_path = Path(info["path"])
            if cached_path.exists() and manifest.verify_file(manifest_key, cached_path):
                logger.info(f"  {key}: already verified at {cached_path.name}")
                if key == "proteomics_tmt":
                    proteomics_ok = True
                continue
            logger.info(f"  {key}: cached record invalid — re-downloading")

        try:
            logger.info(f"  Downloading {key}  ({syn_id}) …")
            entity = syn.get(syn_id, downloadLocation=str(rosmap_dir))
            file_path = Path(entity.path)

            manifest.add_file(
                manifest_key,
                file_path,
                source="Synapse",
                metadata={
                    "cohort": "ROSMAP",
                    "type": key,
                    "synapse_id": syn_id,
                    "dataset": "AMP-AD",
                },
            )
            size_mb = file_path.stat().st_size / 1e6
            logger.info(f"    Saved: {file_path.name}  ({size_mb:.1f} MB)")

            if key == "proteomics_tmt":
                proteomics_ok = True

        except Exception as exc:
            logger.error(f"  Failed to download {key} ({syn_id}): {exc}")
            if key == "proteomics_tmt":
                return False   # Primary file is required

    logger.info("ROSMAP download complete" if proteomics_ok else "ROSMAP download INCOMPLETE")
    return proteomics_ok


def rosmap_files_present(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Tuple[bool, Path]:
    """
    Return (True, path) if the ROSMAP proteomics file already exists on disk.
    Used by the pipeline to skip download when real data is already cached.
    """
    rosmap_dir = Path(output_dir) / "ROSMAP"
    manifest = ManifestManager(Path("data/manifest.json"))

    if manifest.file_exists("rosmap_proteomics_tmt"):
        info = manifest.get_file("rosmap_proteomics_tmt")
        p = Path(info["path"])
        if p.exists():
            return True, p

    # Fallback: glob for any CSV/TSV file in the ROSMAP directory
    for ext in ("*.csv", "*.tsv", "*.txt"):
        matches = list(rosmap_dir.glob(ext))
        if matches:
            return True, matches[0]

    return False, rosmap_dir


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download ROSMAP TMT proteomics from AMP-AD (Synapse)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authentication (choose one):
  export SYNAPSE_AUTH_TOKEN=<PAT>          # Personal Access Token (recommended)
  export SYNAPSE_USER=u  SYNAPSE_PASS=p   # Username + password
  synapse login                            # Cache credentials once

Then run:
  python -m src.download.download_ampad_rosmap
  python -m src.download.download_ampad_rosmap --output data/raw/ampad
""",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Root output directory (default: data/raw/ampad)",
    )
    parser.add_argument(
        "--auth-token",
        default=None,
        help="Synapse Personal Access Token (overrides SYNAPSE_AUTH_TOKEN env var)",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Synapse username (overrides SYNAPSE_USER env var)",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Synapse password (overrides SYNAPSE_PASS env var)",
    )
    parser.add_argument(
        "--skip-clinical",
        action="store_true",
        help="Skip downloading the clinical variable file",
    )
    args = parser.parse_args()

    ok = download_rosmap_proteomics(
        output_dir=Path(args.output),
        auth_token=args.auth_token,
        username=args.username,
        password=args.password,
        skip_clinical=args.skip_clinical,
    )
    sys.exit(0 if ok else 1)
