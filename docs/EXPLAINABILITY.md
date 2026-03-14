# Explainability Analysis for GNN Models

## Overview

The explainability module (`src/explain/explain_model.py`) provides comprehensive analysis of Graph Attention Network predictions for Alzheimer's disease classification using proteomics data. It implements multiple explanation methods to understand which proteins drive the model's decisions.

## Features

### 1. Multiple Explanation Methods

#### Attention-Based Attribution
- Extracts node importance scores directly from the GAT model's attribution head
- Computes normalized importance for each protein in the graph
- Fast and interpretable: high scores indicate proteins influential to the model
- Used by default: `method="attention"`

#### Integrated Gradients (Captum)
- Advanced method using gradient-based attribution
- Integrates gradients along a path from zero baseline to actual input
- Captures how each protein feature influences the final prediction
- Optional: `method="integrated_gradients"` (requires Captum package)

#### GNNExplainer
- Graph-level explanation via edge subgraph masking
- Identifies which edges and nodes are most important for predictions
- Currently available but not used in main pipeline (for future work)

### 2. Aggregation Across Samples

The module computes per-protein attribution statistics across all training samples:

```
Columns in output CSV:
- protein: Protein identifier
- mean_attr: Mean attribution across samples [0, 1]
- median_attr: Median attribution across samples [0, 1]
- std_attr: Standard deviation of attribution values
- min_attr: Minimum attribution value
- max_attr: Maximum attribution value
- n_samples: Number of samples analyzed
- bootstrap_frequency_top100: How often protein appears in top-100 (0-100)
```

### 3. Bootstrap Stability Analysis

Robust uncertainty quantification via bootstrap resampling:

**Method:**
1. Resample training samples with replacement (100 iterations)
2. Compute aggregated attributions for each bootstrap sample
3. Track protein rankings across all iterations
4. Compute stability metrics:
   - `bootstrap_frequency_top100`: Frequency protein appears in top-100 across 100 bootstrap samples
   - `bootstrap_mean_rank`: Average rank across bootstrap samples
   - `bootstrap_std_rank`: Standard deviation of rank (lower = more stable)

**Interpretation:**
- High `bootstrap_frequency_top100`: Protein is consistently important
- Low `bootstrap_std_rank`: Protein has stable ranking (reliable)
- Proteins with both high frequency and low std are most robust

### 4. Stability Visualization

Four-panel figure showing attribution stability:

1. **Mean Bootstrap Rank Distribution**: Histogram of average protein ranks
2. **Std Bootstrap Rank Distribution**: Histogram of rank variability
3. **Top 20 Most Stable Proteins**: Bar plot with error bars (mean rank ± std)
4. **Mean vs Std Scatter Plot**: Relationship between rank stability and variability

## Core Classes

### `GNNModelExplainer`

Unified interface for explaining individual samples.

```python
explainer = GNNModelExplainer(model, dataset, device)

# Explain single sample
attr_df = explainer.explain_sample(sample_idx=0, method="attention")
# Returns: DataFrame with protein_id and importance columns
```

**Methods:**
- `explain_sample_attention()`: Get attributions via attention weights
- `explain_sample_integrated_gradients()`: Get attributions via Integrated Gradients
- `explain_sample()`: Unified interface for both methods

### `ExplainabilityAnalysis`

Main analysis class orchestrating full pipeline.

```python
analyzer = ExplainabilityAnalysis(
    model_path=Path("model.pt"),
    dataset=dataset,
    results_dir=Path("results/"),
    device=device
)

# Generate complete report
report = analyzer.generate_protein_attribution_report(
    train_indices=train_indices,
    n_bootstrap=100,
    method="attention"
)

# Get stability metrics
bootstrap_res = analyzer.bootstrap_stability_analysis(
    sample_indices=train_indices,
    n_bootstrap=100,
    method="attention"
)

# Create visualization
fig = analyzer.plot_attribution_stability(
    bootstrap_res["all_bootstrap_ranks"],
    top_n=20
)

# Save all outputs
analyzer.save_results(report, fig, output_name="ROSMAP_protein_attributions")
```

**Output Files:**
- `ROSMAP_protein_attributions.csv`: Complete attribution statistics
- `ROSMAP_protein_attributions_stability.png`: Stability visualization
- `ROSMAP_protein_attributions_summary.json`: Summary statistics

## Usage

### Quick Start

```python
from src.explain.explain_model import explain_model

# Run explainability for all cohorts
results = explain_model(config_path="config.yaml")
```

### Advanced Usage

```python
from pathlib import Path
from src.explain.explain_model import ExplainabilityAnalysis
from src.models.gnn_model import ProteinGraphDataset
import torch

# Load data
dataset = ProteinGraphDataset(
    graph_path="data/graphs/ROSMAP_graph.graphml",
    processed_data_path="data/processed/ROSMAP_processed.h5ad",
)

# Create analyzer
analyzer = ExplainabilityAnalysis(
    model_path=Path("models/ROSMAP_gnn_model.pt"),
    dataset=dataset,
    results_dir=Path("results/explainability/"),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
)

# Get train indices
train_indices, val_indices, test_indices = dataset.get_train_val_test_split()

# Run analysis with custom parameters
report = analyzer.generate_protein_attribution_report(
    train_indices=train_indices,
    n_bootstrap=100,  # Can increase for more robust estimates
    method="attention"  # Or "integrated_gradients"
)

print(f"Top 10 proteins: {report.head(10)['protein'].tolist()}")
print(f"Mean stability: {report['std_attr'].mean():.4f}")
```

### Command-Line Execution

```bash
# Full training + explainability pipeline
python src/models/train.py --config config.yaml

# Explainability only (after models are trained)
python src/models/train.py --config config.yaml --explain-only

# Explainability from explain_model.py directly
python src/explain/explain_model.py --config config.yaml
```

## Output Interpretation

### CSV Report

Example output for ROSMAP cohort:

```
protein,mean_attr,median_attr,std_attr,min_attr,max_attr,n_samples,bootstrap_frequency_top100
APOE,0.856,0.871,0.043,0.712,0.932,290,95
TP53,0.824,0.839,0.061,0.589,0.945,290,92
APP,0.798,0.812,0.074,0.421,0.932,290,88
PSEN1,0.791,0.805,0.068,0.432,0.924,290,85
...
```

**Interpretation:**
- **APOE**: Mean importance 0.856 (strong predictor)
  - Consistently in top-100 (frequency=95/100)
  - Low variability (std=0.043) → reliable
  - Biological: APOE is known risk factor for AD

- **Rare protein**: Low mean_attr, low bootstrap_frequency
  - Model doesn't rely on this protein
  - High std_attr → unreliable if sampled

### Stability Plot

- **Top panel left**: Most proteins have ranks concentrated around 2500-3500 (out of 5000)
- **Top panel right**: Most proteins have low rank variability, indicating stable importance
- **Bottom left**: Top-20 most stable proteins with error bars
- **Bottom right**: Strong correlation between mean rank and variability

## Biological Interpretation

### High-Importance Proteins (Top 10-20)
These are the model's primary decision drivers:
- Check literature for known AD associations
- Validate with independent datasets (ADNIGO, ADNI, etc.)
- Consider for targeted biomarker development

### Stability Metrics
- **High bootstrap_frequency_top100 + Low std**: Robust biomarkers
- **High bootstrap_frequency but High std**: Important but variable
- **Low bootstrap_frequency**: Model doesn't rely on this protein

### Cross-Cohort Comparison
Compare top proteins across ROSMAP, MSBB, MAYO:
- **Consistent**: Likely true AD biomarkers
- **Cohort-specific**: May reflect technical/biological differences

## Testing

Comprehensive test suite in `tests/test_explain_model.py`:

```bash
# Run all explainability tests
pytest tests/test_explain_model.py -v

# Run specific test
pytest tests/test_explain_model.py::test_attribution_aggregation -v
```

**Test Coverage:**
- GNNExplainer initialization
- Attention-based explanations
- Sample explanation generation
- Attribution aggregation
- Bootstrap sampling and ranking
- Frequency computation
- Model checkpoint loading

## Performance Notes

**Computational Requirements:**
- Per-sample explanation: ~50-100ms (CPU), ~10-20ms (GPU)
- Aggregation across N samples: O(N) memory, O(N) time
- Bootstrap with 100 iterations: ~5-10 minutes per cohort (GPU)

**Optimization Tips:**
1. Use GPU (CUDA) for significant speedup
2. Reduce bootstrap iterations for quick tests (e.g., n_bootstrap=10)
3. Process only training set (smaller than full dataset)
4. Cache model state if running multiple analyses

## Dependencies

**Required:**
- torch, torch_geometric
- pandas, numpy
- matplotlib, seaborn
- scikit-learn

**Optional:**
- captum (for Integrated Gradients method)

Install optional dependencies:
```bash
pip install captum
```

## Future Enhancements

1. **GNNExplainer Integration**: Full graph-level explanations
2. **Attention Visualization**: Visualize GAT attention patterns
3. **Protein Interaction Paths**: Identify important subgraphs
4. **Perturbation Analysis**: Ablate proteins and measure impact
5. **Multi-method Ensemble**: Combine attention, gradients, and GNNExplainer
6. **Cohort-specific Models**: Identify cohort-specific biomarkers

## References

- Graph Attention Networks: Veličković et al., ICLR 2018
- Integrated Gradients: Sundararajan et al., ICML 2017
- GNNExplainer: Ying et al., NeurIPS 2019
- Captum Documentation: https://captum.ai/
