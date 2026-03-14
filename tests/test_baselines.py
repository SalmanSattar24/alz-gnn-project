"""
Unit tests for baseline ML models.
"""

import json
import tempfile
from pathlib import Path

import anndata
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold

from src.models.baselines import (
    BaselineModelEvaluator,
    LogisticRegressionBaseline,
    MLPBaseline,
    RandomForestBaseline,
)


class TestBaselineModels:
    """Test baseline model implementations."""

    @pytest.fixture
    def sample_data(self):
        """Create sample proteomics matrix with labels."""
        np.random.seed(42)
        n_samples = 100
        n_features = 50

        # Create features
        X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f"PROT_{i}" for i in range(n_features)],
            index=[f"S_{i}" for i in range(n_samples)],
        )

        # Create labels (binary classification)
        y = np.array([1 if i % 2 == 0 else 0 for i in range(n_samples)])

        return X, y

    @pytest.fixture
    def train_val_test_split(self, sample_data):
        """Create train/val/test splits."""
        X, y = sample_data
        n = len(X)

        # Simple stratified split
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        train_val_idx, test_idx = next(skf.split(X, y))

        X_train_val = X.iloc[train_val_idx]
        X_test = X.iloc[test_idx]
        y_train_val = y[train_val_idx]
        y_test = y[test_idx]

        # Split train_val into train and val
        skf2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        train_idx, val_idx = next(skf2.split(X_train_val, y_train_val))

        X_train = X_train_val.iloc[train_idx]
        X_val = X_train_val.iloc[val_idx]
        y_train = y_train_val[train_idx]
        y_val = y_train_val[val_idx]

        return X_train, X_val, X_test, y_train, y_val, y_test

    def test_logistic_regression_initialization(self):
        """Test logistic regression model initialization."""
        model = LogisticRegressionBaseline(seed=42)
        assert model.model_name == "logistic_regression"
        assert model.seed == 42

    def test_random_forest_initialization(self):
        """Test random forest model initialization."""
        model = RandomForestBaseline(seed=42)
        assert model.model_name == "random_forest"
        assert model.seed == 42

    def test_mlp_initialization(self):
        """Test MLP model initialization."""
        model = MLPBaseline(seed=42)
        assert model.model_name == "mlp"
        assert model.seed == 42

    def test_logistic_regression_training(self, train_val_test_split):
        """Test logistic regression training."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = LogisticRegressionBaseline(seed=42)
        model.train(X_train, y_train)

        assert model.model is not None
        assert model.feature_importance is not None
        assert len(model.feature_importance) == X_train.shape[1]

    def test_random_forest_training(self, train_val_test_split):
        """Test random forest training."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = RandomForestBaseline(seed=42)
        model.train(X_train, y_train)

        assert model.model is not None
        assert model.feature_importance is not None
        assert len(model.feature_importance) == X_train.shape[1]

    def test_mlp_training(self, train_val_test_split):
        """Test MLP training."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = MLPBaseline(seed=42)
        model.train(X_train, y_train)

        assert model.model is not None
        assert model.feature_importance is not None
        assert len(model.feature_importance) == X_train.shape[1]

    def test_evaluation_metrics(self, train_val_test_split):
        """Test that evaluation returns valid metrics."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = LogisticRegressionBaseline(seed=42)
        model.train(X_train, y_train)

        metrics = model.evaluate(X_test, y_test)

        assert "auroc" in metrics
        assert "auprc" in metrics
        assert "accuracy" in metrics
        assert "f1" in metrics

        # Metrics should be in valid ranges
        for metric_name in ["auroc", "auprc", "accuracy", "f1"]:
            assert 0.0 <= metrics[metric_name] <= 1.0 or metrics[metric_name] == 0.5

    def test_prediction_shapes(self, train_val_test_split):
        """Test that predictions have correct shape."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = LogisticRegressionBaseline(seed=42)
        model.train(X_train, y_train)

        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        assert y_pred.shape == (len(X_test),)
        assert y_pred_proba.shape == (len(X_test),)

    def test_feature_importance_sorting(self, train_val_test_split):
        """Test that feature importance is sorted descending."""
        X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split
        model = RandomForestBaseline(seed=42)
        model.train(X_train, y_train)

        importances = model.feature_importance["importance"].values
        assert np.all(importances[:-1] >= importances[1:])


class TestBaselineModelEvaluator:
    """Test the evaluator class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory with mock data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create directories
            (tmpdir / "data" / "processed").mkdir(parents=True)
            (tmpdir / "results" / "models").mkdir(parents=True)

            # Create a mock AnnData file for ROSMAP
            n_samples = 50
            n_genes = 100

            # X should be (n_samples, n_genes)
            X = np.random.randn(n_samples, n_genes)
            var_names = [f"PROT_{i}" for i in range(n_genes)]
            obs_names = [f"S_{i}" for i in range(n_samples)]

            diagnosis = ["AD"] * 25 + ["Control"] * 25

            adata = anndata.AnnData(
                X=X,
                obs=pd.DataFrame({"diagnosis": diagnosis}, index=obs_names),
                var=pd.DataFrame(index=var_names),
            )

            adata.write_h5ad(tmpdir / "data" / "processed" / "ROSMAP_processed.h5ad")

            # Create minimal config
            config = {
                "data": {"processed_dir": str(tmpdir / "data" / "processed")},
                "logging": {"checkpoint_dir": str(tmpdir / "results" / "models")},
                "validation": {"cv_folds": 3},
                "debug": {"seed": 42},
            }

            config_path = tmpdir / "config.yaml"
            import yaml

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            yield tmpdir, str(config_path)

    def test_evaluator_initialization(self, temp_config_dir):
        """Test evaluator initialization."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        assert evaluator.config is not None
        assert evaluator.seed == 42
        assert evaluator.cv_folds == 3

    def test_stratified_split(self, temp_config_dir):
        """Test stratified splitting maintains class balance."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        X = pd.DataFrame(np.random.randn(100, 50))
        y = np.array([1] * 50 + [0] * 50)

        X_train, X_val, X_test, y_train, y_val, y_test = evaluator._stratified_split(X, y)

        # Check that no overlap between splits
        assert len(X_train) + len(X_val) + len(X_test) == len(X)

        # Check class balance
        class_ratio_train = np.sum(y_train) / len(y_train)
        assert 0.4 < class_ratio_train < 0.6  # Should be close to 0.5

    def test_cross_validation(self, temp_config_dir):
        """Test cross-validation execution."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        X = pd.DataFrame(np.random.randn(100, 50))
        y = np.array([1] * 50 + [0] * 50)

        cv_metrics = evaluator.cross_validate(LogisticRegressionBaseline, X, y)

        assert "mean_auroc" in cv_metrics
        assert "std_auroc" in cv_metrics
        assert "mean_accuracy" in cv_metrics
        assert "std_accuracy" in cv_metrics

    def test_load_cohort_data(self, temp_config_dir):
        """Test loading cohort data."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        X, y = evaluator._load_cohort_data("ROSMAP")

        assert X is not None
        assert y is not None
        assert X.shape[0] == 50
        assert len(y) == 50
        assert np.sum(y) == 25  # 25 AD cases

    def test_train_all_models(self, temp_config_dir):
        """Test training all models."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        results = evaluator.train_all_models(cohorts=["ROSMAP"])

        assert "ROSMAP" in results
        assert "logistic_regression" in results["ROSMAP"]
        assert "random_forest" in results["ROSMAP"]
        assert "mlp" in results["ROSMAP"]

        for model_name in ["logistic_regression", "random_forest", "mlp"]:
            assert "test_metrics" in results["ROSMAP"][model_name]
            assert "cv_metrics" in results["ROSMAP"][model_name]

    def test_results_saved_to_json(self, temp_config_dir):
        """Test that results are saved to JSON."""
        tmpdir, config_path = temp_config_dir
        evaluator = BaselineModelEvaluator(config_path)

        evaluator.train_all_models(cohorts=["ROSMAP"])

        json_path = evaluator.results_dir / "baseline_metrics.json"
        assert json_path.exists()

        with open(json_path) as f:
            data = json.load(f)

        assert "ROSMAP" in data
        assert "logistic_regression" in data["ROSMAP"]


class TestDataNormalization:
    """Test feature normalization."""

    def test_normalization_scaling(self):
        """Test that normalization properly scales features."""
        from sklearn.preprocessing import StandardScaler

        X_train = pd.DataFrame(np.random.randn(100, 10) * 10 + 50)
        X_test = pd.DataFrame(np.random.randn(50, 10) * 10 + 50)

        model = LogisticRegressionBaseline()

        X_train_norm, X_test_norm, _ = model._normalize_features(X_train, X_test, X_test)

        # Mean should be ~0 and std should be ~1 after normalization
        assert np.abs(X_train_norm.values.mean()) < 0.1
        assert np.abs(X_train_norm.values.std() - 1.0) < 0.1

    def test_normalization_fit_on_train_only(self):
        """Test that normalization is fit only on training data."""
        X_train = pd.DataFrame(np.full((100, 10), 0.0))
        X_test = pd.DataFrame(np.full((50, 10), 1.0))

        model = LogisticRegressionBaseline()
        X_train_norm, X_test_norm, _ = model._normalize_features(X_train, X_test, X_test)

        # After normalizing with train zeros as baseline, test ones should be ~1/std
        assert np.all(X_test_norm.values > 0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
