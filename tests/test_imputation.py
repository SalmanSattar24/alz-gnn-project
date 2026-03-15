"""Tests for src/preprocess/imputation.py."""

import numpy as np
import pandas as pd
import pytest

from src.preprocess.imputation import (
    compare_imputation_methods,
    evaluate_imputation_quality,
    knn_imputation,
    shift_minimum_imputation,
)


@pytest.fixture
def clean_matrix():
    """4×5 DataFrame with no missing values."""
    np.random.seed(42)
    return pd.DataFrame(
        np.random.randn(4, 5),
        columns=[f"S{i}" for i in range(5)],
    )


@pytest.fixture
def matrix_with_nans(clean_matrix):
    """Same matrix with 20% of values set to NaN."""
    df = clean_matrix.copy()
    df.iloc[0, 0] = np.nan
    df.iloc[1, 2] = np.nan
    df.iloc[3, 4] = np.nan
    return df


# ---------------------------------------------------------------------------
# shift_minimum_imputation
# ---------------------------------------------------------------------------

def test_shift_minimum_no_nans_after(matrix_with_nans):
    """All NaNs are filled after shift_minimum_imputation."""
    result = shift_minimum_imputation(matrix_with_nans)
    assert not result.isna().any().any()


def test_shift_minimum_non_nan_unchanged(matrix_with_nans):
    """Non-NaN values are not modified."""
    original = matrix_with_nans.copy()
    result = shift_minimum_imputation(matrix_with_nans)

    mask = ~original.isna()
    pd.testing.assert_frame_equal(result[mask], original[mask])


def test_shift_minimum_imputed_below_min(matrix_with_nans):
    """Imputed values are below the observed minimum for each column."""
    result = shift_minimum_imputation(matrix_with_nans)
    original = matrix_with_nans

    for col in original.columns:
        observed_min = original[col].dropna().min()
        nan_mask = original[col].isna()
        if nan_mask.any():
            assert (result.loc[nan_mask, col] < observed_min).all()


def test_shift_minimum_no_op_on_complete_data(clean_matrix):
    """shift_minimum_imputation is a no-op when there are no NaNs."""
    result = shift_minimum_imputation(clean_matrix)
    pd.testing.assert_frame_equal(result, clean_matrix)


# ---------------------------------------------------------------------------
# knn_imputation
# ---------------------------------------------------------------------------

def test_knn_no_nans_after(matrix_with_nans):
    """All NaNs are filled after knn_imputation."""
    result = knn_imputation(matrix_with_nans, n_neighbors=2)
    assert not result.isna().any().any()


def test_knn_preserves_shape(matrix_with_nans):
    """Output shape matches input shape."""
    result = knn_imputation(matrix_with_nans, n_neighbors=2)
    assert result.shape == matrix_with_nans.shape


def test_knn_preserves_columns(matrix_with_nans):
    """Output columns match input columns."""
    result = knn_imputation(matrix_with_nans, n_neighbors=2)
    assert list(result.columns) == list(matrix_with_nans.columns)


# ---------------------------------------------------------------------------
# compare_imputation_methods
# ---------------------------------------------------------------------------

def test_compare_returns_all_methods(matrix_with_nans):
    """compare_imputation_methods returns a result for every requested method."""
    results = compare_imputation_methods(matrix_with_nans, methods=["mnar", "knn"])
    assert set(results.keys()) == {"mnar", "knn"}


def test_compare_all_results_complete(matrix_with_nans):
    """Each result from compare_imputation_methods has no NaNs."""
    results = compare_imputation_methods(matrix_with_nans, methods=["mnar", "knn"])
    for method, df in results.items():
        assert not df.isna().any().any(), f"NaNs found in method '{method}'"


# ---------------------------------------------------------------------------
# evaluate_imputation_quality
# ---------------------------------------------------------------------------

def test_evaluate_returns_required_keys(clean_matrix):
    """evaluate_imputation_quality returns mae, rmse, r2."""
    np.random.seed(0)
    mask = pd.DataFrame(False, index=clean_matrix.index, columns=clean_matrix.columns)
    mask.iloc[0, 0] = True
    mask.iloc[1, 1] = True

    # Slightly perturbed version as "imputed"
    imputed = clean_matrix + np.random.randn(*clean_matrix.shape) * 0.01

    metrics = evaluate_imputation_quality(clean_matrix, imputed, mask.values)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics


def test_evaluate_perfect_imputation(clean_matrix):
    """Perfect imputation gives mae=0 and r2=1."""
    mask = pd.DataFrame(False, index=clean_matrix.index, columns=clean_matrix.columns)
    mask.iloc[0, 0] = True
    mask.iloc[2, 3] = True

    metrics = evaluate_imputation_quality(clean_matrix, clean_matrix.copy(), mask.values)
    assert metrics["mae"] == pytest.approx(0.0, abs=1e-10)
    assert metrics["r2"] == pytest.approx(1.0, abs=1e-10)
