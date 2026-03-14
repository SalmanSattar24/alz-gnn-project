# Ranking Stability Analysis

## Overview

The ranking stability analysis module (`src/analysis/stability.py`) quantifies how stable the GNN model's protein rankings are across different samples and analyses the consistency of biomarker discovery across cohorts.

## Key Concepts

### 1. Jaccard Similarity
Measures the overlap between top-k protein lists across bootstrap iterations:

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

**Interpretation:**
- **1.0**: Perfect overlap - all proteins in top-k are identical
- **0.5**: Moderate overlap - 50% of proteins match
- **0.0**: No overlap - completely different proteins selected

### 2. Kuncheva Stability Index
A statistical measure of consistency that accounts for random chance:

```
K_i = (p_i / k - (t/n)²) / ((t/n) × (1 - t/n))
```

Where:
- p_i = number of common features in top-k lists
- k = size of top-k
- t = size of top-k
- n = total number of features

**Interpretation:**
- **K > 0**: More stable than random selection
- **K ≤ 0**: Less stable than random
- **K close to 1**: Excellent stability
- **K > 0.3**: Generally considered good stability

### 3. Bootstrap Stability Curves
Plot how Jaccard similarity and Kuncheva index change with different values of k:

- **X-axis**: k (1 to 500, step 10)
- **Left Y-axis**: Jaccard similarity (0 to 1)
- **Right Y-axis**: Kuncheva index
- **Curves show**: How top-k selection changes with k value

**What to look for:**
- High plateau: Stable top proteins are consistently selected
- Steep drop: Proteins outside top-k are less consistently selected
- Positive Kuncheva: Bootstrap is more stable than random

### 4. Cross-Cohort Overlap
Measures protein ranking consistency across ROSMAP, MSBB, and MAYO cohorts:

- **Jaccard similarity matrix**: Shows pairwise overlap between cohorts
- **Shared proteins**: Proteins appearing in top-k across all cohorts
- **Pairwise overlap**: Jaccard index for each cohort pair

**Interpretation:**
- **High overlap (>0.6)**: Consistent biomarkers across cohorts
- **Moderate overlap (0.3-0.6)**: Some consistency
- **Low overlap (<0.3)**: Cohort-specific patterns

### 5. Permutation Tests
Statistical significance testing via random permutations:

**Method:**
1. Shuffle bootstrap ranks randomly
2. Recompute Kuncheva index on shuffled data
3. Compare to real Kuncheva index
4. p-value = fraction of permutations with equal or higher stability

**Interpretation:**
- **p < 0.05**: Real stability significantly better than random
- **p ≥ 0.05**: Cannot reject random baseline
- **p < 0.001**: Very strong evidence of non-random stability

## Core Classes

### `RankingStabilityAnalyzer`
Analyzes stability of protein rankings from bootstrap analysis.

```python
from src.analysis.stability import RankingStabilityAnalyzer

analyzer = RankingStabilityAnalyzer(
    bootstrap_ranks={"PROT_0": [0, 5, 2, ...], ...},
    protein_ids=["PROT_0", "PROT_1", ...],
    n_bootstrap=100
)

# Compute Jaccard stability across bootstrap iterations
jaccard_stats = analyzer.compute_jaccard_stability(k=100)
# Returns: mean, median, std of Jaccard similarities

# Compute Kuncheva stability index
kuncheva = analyzer.compute_kuncheva_index(k=100)

# Stability curves for multiple k values
stability_df = analyzer.compute_stability_curves(k_values=[10, 20, 50, 100])

# Plot results
fig = analyzer.plot_stability_curves(stability_df)
```

### `CrossCohortAnalyzer`
Analyzes protein ranking overlap across cohorts.

```python
from src.analysis.stability import CrossCohortAnalyzer

cohort_reports = {
    "ROSMAP": pd.read_csv("ROSMAP_protein_attributions.csv"),
    "MSBB": pd.read_csv("MSBB_protein_attributions.csv"),
    "MAYO": pd.read_csv("MAYO_protein_attributions.csv"),
}

analyzer = CrossCohortAnalyzer(cohort_reports, results_dir="/tmp")

# Compute pairwise overlap
overlap = analyzer.compute_pairwise_overlap(k=100)
# Returns: DataFrame with intersection, Jaccard, % overlap

# Get shared proteins across all cohorts
shared = analyzer.get_shared_proteins(k=100)
# Returns: {"all_shared": set, "n_all_shared": int, "shared_proteins": list}

# Create heatmap
fig = analyzer.plot_overlap_heatmap(k=100)
```

### `PermutationTest`
Runs statistical significance tests on stability measures.

```python
from src.analysis.stability import PermutationTest

perm_test = PermutationTest(
    bootstrap_ranks=bootstrap_ranks,
    protein_ids=protein_ids,
    n_permutations=1000
)

# Run permutation test
result = perm_test.run_permutation_test(k=100)
# Returns: {"real_stability": float, "perm_stabilities": list,
#           "p_value": float, ...}
```

## Output Files

### 1. **stability_report.md**
Comprehensive markdown report containing:
- Jaccard stability metrics table (k vs stability)
- Kuncheva index table
- Cross-cohort overlap statistics
- Shared proteins across all cohorts
- Interpretation guidelines

### 2. **stability_curves.png**
Two-panel figure showing:
- **Left**: Jaccard similarity vs k (mean ± std dev)
- **Right**: Kuncheva index vs k with confidence bands

### 3. **cohort_overlap_heatmap.png**
Heatmap showing:
- **Rows/Columns**: Cohorts (ROSMAP, MSBB, MAYO)
- **Values**: Jaccard similarity between cohort pairs
- **Color**: Green (high overlap) to Red (low overlap)

## Usage

### Quick Start

```bash
# Run after explainability analysis
python src/models/train.py --config config.yaml --stability-only
```

### Python API

```python
from src.analysis.stability import run_stability_analysis

results = run_stability_analysis(
    config_path="config.yaml",
    n_bootstrap_iters=1000,
    cohorts=["ROSMAP", "MSBB", "MAYO"]
)
```

### Jupyter Notebook

```python
from src.models.train import analyze_stability

# Run stability analysis
results = analyze_stability(config_path="config.yaml")
```

## Biological Interpretation

### High-Stability Proteins
Proteins with:
- Jaccard similarity > 0.7 at top-100
- Kuncheva index > 0.3
- High ranking consistency across bootstrap iterations

**Implication**: Robust biomarkers with strong evidence from data

### Moderately-Stable Proteins
Proteins with:
- Jaccard similarity 0.5-0.7
- Kuncheva index 0-0.3
- Variable ranking across iterations

**Implication**: Important but require validation

### Unstable Proteins
Proteins with:
- Jaccard similarity < 0.5
- Kuncheva index < 0
- Highly variable ranking

**Implication**: Less reliable, may be noise

### High Cross-Cohort Overlap
Proteins in top-100 across ROSMAP, MSBB, MAYO:
- Strong evidence for true AD biomarkers
- Likely biological relevance
- Good candidates for clinical validation

### Low Cross-Cohort Overlap
Cohort-specific top proteins:
- May reflect technical differences
- Biological heterogeneity between populations
- Requires investigation before clinical use

## Expected Results

### Typical Stability Curve
- **Top 20**: Jaccard ~0.6-0.8 (stable core)
- **Top 100**: Jaccard ~0.5-0.6 (reasonably stable)
- **Top 500**: Jaccard ~0.3-0.4 (decreasing stability)

### Cross-Cohort Overlap
- **All cohorts**: 5-15% of top-100 proteins
- **Pairwise average**: 40-60% Jaccard similarity
- **High overlap proteins**: Strong biomarker candidates

### Permutation Tests
- **Significant proteins**: Usually p < 0.05 for top-100
- **Stable curves**: Kuncheva > 0 across most k values
- **Strong evidence**: Multiple cohorts show consistent patterns

## Performance Considerations

**Computational Requirements:**
- Jaccard computation: O(k × n_bootstrap²) for n_bootstrap pairwise comparisons
- Kuncheva index: O(k × n_bootstrap) for rank aggregation
- Permutation tests: O(n_permutations × k × n_bootstrap)

**Runtime (CPU):**
- Jaccard stability curves (k_values=50): ~5-10 seconds
- Cross-cohort analysis: ~1-2 seconds
- Permutation tests (1000 perms): ~5-10 minutes
- Full analysis: ~15-20 minutes per cohort

**Memory:**
- Bootstrap ranks storage: ~5-10 MB per cohort
- Stability curves: <1 MB
- Heatmaps/plots: Generated on-the-fly

## Advanced Usage

### Custom k Values

```python
stability_df = analyzer.compute_stability_curves(
    k_values=list(range(5, 501, 5))  # Step of 5
)
```

### Multiple Permutation Tests

```python
for k in [50, 100, 200]:
    result = perm_test.run_permutation_test(k=k)
    print(f"k={k}: p-value={result['p_value']:.4f}")
```

### Overlap at Multiple Thresholds

```python
for k in [10, 20, 50, 100, 200]:
    overlap_matrix = analyzer.compute_pairwise_overlap(k=k)
    print(f"Top-{k}: Average Jaccard = {overlap_matrix['jaccard'].mean():.3f}")
```

## References

- Jaccard Similarity: Jaccard, P. (1912). "The distribution of the flora in the alpine zone."
- Kuncheva Index: Kuncheva, L. I. (2007). "A stability index for feature selection."
- Bootstrap Methods: Efron, B., & Tibshirani, R. J. (1993). "An introduction to the bootstrap."
- Permutation Tests: Good, P. (2005). "Permutation tests: a practical guide to resampling methods."
