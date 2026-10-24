# Employer guide

## What to evaluate

This repository explores the interface between tabular proteomics, interaction networks and graph-based ML. Its useful engineering story is the separation of data acquisition, ID mapping, graph construction, model experiments and stability reporting.

## Reading path

1. `src/config.py` and `config.yaml`: configuration and mock/real input choices.
2. `src/preprocess/proteomics_qc.py` and `imputation.py`: preprocessing.
3. `src/graphs/graph_utils.py`: graph representation.
4. `src/models/gnn_model.ipynb` and `baselines.ipynb`: model experiments.
5. `src/analysis/stability_analysis.py`: robustness analysis.
6. `execute_pipeline.py`: orchestration and error reporting.

## Reproducibility review

The Makefile advertises several Python scripts that are not present under those names; the implemented stages are often notebooks. A runner parameter also disagrees with the checked-in mock-data config. These are current integration limitations, not capabilities added by the documentation refresh.

## Appropriate claims

Describe exploratory graph-modeling infrastructure and explanation/stability workflows. Do not claim causal target discovery, independent patient-level validation, or a working one-command pipeline without separately demonstrating it. Data access and third-party licensing remain independent requirements.
