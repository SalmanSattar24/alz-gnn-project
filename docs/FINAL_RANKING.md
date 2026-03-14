# Final Protein Prioritization Ranking

## Overview

The final ranking module integrates multiple biomarker discovery signals to create a comprehensive protein prioritization score. This enables identification of high-confidence therapeutic targets for Alzheimer's disease.

## Scoring System

### Composite Score Formula

```
score = normalized(GNN_attribution) × normalized(centrality) × (1 + stability_weight)

where:
  stability_weight = log(1 + bootstrap_frequency) / log(101)
```

### Score Components

1. **GNN Attribution (Explainability)**
   - Source: `mean_attr` from explainability analysis
   - Range: [0, 1] after normalization
   - Represents: How important protein is to AD prediction
   - Higher = more influential in model decisions

2. **Network Centrality (Topology)**
   - Source: Protein interaction graph analysis
   - Combines: Degree, betweenness, closeness centrality
   - Range: [0, 1] after normalization
   - Represents: Hub importance in protein network
   - Higher = more connected, network hub

3. **Bootstrap Stability Weight**
   - Source: `bootstrap_frequency_top100` from stability analysis
   - Formula: log(1 + frequency) / log(101)
   - Range: [0, 1]
   - Represents: Ranking consistency across bootstrap iterations
   - Higher = more stable, more reliable biomarker

### Interpretation

**Multiplicative Combination Rationale:**
- All components must be high for high total score
- Missing evidence in any dimension reduces score
- Prevents false positives from single-signal artifacts

**Score Distribution:**
- Top 1%: High confidence targets (score > 75th percentile)
- Top 5%: Moderate-high confidence (score > 50th percentile)
- Top 10%: Moderate confidence (score > 25th percentile)
- Rank 11-100: Supporting candidates

## Output Files

### 1. `final_protein_targets.csv`
Complete ranking of all proteins with scores.

**Columns:**
- `protein`: Protein identifier
- `gene`: Gene name (mapped from protein ID)
- `composite_score`: Final prioritization score [0, 1]
- `gnn_importance`: Normalized GNN attribution [0, 1]
- `centrality`: Normalized network centrality [0, 1]
- `stability`: Bootstrap frequency (0-100)

**Sorted by:** composite_score (descending)

Example:
```
protein,gene,composite_score,gnn_importance,centrality,stability
ENSP00001,TP53,0.8725,0.85,0.92,95
ENSP00002,APOE,0.8614,0.82,0.90,92
ENSP00003,APP,0.8521,0.80,0.88,89
...
```

### 2. `top_20_proteins.png`
Publication-ready table of top 20 prioritized proteins.

Features:
- Ranked list (1-20)
- All metric scores
- Professional formatting
- Color-coded rows

### 3. `disease_module_network.png`
Network visualization of top-50 protein disease module.

Features:
- Top-20 proteins highlighted in red
- Supporting proteins in blue
- Node size proportional to composite score
- Edge network shows protein interactions
- Labels on top-20 proteins
- Spring layout for readability

### 4. `ranking_summary.json`
Summary statistics in JSON format.

Contents:
- Total proteins ranked
- Top 10 and top 100 proteins
- Score statistics (mean, std, min, max)
- Cohort information

## Usage

### Command Line

```bash
# Full pipeline including ranking
python src/models/train.py --config config.yaml

# Ranking only (after explainability/stability)
python src/models/train.py --config config.yaml --rank-only

# Direct execution
python src/analysis/final_ranking.py --config config.yaml
```

### Python API

```python
from src.analysis.final_ranking import run_protein_prioritization

results = run_protein_prioritization(
    config_path="config.yaml",
    cohorts=["ROSMAP", "MSBB", "MAYO"]
)

# Access results
for cohort, data in results.items():
    ranking_df = data["ranking"]
    top_20 = data["top_20"]
```

### Jupyter Notebook

```python
from src.models.train import rank_proteins

# Run protein ranking
results = rank_proteins(config_path="config.yaml")
```

## Class Reference

### `ProteinRankingIntegrator`

Main class orchestrating protein ranking.

**Initialization:**
```python
integrator = ProteinRankingIntegrator(
    results_dir=Path("results/"),
    explainability_csv=Path("ROSMAP_protein_attributions.csv"),
    graph_file=Path("ROSMAP_graph.graphml"),
    cohort="ROSMAP"
)
```

**Key Methods:**

- `compute_network_centrality()` - Degree, betweenness, closeness
- `normalize_values()` - Min-max normalization to [0, 1]
- `compute_composite_scores()` - Apply scoring formula
- `generate_ranking()` - Full ranking pipeline
- `map_proteins_to_genes()` - Add gene names
- `get_top_k_subgraph()` - Extract disease module
- `plot_disease_module()` - Network visualization
- `plot_top_20_table()` - Publication table
- `save_results()` - Output to files

## Analysis Outputs

### For Top 10 Proteins:
- Expected composite scores: 0.75-0.95
- GNN importance: 0.70-0.95
- Centrality: 0.65-0.90
- Stability: 80-100

### For Top 100 Proteins:
- Expected composite scores: 0.10-0.75
- Spread across all metric ranges
- Mix of high-confidence and supporting candidates

### For Full Ranking (5000 proteins):
- Median score: ~0.02-0.05
- Bottom quartile: close to 0
- Clear separation between top and mid-tier

## Biological Validation

### Cross-Cohort Consistency
Proteins appearing in top-20 across ≥2 cohorts:
- Strong biomarker candidates
- Less likely to be cohort-specific noise
- Good targets for independent validation

### Known AD Genes
Expected to see:
- APOE (top 5)
- APP (top 10)
- PSEN1/PSEN2 (top 20)
- MAPT (top 50)

### Network Hubs
High centrality proteins:
- Potential regulatory nodes
- Drug target candidates
- Pathway convergence points

## Performance and Scalability

**Computational Requirements (CPU):**
- Network analysis: 30-60 seconds per cohort
- Ranking generation: 5-10 seconds
- Visualization generation: 10-20 seconds
- **Total: ~1-2 minutes per cohort**

**GPU:** 5-10x faster

**Memory:**
- Graph storage: 10-50 MB per cohort
- DataFrame: 5-10 MB
- Figures: Generated on-the-fly

## Advanced Customization

### Modify Score Weights

```python
# Custom stability weight
def custom_stability_weight(freq):
    return (freq / 100) ** 0.5  # Square root instead of log

# Apply in compute_composite_scores()
stability_weights = {p: custom_stability_weight(freq) for p, freq in bootstrap_freq.items()}
```

### Different Centrality Measures

```python
# PageRank instead of combined measures
pagerank = nx.pagerank(graph)

# Eigenvector centrality
eigenvector = nx.eigenvector_centrality(graph)
```

### Weighted Network Analysis

```python
# Use edge weights (PPI confidence scores)
weighted_graph = graph.copy()
for u, v, data in weighted_graph.edges(data=True):
    weight = data.get('weight', 1.0)
    # Apply weight to centrality calculations
```

## Quality Checks

### Validation Criteria

1. **Score Distribution**
   - Mean composite score: 0.02-0.10
   - Std dev: 0.02-0.08
   - Top 10% > median + 2×std

2. **Ranking Consistency**
   - Top 20 should have high stability (freq > 80)
   - GNN and centrality should be correlated (r > 0.3)
   - No isolated high-score proteins without supporting evidence

3. **Network Quality**
   - Top 20 subgraph should be connected (single component)
   - Average degree > 5 for top proteins
   - High clustering coefficient (tight cliques)

## References

- Betweenness Centrality: Brandes, U. (2001). A faster algorithm for betweenness centrality.
- Closeness Centrality: Sabidussi, G. (1966). The centrality index of a graph.
- Gene Prioritization: Tiffin, N., et al. (2006). Computational disease gene identification.
