"""Tests for src/graphs/graph_utils.py."""

import numpy as np
import pandas as pd
import pytest
import networkx as nx

from src.graphs.graph_utils import (
    compute_centrality_metrics,
    create_network,
    map_proteins_to_ids,
    validate_graph,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ppi_edges():
    """Small PPI edge DataFrame (5 edges among 6 proteins)."""
    return pd.DataFrame({
        "protein1": ["P1", "P1", "P2", "P3", "P4"],
        "protein2": ["P2", "P3", "P4", "P5", "P6"],
        "combined_score": [900, 800, 750, 700, 850],
    })


@pytest.fixture
def coab_edges():
    """Small co-abundance edge DataFrame."""
    return pd.DataFrame({
        "protein1": ["P1", "P2"],
        "protein2": ["P5", "P6"],
        "rho": [0.7, -0.6],
        "pvalue": [0.01, 0.02],
    })


# ---------------------------------------------------------------------------
# create_network
# ---------------------------------------------------------------------------

def test_create_network_from_ppi(ppi_edges):
    """Graph contains the correct number of edges and nodes from PPI data."""
    G = create_network(ppi_edges, coab_edges=None)

    assert isinstance(G, nx.Graph)
    assert G.number_of_edges() == 5
    for p in ["P1", "P2", "P3", "P4", "P5", "P6"]:
        assert p in G.nodes()


def test_create_network_ppi_edge_attributes(ppi_edges):
    """PPI edges have type='ppi' and a normalized weight."""
    G = create_network(ppi_edges)

    attrs = G["P1"]["P2"]
    assert attrs["type"] == "ppi"
    assert 0 <= attrs["weight"] <= 1


def test_create_network_with_coab(ppi_edges, coab_edges):
    """Adding co-abundance edges increases edge count."""
    G_ppi = create_network(ppi_edges)
    G_both = create_network(ppi_edges, coab_edges)

    assert G_both.number_of_edges() > G_ppi.number_of_edges()


def test_create_network_coab_attributes(ppi_edges, coab_edges):
    """Co-abundance edges carry type='coab' and absolute rho as weight."""
    G = create_network(ppi_edges, coab_edges)

    if G.has_edge("P1", "P5"):
        attrs = G["P1"]["P5"]
        assert attrs["type"] == "coab"
        assert attrs["weight"] == pytest.approx(abs(0.7))


def test_create_network_with_protein_filter(ppi_edges):
    """When proteins set is provided, only those nodes appear."""
    subset = {"P1", "P2", "P3"}
    G = create_network(ppi_edges, proteins=subset)

    assert set(G.nodes()) == subset


def test_create_network_empty_ppi():
    """Empty PPI DataFrame produces an empty graph."""
    empty = pd.DataFrame(columns=["protein1", "protein2", "combined_score"])
    G = create_network(empty)
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0


# ---------------------------------------------------------------------------
# compute_centrality_metrics
# ---------------------------------------------------------------------------

def test_centrality_columns(ppi_edges):
    """Output DataFrame has the required centrality columns."""
    G = create_network(ppi_edges)
    df = compute_centrality_metrics(G)

    required = {"protein", "degree", "betweenness", "pagerank"}
    assert required.issubset(set(df.columns))


def test_centrality_row_count(ppi_edges):
    """One row per node in the graph."""
    G = create_network(ppi_edges)
    df = compute_centrality_metrics(G)
    assert len(df) == G.number_of_nodes()


def test_centrality_values_in_range(ppi_edges):
    """Betweenness and pagerank values are in [0, 1]."""
    G = create_network(ppi_edges)
    df = compute_centrality_metrics(G)

    assert (df["betweenness"] >= 0).all() and (df["betweenness"] <= 1).all()
    assert (df["pagerank"] >= 0).all() and (df["pagerank"] <= 1).all()


# ---------------------------------------------------------------------------
# validate_graph
# ---------------------------------------------------------------------------

def test_validate_graph_keys(ppi_edges):
    """validate_graph report contains all expected keys."""
    G = create_network(ppi_edges)
    proteins = {"P1", "P2", "P3"}
    ppi_proteins = set(ppi_edges["protein1"]) | set(ppi_edges["protein2"])

    report = validate_graph(G, proteins, ppi_proteins)

    for key in ("n_nodes", "n_edges", "density", "avg_degree", "n_connected_components"):
        assert key in report


def test_validate_graph_node_count(ppi_edges):
    """n_nodes matches graph size."""
    G = create_network(ppi_edges)
    report = validate_graph(G, set(), set())
    assert report["n_nodes"] == G.number_of_nodes()


# ---------------------------------------------------------------------------
# map_proteins_to_ids
# ---------------------------------------------------------------------------

def test_map_proteins_finds_common(ppi_edges):
    """Proteins appearing in both data and PPI are returned."""
    data_proteins = pd.Index(["P1", "P2", "P99"])  # P99 not in PPI
    in_ppi, mapping = map_proteins_to_ids(data_proteins, ppi_edges)

    assert "P1" in in_ppi
    assert "P2" in in_ppi
    assert "P99" not in in_ppi


def test_map_proteins_identity_mapping(ppi_edges):
    """The returned mapping is an identity map (protein → same string)."""
    data_proteins = pd.Index(["P1", "P3"])
    _, mapping = map_proteins_to_ids(data_proteins, ppi_edges)

    for protein, mapped in mapping.items():
        assert protein == mapped


def test_map_proteins_no_overlap(ppi_edges):
    """Returns empty set when data proteins have no intersection with PPI."""
    data_proteins = pd.Index(["Z1", "Z2"])
    in_ppi, mapping = map_proteins_to_ids(data_proteins, ppi_edges)

    assert len(in_ppi) == 0
    assert len(mapping) == 0
