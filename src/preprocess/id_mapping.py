"""
Protein identifier mapping utilities.

Maps between different protein ID formats:
- Gene symbols (HUGO/HGNC)
- UniProt IDs
- Ensembl IDs
"""

import gzip
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd


class ProteinIDMapper:
    """Maps between different protein identifier formats."""

    def __init__(self):
        """Initialize mapper with empty indices (loaded on demand)."""
        self._symbol_to_uniprot: Dict[str, str] = {}
        self._uniprot_to_symbol: Dict[str, str] = {}
        self._symbol_to_ensembl: Dict[str, str] = {}
        self._ensembl_to_symbol: Dict[str, str] = {}
        self._uniprot_to_ensembl: Dict[str, str] = {}
        self._ensembl_to_uniprot: Dict[str, str] = {}
        self._loaded = False

    def build_mapping(
        self,
        protein_data: pd.DataFrame,
        symbol_col: str = "preferred_name",
        uniprot_col: Optional[str] = None,
        ensembl_col: Optional[str] = None,
    ) -> None:
        """
        Build mappings from protein annotation DataFrame.

        Args:
            protein_data: DataFrame with protein annotations
            symbol_col: Column name for gene symbols
            uniprot_col: Column name for UniProt IDs (optional)
            ensembl_col: Column name for Ensembl IDs (optional)
        """
        if symbol_col in protein_data.columns:
            for idx, row in protein_data.iterrows():
                symbol = str(row[symbol_col]).upper()

                if uniprot_col and uniprot_col in protein_data.columns:
                    uniprot = str(row[uniprot_col])
                    if not pd.isna(uniprot) and uniprot != "nan":
                        self._symbol_to_uniprot[symbol] = uniprot
                        self._uniprot_to_symbol[uniprot] = symbol

                if ensembl_col and ensembl_col in protein_data.columns:
                    ensembl = str(row[ensembl_col])
                    if not pd.isna(ensembl) and ensembl != "nan":
                        self._symbol_to_ensembl[symbol] = ensembl
                        self._ensembl_to_symbol[ensembl] = symbol

        self._loaded = True

    def symbol_to_uniprot(self, symbol: str) -> Optional[str]:
        """Convert gene symbol to UniProt ID."""
        return self._symbol_to_uniprot.get(symbol.upper())

    def uniprot_to_symbol(self, uniprot: str) -> Optional[str]:
        """Convert UniProt ID to gene symbol."""
        return self._uniprot_to_symbol.get(uniprot)

    def symbol_to_ensembl(self, symbol: str) -> Optional[str]:
        """Convert gene symbol to Ensembl ID."""
        return self._symbol_to_ensembl.get(symbol.upper())

    def ensembl_to_symbol(self, ensembl: str) -> Optional[str]:
        """Convert Ensembl ID to gene symbol."""
        return self._ensembl_to_symbol.get(ensembl)

    def map_protein_ids(
        self,
        proteins: List[str],
        from_format: str = "symbol",
        to_format: str = "uniprot",
        keep_unmapped: bool = False,
    ) -> Dict[str, Optional[str]]:
        """
        Map a list of protein IDs.

        Args:
            proteins: List of protein identifiers
            from_format: Source format ('symbol', 'uniprot', 'ensembl')
            to_format: Target format ('symbol', 'uniprot', 'ensembl')
            keep_unmapped: Whether to keep proteins with no mapping

        Returns:
            Dictionary mapping input to output IDs
        """
        mapping = {}

        for protein in proteins:
            if from_format == "symbol" and to_format == "uniprot":
                result = self._symbol_to_uniprot.get(protein.upper())
            elif from_format == "uniprot" and to_format == "symbol":
                result = self._uniprot_to_symbol.get(protein)
            elif from_format == "symbol" and to_format == "ensembl":
                result = self._symbol_to_ensembl.get(protein.upper())
            elif from_format == "ensembl" and to_format == "symbol":
                result = self._ensembl_to_symbol.get(protein)
            else:
                result = None

            if result is not None or keep_unmapped:
                mapping[protein] = result

        return mapping

    def get_mapped_count(self) -> Tuple[int, int, int]:
        """Get mapping statistics. Returns (symbol_to_uniprot, symbol_to_ensembl, uniprot_to_ensembl)."""
        return (
            len(self._symbol_to_uniprot),
            len(self._symbol_to_ensembl),
            len(self._uniprot_to_ensembl),
        )


def standardize_protein_names(proteins: List[str]) -> List[str]:
    """
    Standardize protein names to uppercase gene symbols.

    Args:
        proteins: Input protein identifiers

    Returns:
        Standardized names
    """
    standardized = []
    for p in proteins:
        # Remove common prefixes and suffixes
        p_clean = str(p).upper().strip()
        # Remove gene isoform info (e.g., "-1", "-2")
        p_clean = p_clean.split("-")[0]
        standardized.append(p_clean)
    return standardized


def filter_proteins_by_mapping(
    proteins: List[str],
    mapper: ProteinIDMapper,
    from_format: str = "symbol",
    to_format: str = "uniprot",
) -> Tuple[List[str], List[str]]:
    """
    Filter proteins to keep only those with valid mappings.

    Args:
        proteins: List of protein identifiers
        mapper: ProteinIDMapper instance
        from_format: Source format
        to_format: Target format

    Returns:
        Tuple of (kept_proteins, unmapped_proteins)
    """
    mapping = mapper.map_protein_ids(proteins, from_format, to_format, keep_unmapped=True)

    kept = [p for p, m in mapping.items() if m is not None]
    unmapped = [p for p, m in mapping.items() if m is None]

    return kept, unmapped
