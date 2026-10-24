# Alzheimer's Protein-Network Research

A notebook-centered research framework for proteomics preprocessing, protein-interaction graphs, GNN experiments, explanation and stability analysis.

**Research prototype—not a clinical predictor or validated drug-discovery system.** Mock-data and real-data pathways coexist; always identify which produced a result. Start with [the employer guide](docs/EMPLOYER_GUIDE.md).

## What is actually in the repository?

| Component | Where to look |
|---|---|
| Configuration and data-access utilities | [config.yaml](config.yaml), [src/config.py](src/config.py), [src/download/](src/download/) |
| Quality control and imputation | [src/preprocess/](src/preprocess/) |
| Network construction | [src/graphs/graph_utils.py](src/graphs/graph_utils.py), [build_graphs.ipynb](src/graphs/build_graphs.ipynb) |
| Baselines and graph-model notebooks | [src/models/](src/models/) |
| Explanation and stability | [src/explain/](src/explain/), [src/analysis/](src/analysis/) |
| Notebook orchestration | [execute_pipeline.py](execute_pipeline.py), [execute_pipeline_direct.py](execute_pipeline_direct.py) |
| Python and notebook test material | [tests/](tests/) |

## Setup and inspection

```bash
git clone https://github.com/SalmanSattar24/alz-gnn-project.git
cd alz-gnn-project
conda env create -f environment.yml
conda activate alz-gnn
```

Review `config.yaml` and the individual notebooks before execution. Synapse/ROSMAP access is permission-controlled; configure your own permitted inputs and keep credentials out of version control.

**Important reproducibility caveat:** several Makefile targets reference `.py` entry points whose checked-in implementations are notebooks instead. Do not treat `make all` or the old README as a verified one-command replay. Likewise, `execute_pipeline.py` passes `use_mock=True`, while the checked-in config declares `data.use_mock: false`; inspect the notebook/config behavior rather than assuming the runner argument guarantees synthetic-only execution.

## Intended workflow

```text
Authorized proteomics + interaction network
  -> preprocessing / ID mapping
  -> graph construction
  -> baseline and GNN experiments
  -> explanations
  -> stability analysis and candidate ranking
```

Explanation scores and network rankings are exploratory, not proof of biological mechanism or intervention efficacy.

## Validation and limitations

The repository includes test/configuration utilities and notebook test material. This documentation pass did not execute downloads, notebook pipelines, model training or a fresh test suite. Generated graphs and sample files already in the repository should not be mistaken for independent external validation.

Some paths, environment assumptions and orchestrators need reconciliation before full replay. That limitation is documented rather than hidden behind a production-ready label.

## Related work and history

[ad_gnn_pipeline](https://github.com/SalmanSattar24/ad_gnn_pipeline) is another staged research implementation, not an independent validation cohort. The [previous README](docs/README_LEGACY.md) is retained as a historical reference; its executable instructions may be stale.

Use this project as a portfolio example of research workflow design, graph-based modeling and scientific debugging. No clinical or treatment use is intended.
