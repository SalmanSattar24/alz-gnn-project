"""Tests for src/config.py — load_config / save_config."""

import pytest
import yaml
from pathlib import Path

from src.config import load_config, save_config


def test_load_config_valid(tmp_path):
    """load_config reads a YAML file and returns a dict."""
    cfg_data = {"data": {"raw_dir": "data/raw"}, "debug": {"seed": 42}}
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml.dump(cfg_data))

    result = load_config(str(cfg_file))

    assert isinstance(result, dict)
    assert result["data"]["raw_dir"] == "data/raw"
    assert result["debug"]["seed"] == 42


def test_load_config_missing_file():
    """load_config raises FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config_XXXX.yaml")


def test_load_config_empty_file(tmp_path):
    """load_config returns None for an empty YAML file (yaml.safe_load behaviour)."""
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")

    result = load_config(str(cfg_file))
    assert result is None


def test_save_config_creates_file(tmp_path):
    """save_config writes the dict to disk as valid YAML."""
    cfg = {"model": {"architecture": "GAT"}, "training": {"epochs": 50}}
    out_path = tmp_path / "sub" / "config.yaml"

    save_config(cfg, str(out_path))

    assert out_path.exists()
    loaded = yaml.safe_load(out_path.read_text())
    assert loaded["model"]["architecture"] == "GAT"
    assert loaded["training"]["epochs"] == 50


def test_save_load_roundtrip(tmp_path):
    """save_config followed by load_config returns the original dict."""
    original = {"data": {"raw_dir": "data/raw", "processed_dir": "data/processed"}}
    out_path = tmp_path / "roundtrip.yaml"

    save_config(original, str(out_path))
    recovered = load_config(str(out_path))

    assert recovered == original
