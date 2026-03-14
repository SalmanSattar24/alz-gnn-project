# Proteomics-Driven Graph Neural Networks for Alzheimer's Protein Prioritization

A comprehensive research framework for analyzing and modeling Alzheimer's disease proteomics using Graph Neural Networks (GNNs) with explainability and stability analysis.

## Overview

This project implements state-of-the-art Graph Neural Networks to investigate protein interaction networks and biomarkers in Alzheimer's disease. The framework integrates proteomics data with protein-protein interaction networks to enable:

- **Data-Driven Discovery**: Identify key proteins and interactions associated with Alzheimer's pathology
- **Predictive Modeling**: Train GNN models for protein prioritization and biomarker prediction
- **Interpretability**: Explain model predictions using SHAP and CAPTUM
- **Robustness Analysis**: Evaluate model stability and generalization across patient cohorts

## Project Structure

```
alz-gnn-project/
├── data/                      # Data storage
│   ├── raw/                   # Downloaded raw datasets
│   └── processed/             # Preprocessed and graph-ready data
├── src/
│   ├── download/              # Data acquisition modules (Synapse, etc.)
│   ├── preprocess/            # Data cleaning and normalization pipelines
│   ├── graphs/                # Graph construction and utilities
│   ├── models/                # GNN model definitions and training
│   ├── explain/               # Model interpretability (SHAP, CAPTUM)
│   ├── analysis/              # Stability and robustness analysis
│   └── utils/                 # Common utilities and helpers
├── notebooks/                 # Jupyter notebooks for exploration
├── results/                   # Model outputs, plots, and reports
├── tests/                     # Unit and integration tests
├── config.yaml                # Project configuration
├── environment.yml            # Conda environment specification
├── requirements.txt           # Pip requirements (alternative)
├── Makefile                   # Pipeline automation
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Conda (Anaconda or Miniconda)
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/alz-gnn-project.git
   cd alz-gnn-project
   ```

2. **Create conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate alz-gnn
   ```

3. **Verify installation:**
   ```bash
   python -c "import torch; import torch_geometric; print('✓ All imports successful')"
   ```

## Quick Pipeline Usage

The project uses a Makefile for easy pipeline execution:

```bash
# Download data from Synapse
make download

# Preprocess and normalize data
make preprocess

# Construct protein interaction graphs
make graph

# Train GNN models
make train

# Generate model explanations
make explain

# Run stability and robustness analysis
make stability

# Generate comprehensive report
make report
```

## Detailed Usage

### 1. Data Download

Download proteomics and network data:

```python
python src/download/download_data.py --config config.yaml
```

### 2. Data Preprocessing

Clean, normalize, and format data for model training:

```python
python src/preprocess/preprocess.py --config config.yaml
```

### 3. Graph Construction

Build protein-protein interaction graphs:

```python
python src/graphs/build_graphs.py --config config.yaml
```

### 4. Model Training

Train GNN models:

```python
python src/models/train.py --config config.yaml
```

### 5. Explainability Analysis

Generate SHAP and CAPTUM explanations:

```python
python src/explain/explain_model.py --config config.yaml
```

### 6. Stability Analysis

Evaluate model robustness:

```python
python src/analysis/stability_analysis.py --config config.yaml
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| **PyTorch** | Deep learning framework |
| **PyTorch Geometric** | Graph neural networks |
| **Pandas/NumPy** | Data manipulation |
| **Scikit-learn** | ML utilities and preprocessing |
| **NetworkX** | Graph analysis |
| **CAPTUM** | Model interpretability |
| **SHAP** | Shapley-based explanations |
| **Optuna** | Hyperparameter optimization |
| **AnnData/Scanpy** | Single-cell/omics data handling |
| **SynapseClient** | Synapse data access |
| **Seaborn/Matplotlib** | Visualization |

## Configuration

Edit `config.yaml` to customize:

```yaml
# data
data:
  raw_dir: data/raw
  processed_dir: data/processed
  synapse_project_id: null

# preprocessing
preprocess:
  normalization: "z-score"
  batch_correction: true

# graph construction
graph:
  ppi_source: "string"
  edge_threshold: 0.4

# model training
training:
  model: "GCN"
  hidden_dims: [128, 64]
  epochs: 100
  batch_size: 32

# explainability
explain:
  method: "shap"
  num_samples: 100
```

## Testing

Run the test suite:

```bash
pytest tests/ -v --cov=src
```

## Notebooks

Explore analysis workflows in `notebooks/`:

- `01_data_exploration.ipynb`: Data overview and statistics
- `02_graph_analysis.ipynb`: Network topology analysis
- `03_model_training.ipynb`: Training and validation curves
- `04_explainability.ipynb`: SHAP and CAPTUM visualizations
- `05_stability_analysis.ipynb`: Robustness evaluation

## Code Quality

Ensure code quality before committing:

```bash
# Format code
black src/ tests/ notebooks/

# Lint
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports

# Run tests
pytest tests/
```

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Follow project conventions (see code style above)
3. Write tests for new functionality
4. Commit with descriptive messages
5. Push and open a pull request

## Results and Outputs

- `results/models/`: Trained model checkpoints
- `results/figures/`: Publication-quality plots
- `results/explanations/`: SHAP and CAPTUM outputs
- `results/stability/`: Robustness analysis results
- `results/report.pdf`: Comprehensive analysis report

## Troubleshooting

### GPU Issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Force CPU mode
export CUDA_VISIBLE_DEVICES=""
```

### Memory Issues
Reduce batch size in `config.yaml` or process in smaller chunks.

### Import Errors
Reinstall dependencies:
```bash
conda env remove -n alz-gnn
conda env create -f environment.yml
```

## Citation

If you use this project in your research, please cite:

```bibtex
@software{proteomics_gnn_2026,
  title={Proteomics-Driven Graph Neural Networks for Alzheimer's Protein Prioritization},
  author={Your Name and Contributors},
  year={2026},
  url={https://github.com/yourusername/alz-gnn-project},
  doi={}
}
```

## License

MIT License - see LICENSE file for details

## Contact

For questions, issues, or collaboration:
- Open an issue on GitHub
- Contact the maintainers

## Acknowledgments

- Data sourced from [Synapse](https://www.synapse.org)
- Protein interaction networks from [STRING](https://string-db.org)
- Inspired by recent GNN+proteomics research
