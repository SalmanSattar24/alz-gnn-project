"""
Unit tests for preprocessing pipeline.
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.preprocess.proteomics_qc import ProteomicsQC
from src.preprocess.id_mapping import ProteinIDMapper, standardize_protein_names
from src.preprocess.imputation import (
    shift_minimum_imputation,
    knn_imputation,
)


class TestProteomicsQC:
    """Test ProteomicsQC preprocessing."""

    @pytest.fixture
    def sample_data(self):
        """Create sample proteomics matrix."""
        np.random.seed(42)
        proteins = [f"PROT_{i}" for i in range(100)]
        samples = [f"S_{i}" for i in range(50)]
        data = pd.DataFrame(
            np.random.lognormal(mean=5, sigma=2, size=(100, 50)),
            index=proteins,
            columns=samples,
        )
        # Add some missing values
        mask = np.random.random((100, 50)) < 0.1
        data[mask] = np.nan
        return data

    @pytest.fixture
    def qc_pipeline(self):
        """Create QC pipeline instance."""
        return ProteomicsQC(random_state=42)

    def test_initialization(self, qc_pipeline):
        """Test pipeline initialization."""
        assert qc_pipeline.random_state == 42
        assert qc_pipeline.mapper is not None

    def test_missing_value_filtering(self, sample_data, qc_pipeline):
        """Test removal of proteins with excessive missing values."""
        initial_count = len(sample_data)

        # Add one protein with 50% missing
        sample_data.loc["HIGH_MISSING"] = np.nan
        sample_data.loc["HIGH_MISSING", :25] = 5.0

        # Filter with 30% threshold
        filtered, metrics = qc_pipeline.remove_missing_heavy_proteins(
            sample_data,
            missing_threshold=0.30,
        )

        # Check that protein was removed
        assert "HIGH_MISSING" not in filtered.index
        assert len(filtered) < len(sample_data)
        assert metrics["proteins_removed"] >= 1

    def test_imputation_mnar(self, sample_data, qc_pipeline):
        """Test MNAR imputation."""
        data_imputed, metrics = qc_pipeline.impute_missing_values(
            sample_data,
            method="mnar",
        )

        # Check no missing values remain
        assert data_imputed.isna().sum().sum() == 0
        assert metrics["method"] == "mnar"
        assert metrics["imputed_values"] > 0

    def test_imputation_knn(self, sample_data, qc_pipeline):
        """Test kNN imputation."""
        data_imputed, metrics = qc_pipeline.impute_missing_values(
            sample_data,
            method="knn",
        )

        # Check no missing values remain
        assert data_imputed.isna().sum().sum() == 0
        assert metrics["method"] == "knn"

    def test_log2_normalization(self, sample_data, qc_pipeline):
        """Test log2 normalization."""
        normalized, metrics = qc_pipeline.log2_normalize(sample_data)

        # Check that values are log-scale
        assert normalized.values.max() < sample_data.values.max()
        assert metrics["was_linear"] is True
        assert metrics["method"] == "log2"

    def test_full_pipeline(self, sample_data, qc_pipeline):
        """Test complete preprocessing pipeline."""
        processed, qc_report = qc_pipeline.preprocess_pipeline(
            sample_data,
            missing_threshold=0.30,
            impute_method="mnar",
        )

        # Check no missing values
        assert processed.isna().sum().sum() == 0
        # Check data dimensions match
        assert processed.shape[1] == sample_data.shape[1]
        # Check QC report
        assert "missing_filtering" in qc_report
        assert "imputation" in qc_report
        assert "normalization" in qc_report

    def test_reproducibility(self, sample_data):
        """Test that preprocessing is reproducible with fixed seed."""
        qc1 = ProteomicsQC(random_state=42)
        qc2 = ProteomicsQC(random_state=42)

        data1, _ = qc1.preprocess_pipeline(sample_data.copy(), impute_method="mnar")
        data2, _ = qc2.preprocess_pipeline(sample_data.copy(), impute_method="mnar")

        # Results should be identical
        pd.testing.assert_frame_equal(data1, data2)


class TestIDMapping:
    """Test protein ID mapping."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with test data."""
        mapper = ProteinIDMapper()

        # Create test annotation data
        annotations = pd.DataFrame({
            "preferred_name": ["TP53", "BRCA1", "EGFR", "MYC"],
            "uniprot_id": ["P04637", "P38398", "P00533", "P01106"],
            "ensembl_id": ["ENSG00000141510", "ENSG00000012048", "ENSG00000005468", "ENSG00000136997"],
        })

        mapper.build_mapping(
            annotations,
            symbol_col="preferred_name",
            uniprot_col="uniprot_id",
            ensembl_col="ensembl_id",
        )

        return mapper

    def test_symbol_to_uniprot(self, mapper):
        """Test gene symbol to UniProt mapping."""
        uniprot = mapper.symbol_to_uniprot.get("TP53".upper())
        assert uniprot == "P04637"

    def test_uniprot_to_symbol(self, mapper):
        """Test UniProt to gene symbol mapping."""
        symbol = mapper.uniprot_to_symbol.get("P04637")
        assert symbol == "TP53"

    def test_symbol_to_ensembl(self, mapper):
        """Test gene symbol to Ensembl mapping."""
        ensembl = mapper.symbol_to_ensembl.get("EGFR".upper())
        assert ensembl == "ENSG00000005468"

    def test_mapping_statistics(self, mapper):
        """Test mapping statistics."""
        counts = mapper.get_mapped_count()
        assert counts[0] > 0  # symbol_to_uniprot
        assert counts[1] > 0  # symbol_to_ensembl


class TestImputation:
    """Test imputation methods."""

    @pytest.fixture
    def data_with_missing(self):
        """Create data with missing values."""
        np.random.seed(42)
        data = pd.DataFrame(
            np.random.randn(50, 20),
            index=[f"P{i}" for i in range(50)],
            columns=[f"S{i}" for i in range(20)],
        )
        # Add missing values
        mask = np.random.random((50, 20)) < 0.2
        data[mask] = np.nan
        return data

    def test_mnar_imputation(self, data_with_missing):
        """Test MNAR imputation produces no missing values."""
        imputed = shift_minimum_imputation(data_with_missing)
        assert imputed.isna().sum().sum() == 0

    def test_knn_imputation(self, data_with_missing):
        """Test kNN imputation produces reasonable values."""
        imputed = knn_imputation(data_with_missing, n_neighbors=3)
        assert imputed.isna().sum().sum() == 0
        # Check that imputed values are in reasonable range
        assert imputed.values.min() > data_with_missing.values.min() - 2
        assert imputed.values.max() < data_with_missing.values.max() + 2

    def test_imputation_preserves_shape(self, data_with_missing):
        """Test that imputation preserves data dimensions."""
        imputed_mnar = shift_minimum_imputation(data_with_missing)
        imputed_knn = knn_imputation(data_with_missing)

        assert imputed_mnar.shape == data_with_missing.shape
        assert imputed_knn.shape == data_with_missing.shape


class TestStandardization:
    """Test protein name standardization."""

    def test_standardize_to_uppercase(self):
        """Test standardization to uppercase."""
        proteins = ["tp53", "BRCA1", "EgfR"]
        standardized = standardize_protein_names(proteins)
        assert all(p.isupper() for p in standardized)

    def test_remove_isoform_suffix(self):
        """Test removal of isoform suffixes."""
        proteins = ["TP53-1", "BRCA1-2", "EGFR"]
        standardized = standardize_protein_names(proteins)
        assert "TP53-1" not in standardized
        assert "TP53" in standardized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
