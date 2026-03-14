"""
Mock data generator for testing pipeline without real datasets.

Generates synthetic proteomics and network data that matches the structure
of real datasets, allowing the full pipeline to run for development/testing.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

from src.download.utils import ManifestManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Mock dataset configuration
MOCK_PROTEINS = 5000  # Number of proteins
MOCK_SAMPLES = 200  # Number of samples
MOCK_TISSUES = 54  # GTEx tissues


def generate_mock_ampad(output_dir: Path = Path("data/raw/ampad")) -> bool:
    """
    Generate mock AMP-AD proteomics data.

    Args:
        output_dir: Output directory for mock data

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Generating mock AMP-AD data to {output_dir}")

    cohorts = {
        "ROSMAP": {"samples": 100, "n_ad": 60, "n_control": 40},
        "MSBB": {"samples": 80, "n_ad": 50, "n_control": 30},
        "MAYO": {"samples": 90, "n_ad": 55, "n_control": 35},
    }

    # Generate UniProt protein IDs
    protein_ids = [f"P{str(i).zfill(5)}" for i in range(1, MOCK_PROTEINS + 1)]

    for cohort_name, cohort_info in cohorts.items():
        cohort_dir = output_dir / cohort_name
        cohort_dir.mkdir(exist_ok=True)

        # Generate proteomics data (log-normalized intensity)
        np.random.seed(42 + hash(cohort_name) % 100)
        proteomics = np.random.normal(loc=5, scale=1.5, size=(MOCK_PROTEINS, cohort_info["samples"]))

        # Add disease signal to first 200 proteins
        disease_indices = np.random.choice(MOCK_PROTEINS, size=200, replace=False)
        ad_samples = slice(0, cohort_info["n_ad"])
        proteomics[disease_indices, ad_samples] += np.random.normal(0, 0.5, size=(200, cohort_info["n_ad"]))

        # Create DataFrame
        sample_names = [f"{cohort_name}_S{i:04d}" for i in range(cohort_info["samples"])]
        proteomics_df = pd.DataFrame(
            proteomics,
            index=protein_ids,
            columns=sample_names,
        )

        # Save proteomics
        proteomics_path = cohort_dir / f"{cohort_name}_proteomics.csv.gz"
        proteomics_df.to_csv(proteomics_path, compression="gzip")

        manifest.add_file(
            f"mock_ampad_{cohort_name}_proteomics",
            proteomics_path,
            source="Mock",
            metadata={
                "cohort": cohort_name,
                "n_proteins": MOCK_PROTEINS,
                "n_samples": cohort_info["samples"],
                "n_ad": cohort_info["n_ad"],
                "n_control": cohort_info["n_control"],
            },
        )

        # Generate metadata
        metadata = pd.DataFrame({
            "sample_id": sample_names,
            "cohort": [cohort_name] * cohort_info["samples"],
            "diagnosis": ["AD"] * cohort_info["n_ad"] + ["Control"] * cohort_info["n_control"],
            "age": np.random.normal(75, 10, cohort_info["samples"]),
            "sex": np.random.choice(["M", "F"], size=cohort_info["samples"]),
        })

        metadata_path = cohort_dir / f"{cohort_name}_metadata.csv"
        metadata.to_csv(metadata_path, index=False)

        manifest.add_file(
            f"mock_ampad_{cohort_name}_metadata",
            metadata_path,
            source="Mock",
            metadata={
                "cohort": cohort_name,
                "sample_count": len(metadata),
            },
        )

        logger.info(f"  Generated {cohort_name}: {MOCK_PROTEINS} proteins x {cohort_info['samples']} samples")

    return True


def generate_mock_pride(output_dir: Path = Path("data/raw/pride")) -> bool:
    """
    Generate mock PRIDE proteomics data.

    Args:
        output_dir: Output directory for mock data

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Generating mock PRIDE data to {output_dir}")

    projects = {
        "PXD000560": {"samples": 50, "description": "Alzheimer's disease brain proteomics"},
        "PXD004165": {"samples": 40, "description": "APP transgenic mouse models"},
        "PXD010871": {"samples": 35, "description": "Amyloid-beta aggregates"},
    }

    protein_ids = [f"Q{str(i).zfill(5)}" for i in range(1, 3000)]  # Subset of proteins

    for pxd_id, project_info in projects.items():
        project_dir = output_dir / pxd_id
        project_dir.mkdir(exist_ok=True)

        # Generate expression data
        np.random.seed(42 + hash(pxd_id) % 100)
        expression = np.random.lognormal(mean=5, sigma=2, size=(len(protein_ids), project_info["samples"]))

        sample_names = [f"{pxd_id}_sample_{i:03d}" for i in range(project_info["samples"])]
        expression_df = pd.DataFrame(
            expression,
            index=protein_ids,
            columns=sample_names,
        )

        expression_path = project_dir / f"{pxd_id}_expression.csv.gz"
        expression_df.to_csv(expression_path, compression="gzip")

        manifest.add_file(
            f"mock_pride_{pxd_id}",
            expression_path,
            source="Mock",
            metadata={
                "project_id": pxd_id,
                "description": project_info["description"],
                "n_proteins": len(protein_ids),
                "n_samples": project_info["samples"],
            },
        )

        logger.info(f"  Generated {pxd_id}: {len(protein_ids)} proteins x {project_info['samples']} samples")

    return True


def generate_mock_string(output_dir: Path = Path("data/raw/string")) -> bool:
    """
    Generate mock STRING protein interaction network.

    Args:
        output_dir: Output directory for mock data

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Generating mock STRING data to {output_dir}")

    # Generate protein interaction edges
    np.random.seed(42)
    n_edges = 50000
    n_proteins = 5000

    protein_ids = [f"ENSP{str(i).zfill(8)}" for i in range(1, n_proteins + 1)]

    # Create interaction edges
    protein1 = np.random.choice(protein_ids, size=n_edges)
    protein2 = np.random.choice(protein_ids, size=n_edges)
    scores = np.random.randint(400, 1000, size=n_edges)

    # Filter for score >= 700
    mask = scores >= 700
    edges = pd.DataFrame({
        "protein1": protein1[mask],
        "protein2": protein2[mask],
        "combined_score": scores[mask],
    })

    edges_path = output_dir / "protein_interactions.csv.gz"
    edges.to_csv(edges_path, compression="gzip", index=False)

    manifest.add_file(
        "mock_string_edges",
        edges_path,
        source="Mock",
        metadata={
            "total_edges": len(edges),
            "n_proteins": n_proteins,
            "score_threshold": 700,
        },
    )

    logger.info(f"  Generated STRING network: {len(edges)} edges with score >= 700")

    return True


def generate_mock_gtex(output_dir: Path = Path("data/raw/gtex")) -> bool:
    """
    Generate mock GTEx tissue expression data.

    Args:
        output_dir: Output directory for mock data

    Returns:
        True if successful
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ManifestManager(Path("data/manifest.json"))

    logger.info(f"Generating mock GTEx data to {output_dir}")

    # GTEx tissues
    tissues = [
        "Adipose_Subcutaneous", "Adipose_Visceral", "Adrenal_Gland", "Artery_Aorta",
        "Artery_Coronary", "Artery_Tibial", "Bladder", "Brain_Amygdala", "Brain_Anterior",
        "Brain_Caudate", "Brain_Cerebellum", "Brain_Cerebral_Cortex", "Brain_Cortex",
        "Brain_Frontal_Cortex", "Brain_Hippocampus", "Brain_Hypothalamus", "Brain_Nucleus",
        "Brain_Putamen", "Brain_Spinal_Cord", "Brain_Substantia_Nigra", "Breast_Mammary",
        "Cells_Cultured_Fibroblasts", "Cells_EBV_Lymphocytes", "Colon_Sigmoid",
        "Colon_Transverse", "Coronary_Artery", "Esophagus_Gastroesophageal", "Esophagus_Mucosa",
        "Esophagus_Muscularis", "Fallopian_Tube", "Heart_Atrial_Appendage", "Heart_Left_Ventricle",
        "Kidney_Cortex", "Kidney_Medulla", "Liver", "Lung", "Minor_Salivary_Gland",
        "Muscle_Skeletal", "Nerve_Tibial", "Ovary", "Pancreas", "Pituitary",
        "Prostate", "Skin_Not_Sun_Exposed", "Skin_Sun_Exposed", "Small_Intestine_Terminal",
        "Spleen", "Stomach", "Testis", "Thyroid", "Uterus", "Vagina",
    ][:MOCK_TISSUES]

    # Generate expression
    protein_ids = [f"ENSG{str(i).zfill(8)}" for i in range(1, MOCK_PROTEINS + 1)]
    np.random.seed(42)
    expression = np.random.lognormal(mean=3, sigma=2, size=(MOCK_PROTEINS, len(tissues)))

    expression_df = pd.DataFrame(
        expression,
        index=protein_ids,
        columns=tissues,
    )

    expression_path = output_dir / "gtex_tissue_expression.csv.gz"
    expression_df.to_csv(expression_path, compression="gzip")

    manifest.add_file(
        "mock_gtex_expression",
        expression_path,
        source="Mock",
        metadata={
            "n_genes": MOCK_PROTEINS,
            "n_tissues": len(tissues),
            "tissues": tissues,
        },
    )

    logger.info(f"  Generated GTEx data: {MOCK_PROTEINS} genes x {len(tissues)} tissues")

    return True


def generate_all_mock_data(output_base: Path = Path("data/raw")) -> bool:
    """
    Generate all mock datasets.

    Args:
        output_base: Base output directory

    Returns:
        True if successful
    """
    logger.info("=" * 60)
    logger.info("GENERATING MOCK DATASETS FOR PIPELINE TESTING")
    logger.info("=" * 60)

    try:
        success = True
        success &= generate_mock_ampad(output_base / "ampad")
        success &= generate_mock_pride(output_base / "pride")
        success &= generate_mock_string(output_base / "string")
        success &= generate_mock_gtex(output_base / "gtex")

        if success:
            logger.info("\n" + "=" * 60)
            logger.info("MOCK DATA GENERATION COMPLETE")
            logger.info("=" * 60)
            logger.info("Ready for pipeline testing!")

        return success
    except Exception as e:
        logger.error(f"Mock data generation failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate mock datasets for testing")
    parser.add_argument(
        "--output",
        default="data/raw",
        help="Base output directory for mock data",
    )
    args = parser.parse_args()

    success = generate_all_mock_data(Path(args.output))
    exit(0 if success else 1)
