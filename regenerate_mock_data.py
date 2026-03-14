"""
Rebuild mock proteomics data with protein IDs compatible with STRING network.
"""

import gzip
import numpy as np
import pandas as pd
from pathlib import Path

# Load first 5000 unique proteins from STRING network
print("Reading STRING network to extract protein IDs...")
proteins = set()

with gzip.open("data/raw/string/protein.links.v11.5.txt.gz", "rt") as f:
    header = next(f)
    for line in f:
        if len(proteins) >= 5000:
            break
        parts = line.strip().split()
        proteins.add(parts[0])
        proteins.add(parts[1])

protein_list = sorted(list(proteins))[:5000]
print(f"Extracted {len(protein_list)} unique protein IDs from STRING")
print(f"Example IDs: {protein_list[:5]}")

# Regenerate mock AMP-AD proteomics with these IDs
print("\nRegenerating mock AMP-AD proteomics with compatible IDs...")

random_state = 42
np.random.seed(random_state)

cohorts = {
    "ROSMAP": {"samples": 100, "n_ad": 60, "n_control": 40},
    "MSBB": {"samples": 80, "n_ad": 50, "n_control": 30},
    "MAYO": {"samples": 90, "n_ad": 55, "n_control": 35},
}

for cohort_name, cohort_info in cohorts.items():
    cohort_dir = Path("data") / "raw" / "ampad" / cohort_name

    # Generate proteomics data
    proteomics = np.random.normal(loc=5, scale=1.5, size=(len(protein_list), cohort_info["samples"]))

    # Add disease signal
    disease_indices = np.random.choice(len(protein_list), size=200, replace=False)
    ad_samples = slice(0, cohort_info["n_ad"])
    proteomics[disease_indices, ad_samples] += np.random.normal(0, 0.5, size=(200, cohort_info["n_ad"]))

    # Create DataFrame
    sample_names = [f"{cohort_name}_S{i:04d}" for i in range(cohort_info["samples"])]
    proteomics_df = pd.DataFrame(
        proteomics,
        index=protein_list,
        columns=sample_names,
    )

    # Save
    proteomics_path = cohort_dir / f"{cohort_name}_proteomics.csv.gz"
    proteomics_df.to_csv(proteomics_path, compression="gzip")
    print(f"Saved: {proteomics_path} ({proteomics_df.shape})")

    # Metadata
    metadata = pd.DataFrame({
        "sample_id": sample_names,
        "cohort": [cohort_name] * cohort_info["samples"],
        "diagnosis": ["AD"] * cohort_info["n_ad"] + ["Control"] * cohort_info["n_control"],
        "age": np.random.normal(75, 10, cohort_info["samples"]),
        "sex": np.random.choice(["M", "F"], size=cohort_info["samples"]),
    })

    metadata_path = cohort_dir / f"{cohort_name}_metadata.csv"
    metadata.to_csv(metadata_path, index=False)
    print(f"Saved: {metadata_path}")

print("\nMock data regeneration complete!")
print("Now preprocessing and graph building should work with matching protein IDs.")
