"""
Imputation methods for missing proteomics values.

Implements:
- MNAR (Missing Not At Random) minimum shift
- kNN imputation
"""

import numpy as np
import pandas as pd
from typing import Tuple


def shift_minimum_imputation(
    data: pd.DataFrame,
    shift_amount: float = 1.8,
) -> pd.DataFrame:
    """
    Minimum shift (MNAR) imputation.

    Replaces missing values with a value below the detected minimum,
    simulating the behavior of undetected proteins in mass spectrometry.

    Args:
        data: Expression matrix (genes x samples)
        shift_amount: How many standard deviations below minimum to impute

    Returns:
        Data with imputed values
    """
    data_imputed = data.copy()

    for col in data_imputed.columns:
        row_values = data_imputed[col].dropna()
        if len(row_values) > 0:
            min_val = row_values.min()
            std_val = row_values.std()
            # Impute with value below minimum
            impute_val = min_val - (shift_amount * std_val)
            data_imputed.loc[data_imputed[col].isna(), col] = impute_val

    return data_imputed


def knn_imputation(
    data: pd.DataFrame,
    n_neighbors: int = 5,
    metric: str = "euclidean",
) -> pd.DataFrame:
    """
    kNN imputation based on similar proteins/genes.

    Imputes missing values by taking the weighted average of
    k-nearest neighbors in expression space.

    Args:
        data: Expression matrix (genes x samples)
        n_neighbors: Number of neighbors to use
        metric: Distance metric ('euclidean', 'cosine')

    Returns:
        Data with imputed values
    """
    from sklearn.impute import KNNImputer

    # Use scikit-learn's KNNImputer
    imputer = KNNImputer(n_neighbors=min(n_neighbors, len(data) - 1), weights="distance")
    data_array = imputer.fit_transform(data)
    data_imputed = pd.DataFrame(data_array, index=data.index, columns=data.columns)

    return data_imputed


def iterative_imputation(
    data: pd.DataFrame,
    max_iter: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Iterative imputation using MICE (Multivariate Imputation by Chained Equations).

    More sophisticated method that models each feature with other features.

    Args:
        data: Expression matrix (genes x samples)
        max_iter: Maximum iterations
        random_state: Random seed

    Returns:
        Data with imputed values
    """
    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer

    imputer = IterativeImputer(
        max_iter=max_iter,
        random_state=random_state,
        verbose=0,
    )
    data_array = imputer.fit_transform(data)
    data_imputed = pd.DataFrame(data_array, index=data.index, columns=data.columns)

    return data_imputed


def compare_imputation_methods(
    data: pd.DataFrame,
    methods: list = None,
    random_state: int = 42,
) -> dict:
    """
    Compare different imputation methods.

    Args:
        data: Expression matrix
        methods: List of methods to try (['mnar', 'knn', 'iterative'])
        random_state: Random seed

    Returns:
        Dictionary with imputed data for each method
    """
    if methods is None:
        methods = ["mnar", "knn", "iterative"]

    np.random.seed(random_state)
    results = {}

    for method in methods:
        if method == "mnar":
            results[method] = shift_minimum_imputation(data)
        elif method == "knn":
            results[method] = knn_imputation(data)
        elif method == "iterative":
            results[method] = iterative_imputation(data, random_state=random_state)

    return results


def evaluate_imputation_quality(
    original: pd.DataFrame,
    imputed: pd.DataFrame,
    mask: pd.DataFrame,
) -> dict:
    """
    Evaluate imputation quality by comparing to held-out values.

    Args:
        original: Ground truth values
        imputed: Imputed values
        mask: Boolean mask of which values were imputed

    Returns:
        Dictionary with quality metrics
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    # Get imputed and true values at missing locations
    true_vals = original.values[mask]
    imputed_vals = imputed.values[mask]

    mae = mean_absolute_error(true_vals, imputed_vals)
    rmse = np.sqrt(mean_squared_error(true_vals, imputed_vals))
    r2 = 1 - (np.sum((true_vals - imputed_vals) ** 2) / np.sum((true_vals - true_vals.mean()) ** 2))

    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }
