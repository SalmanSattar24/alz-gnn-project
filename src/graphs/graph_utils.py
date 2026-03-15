"""
Graph utilities for building and analyzing protein interaction networks.
"""

import gzip
from pathlib import Path
from typing import Dict, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_string_ppi(
    string_file: Path,
    score_threshold: int = 700,
) -> pd.DataFrame:
    """
    Load STRING protein interaction network.

    Args:
        string_file: Path to STRING interactions file (protein.links.v11.5.txt.gz)
        score_threshold: Minimum combined score (0-1000)

    Returns:
        DataFrame with columns: protein1, protein2, combined_score
    """
    logger.info(f"Loading STRING PPI from {string_file}")

    if not string_file.exists():
        logger.error(f"STRING file not found: {string_file}")
        return pd.DataFrame()

    try:
        # Read gzipped file
        interactions = []
        with gzip.open(string_file, "rt") as f:
            header = next(f)  # Skip header
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    protein1 = parts[0]
                    protein2 = parts[1]
                    score = int(parts[2])

                    if score >= score_threshold:
                        interactions.append({
                            "protein1": protein1,
                            "protein2": protein2,
                            "combined_score": score,
                        })

        df = pd.DataFrame(interactions)
        logger.info(f"Loaded {len(df)} STRING interactions (score >= {score_threshold})")
        return df

    except Exception as e:
        logger.error(f"Failed to load STRING file: {e}")
        return pd.DataFrame()


def compute_coabundance_edges(
    data: pd.DataFrame,
    rho_threshold: float = 0.5,
    pvalue_threshold: float = 0.05,
) -> pd.DataFrame:
    """
    Compute co-abundance edges from proteomics data.

    Uses Spearman correlation with FDR correction.

    Args:
        data: Expression matrix (proteins x samples)
        rho_threshold: Minimum correlation coefficient (absolute value)
        pvalue_threshold: Maximum p-value (before FDR correction)

    Returns:
        DataFrame with columns: protein1, protein2, rho, pvalue
    """
    logger.info(f"Computing co-abundance edges (|rho| > {rho_threshold}, p < {pvalue_threshold})")

    proteins = data.index.tolist()
    edges = []

    # Compute pairwise correlations
    n_proteins = len(proteins)
    for i, p1 in enumerate(proteins):
        if i % 500 == 0:
            logger.info(f"  Processing protein {i}/{n_proteins}")

        for j, p2 in enumerate(proteins):
            if i >= j:  # Only compute upper triangle
                continue

            # Spearman correlation
            rho, pvalue = spearmanr(data.loc[p1], data.loc[p2])

            # Filter by thresholds
            if abs(rho) >= rho_threshold and pvalue < pvalue_threshold:
                edges.append({
                    "protein1": p1,
                    "protein2": p2,
                    "rho": rho,
                    "pvalue": pvalue,
                })

    df = pd.DataFrame(edges)
    logger.info(f"Found {len(df)} co-abundance edges")
    return df


def map_proteins_to_ids(
    proteins: pd.Index,
    ppi_df: pd.DataFrame,
) -> Tuple[Set[str], Dict[str, str]]:
    """
    Map protein IDs between different formats.

    Args:
        proteins: Protein identifiers from data
        ppi_df: PPI dataframe with protein IDs

    Returns:
        Tuple of (proteins_in_ppi, protein_mapping)
    """
    logger.info(f"Mapping {len(proteins)} proteins to PPI network")

    # Extract unique proteins from PPI
    ppi_proteins = set(ppi_df["protein1"].tolist() + ppi_df["protein2"].tolist())

    # Find proteins in both datasets
    # For now, use exact matching (can be improved with ID mapping)
    proteins_in_ppi = set(proteins) & ppi_proteins

    # Create mapping (identity mapping for now)
    mapping = {p: p for p in proteins_in_ppi}

    logger.info(f"Mapped {len(proteins_in_ppi)} / {len(proteins)} proteins to PPI")

    return proteins_in_ppi, mapping


def create_network(
    ppi_edges: pd.DataFrame,
    coab_edges: pd.DataFrame = None,
    proteins: Set[str] = None,
) -> nx.Graph:
    """
    Create networkx graph from edges.

    Args:
        ppi_edges: PPI edges (protein1, protein2, combined_score)
        coab_edges: Co-abundance edges (protein1, protein2, rho, pvalue)
        proteins: Set of valid proteins (filters nodes)

    Returns:
        NetworkX graph
    """
    G = nx.Graph()

    # Add nodes
    if proteins:
        G.add_nodes_from(proteins)
        logger.info(f"Added {len(proteins)} nodes")
    else:
        # Add all proteins from edges
        nodes = set()
        if not ppi_edges.empty:
            nodes.update(ppi_edges["protein1"].tolist())
            nodes.update(ppi_edges["protein2"].tolist())
        if coab_edges is not None and not coab_edges.empty:
            nodes.update(coab_edges["protein1"].tolist())
            nodes.update(coab_edges["protein2"].tolist())
        G.add_nodes_from(nodes)
        logger.info(f"Added {len(nodes)} nodes")

    # Add PPI edges
    if not ppi_edges.empty:
        ppi_edge_list = [
            (row["protein1"], row["protein2"], {
                "type": "ppi",
                "weight": row["combined_score"] / 1000.0,  # Normalize to 0-1
                "score": row["combined_score"],
            })
            for _, row in ppi_edges.iterrows()
            if proteins is None or (row["protein1"] in proteins and row["protein2"] in proteins)
        ]
        G.add_edges_from(ppi_edge_list)
        logger.info(f"Added {len(ppi_edge_list)} PPI edges")

    # Add co-abundance edges
    if coab_edges is not None and not coab_edges.empty:
        coab_edge_list = [
            (row["protein1"], row["protein2"], {
                "type": "coab",
                "weight": abs(row["rho"]),  # Use absolute correlation as weight
                "rho": row["rho"],
                "pvalue": row["pvalue"],
            })
            for _, row in coab_edges.iterrows()
            if proteins is None or (row["protein1"] in proteins and row["protein2"] in proteins)
        ]
        G.add_edges_from(coab_edge_list)
        logger.info(f"Added {len(coab_edge_list)} co-abundance edges")

    return G


def compute_centrality_metrics(G: nx.Graph) -> pd.DataFrame:
    """
    Compute node centrality metrics.

    Args:
        G: NetworkX graph

    Returns:
        DataFrame with centrality metrics
    """
    logger.info("Computing centrality metrics")

    metrics = {
        "protein": list(G.nodes()),
        "degree": [G.degree(n) for n in G.nodes()],
    }

    # Betweenness centrality
    logger.info("  Computing betweenness centrality...")
    betweenness = nx.betweenness_centrality(G)
    metrics["betweenness"] = [betweenness.get(n, 0) for n in G.nodes()]

    # Eigenvector centrality (if connected)
    try:
        logger.info("  Computing eigenvector centrality...")
        if nx.is_connected(G):
            eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
        else:
            # Use largest component
            largest_cc = max(nx.connected_components(G), key=len)
            G_sub = G.subgraph(largest_cc)
            eigenvector_sub = nx.eigenvector_centrality(G_sub, max_iter=1000)
            eigenvector = {n: eigenvector_sub.get(n, 0) for n in G.nodes()}
        metrics["eigenvector"] = [eigenvector.get(n, 0) for n in G.nodes()]
    except Exception as e:
        logger.warning(f"Eigenvector centrality failed: {e}. Using zeros.")
        metrics["eigenvector"] = [0] * len(G.nodes())

    # PageRank
    logger.info("  Computing PageRank...")
    pagerank = nx.pagerank(G)
    metrics["pagerank"] = [pagerank.get(n, 0) for n in G.nodes()]

    df = pd.DataFrame(metrics)
    return df


def validate_graph(
    G: nx.Graph,
    data_proteins: Set[str],
    ppi_proteins: Set[str],
) -> Dict:
    """
    Validate graph against data.

    Args:
        G: NetworkX graph
        data_proteins: Proteins in expression data
        ppi_proteins: Proteins in PPI network

    Returns:
        Validation report
    """
    graph_proteins = set(G.nodes())

    report = {
        "n_nodes": len(G.nodes()),
        "n_edges": len(G.edges()),
        "n_data_proteins": len(data_proteins),
        "n_ppi_proteins": len(ppi_proteins),
        "nodes_in_data": len(graph_proteins & data_proteins),
        "nodes_in_ppi": len(graph_proteins & ppi_proteins),
        "density": nx.density(G),
        "avg_degree": np.mean([G.degree(n) for n in G.nodes()]),
        "n_connected_components": nx.number_connected_components(G),
    }

    # Check for isolated nodes
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    report["n_isolated_nodes"] = len(isolated)

    logger.info("\nGraph validation report:")
    for key, value in report.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.3f}")
        else:
            logger.info(f"  {key}: {value}")

    return report
