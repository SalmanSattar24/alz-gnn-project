"""
Proteomics quality control and preprocessing pipeline.

Main module for processing proteomics expression matrices.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from src.preprocess.id_mapping import ProteinIDMapper
from src.preprocess.imputation import (
    shift_minimum_imputation,
    knn_imputation,
    iterative_imputation,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ProteomicsQC:
    """Quality control and preprocessing for proteomics data."""

    def __init__(self, random_state: int = 42):
        """
        Initialize QC pipeline.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        np.random.seed(random_state)
        self.mapper = ProteinIDMapper()
        self.qc_metrics = {}

    def load_proteomics_matrix(
        self,
        file_path: Path,
        index_col: int = 0,
    ) -> pd.DataFrame:
        """
        Load proteomics expression matrix.

        Args:
            file_path: Path to proteomics file (CSV or HDF5)
            index_col: Column index to use as index

        Returns:
            Expression matrix (proteins x samples)
        """
        logger.info(f"Loading proteomics data from {file_path}")

        if str(file_path).endswith(".h5ad"):
            import anndata
            adata = anndata.read_h5ad(file_path)
            return pd.DataFrame(
                adata.X,
                index=adata.obs_names,
                columns=adata.var_names,
            )
        elif str(file_path).endswith(".h5"):
            return pd.read_hdf(file_path, key="data")
        else:
            # Assume CSV/TSV
            return pd.read_csv(file_path, index_col=index_col, compression="gzip")

    def remove_missing_heavy_proteins(
        self,
        data: pd.DataFrame,
        missing_threshold: float = 0.30,
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Remove proteins with excessive missing values.

        Args:
            data: Expression matrix
            missing_threshold: Fraction of missing values to remove (default 30%)

        Returns:
            Filtered matrix and QC metrics
        """
        initial_proteins = len(data)

        # Calculate missing fraction per protein
        missing_fraction = data.isna().sum(axis=1) / data.shape[1]
        proteins_to_keep = missing_fraction <= missing_threshold

        data_filtered = data[proteins_to_keep].copy()
        proteins_removed = initial_proteins - len(data_filtered)

        metrics = {
            "initial_proteins": initial_proteins,
            "proteins_removed": proteins_removed,
            "proteins_kept": len(data_filtered),
            "removal_percent": 100 * proteins_removed / initial_proteins,
            "missing_threshold": missing_threshold,
        }

        logger.info(f"Protein filtering: {initial_proteins} -> {len(data_filtered)} " f"({metrics['removal_percent']:.1f}% removed)")

        return data_filtered, metrics

    def impute_missing_values(
        self,
        data: pd.DataFrame,
        method: str = "mnar",
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Impute missing values using specified method.

        Args:
            data: Expression matrix
            method: Imputation method ('mnar', 'knn', 'iterative')

        Returns:
            Imputed matrix and imputation statistics
        """
        initial_missing = data.isna().sum().sum()

        logger.info(f"Imputing missing values ({initial_missing} total) using {method}")

        if method == "mnar":
            data_imputed = shift_minimum_imputation(data)
        elif method == "knn":
            data_imputed = knn_imputation(data)
        elif method == "iterative":
            data_imputed = iterative_imputation(data, random_state=self.random_state)
        else:
            raise ValueError(f"Unknown imputation method: {method}")

        final_missing = data_imputed.isna().sum().sum()

        metrics = {
            "method": method,
            "initial_missing": initial_missing,
            "final_missing": final_missing,
            "imputed_values": initial_missing - final_missing,
        }

        logger.info(f"Imputation complete: {final_missing} values still missing")

        return data_imputed, metrics

    def log2_normalize(
        self,
        data: pd.DataFrame,
        pseudocount: float = 1.0,
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Log2 normalize abundance values.

        Args:
            data: Expression matrix (linear scale)
            pseudocount: Small value to add before log transform

        Returns:
            Log2-normalized matrix and normalization info
        """
        logger.info(f"Applying log2 normalization (pseudocount={pseudocount})")

        # Check if already log-transformed (values < 20)
        if data.values.max() > 20:
            data_normalized = np.log2(data + pseudocount)
            was_linear = True
        else:
            logger.warning("Data appears to already be log-transformed. Skipping.")
            data_normalized = data.copy()
            was_linear = False

        metrics = {
            "method": "log2",
            "pseudocount": pseudocount,
            "was_linear": was_linear,
            "original_mean": data.values.mean(),
            "normalized_mean": data_normalized.values.mean(),
        }

        return data_normalized, metrics

    def batch_correction(
        self,
        data: pd.DataFrame,
        batch_info: pd.DataFrame,
        method: str = "combat",
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Apply batch correction if batch information provided.

        Args:
            data: Expression matrix
            batch_info: DataFrame with batch information
            method: Batch correction method ('combat')

        Returns:
            Corrected matrix and correction info
        """
        if batch_info is None or len(batch_info) == 0:
            logger.info("No batch information provided. Skipping batch correction.")
            return data, {"applied": False}

        logger.info(f"Applying batch correction ({method})")

        if method == "combat":
            try:
                import scanpy as sc

                # Prepare batch vector
                batch_col = batch_info.get("batch", batch_info.iloc[:, 0])
                batch_vector = batch_col.values

                # Create AnnData object
                import anndata
                adata = anndata.AnnData(data.T)
                adata.obs["batch"] = batch_vector

                # Apply ComBat (modifies adata in-place)
                sc.pp.combat(adata, key="batch")

                data_corrected = pd.DataFrame(
                    adata.X.T,
                    index=data.index,
                    columns=data.columns,
                )

                n_batches = len(np.unique(batch_vector))
                metrics = {
                    "applied": True,
                    "method": "combat",
                    "batches": n_batches,
                }

                logger.info(f"Batch correction complete ({n_batches} batches)")

                return data_corrected, metrics

            except Exception as e:
                logger.warning(f"Batch correction failed: {e}. Returning uncorrected data.")
                return data, {"applied": False, "error": str(e)}
        else:
            raise ValueError(f"Unknown batch correction method: {method}")

    def preprocess_pipeline(
        self,
        data: pd.DataFrame,
        batch_info: Optional[pd.DataFrame] = None,
        missing_threshold: float = 0.30,
        impute_method: str = "mnar",
        apply_batch_correction: bool = False,
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Complete preprocessing pipeline.

        Steps:
        1. Remove proteins with excessive missing values
        2. Impute remaining missing values
        3. Log2 normalize
        4. Optional batch correction

        Args:
            data: Input expression matrix
            batch_info: Batch information (optional)
            missing_threshold: Max fraction of missing values per protein
            impute_method: Imputation method
            apply_batch_correction: Whether to apply batch correction

        Returns:
            Processed matrix and QC report
        """
        logger.info("=" * 60)
        logger.info("PROTEOMICS PREPROCESSING PIPELINE")
        logger.info("=" * 60)

        qc_report = {}

        # Step 1: Remove missing-heavy proteins
        data_qc, metrics = self.remove_missing_heavy_proteins(data, missing_threshold)
        qc_report["missing_filtering"] = metrics

        # Step 2: Impute missing values
        data_imputed, metrics = self.impute_missing_values(data_qc, method=impute_method)
        qc_report["imputation"] = metrics

        # Step 3: Log2 normalize
        data_normalized, metrics = self.log2_normalize(data_imputed)
        qc_report["normalization"] = metrics

        # Step 4: Optional batch correction
        if apply_batch_correction:
            data_processed, metrics = self.batch_correction(
                data_normalized,
                batch_info,
                method="combat",
            )
            qc_report["batch_correction"] = metrics
        else:
            data_processed = data_normalized

        logger.info("\n" + "=" * 60)
        logger.info("PREPROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Input: {data.shape} -> Output: {data_processed.shape}")

        return data_processed, qc_report

    def save_processed_data(
        self,
        data: pd.DataFrame,
        metadata: Optional[pd.DataFrame],
        output_path: Path,
    ) -> None:
        """
        Save processed data in AnnData HDF5 format.

        Args:
            data: Expression matrix (genes x samples)
            metadata: Sample metadata
            output_path: Output file path
        """
        try:
            import anndata
        except ImportError:
            logger.error("anndata not installed. Saving as CSV instead.")
            data.to_csv(output_path.with_suffix(".csv.gz"), compression="gzip")
            return

        logger.info(f"Saving processed data to {output_path}")

        # Create AnnData object
        adata = anndata.AnnData(
            X=data.T.values,  # Samples x genes
            obs=metadata if metadata is not None else pd.DataFrame(index=data.columns),
            var=pd.DataFrame(index=data.index),
        )

        # Add metadata
        adata.obs_names = data.columns
        adata.var_names = data.index

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(output_path)

        logger.info(f"Saved AnnData object: {adata.shape}")
