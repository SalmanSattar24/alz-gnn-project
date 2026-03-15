"""Tests for src/download/utils.py and src/utils/logger.py."""

import json
import logging
from pathlib import Path

import pytest

from src.download.utils import ManifestManager, compute_file_hash
from src.utils.logger import LoggerContext, get_logger, setup_logger


# ---------------------------------------------------------------------------
# compute_file_hash
# ---------------------------------------------------------------------------

def test_compute_file_hash_sha256(tmp_path):
    """SHA-256 hash is deterministic for the same content."""
    f = tmp_path / "hello.txt"
    f.write_text("hello world")

    h1 = compute_file_hash(f, algorithm="sha256")
    h2 = compute_file_hash(f, algorithm="sha256")

    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest length


def test_compute_file_hash_md5(tmp_path):
    """MD5 hash has the expected 32-char hex length."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02\x03")

    h = compute_file_hash(f, algorithm="md5")
    assert len(h) == 32


def test_compute_file_hash_different_content(tmp_path):
    """Different file contents produce different hashes."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("content A")
    f2.write_text("content B")

    assert compute_file_hash(f1) != compute_file_hash(f2)


# ---------------------------------------------------------------------------
# ManifestManager
# ---------------------------------------------------------------------------

def test_manifest_init_creates_structure(tmp_path):
    """ManifestManager creates a manifest file with 'files' and 'metadata' keys."""
    mm = ManifestManager(tmp_path / "manifest.json")
    mm.save()

    data = json.loads((tmp_path / "manifest.json").read_text())
    assert "files" in data
    assert "metadata" in data


def test_manifest_add_and_get_file(tmp_path):
    """add_file records the file; get_file retrieves it."""
    mm = ManifestManager(tmp_path / "manifest.json")
    f = tmp_path / "sample.txt"
    f.write_text("sample content")

    mm.add_file("sample", f, source="test")
    info = mm.get_file("sample")

    assert info is not None
    assert info["source"] == "test"
    assert "hash" in info
    assert info["size"] == f.stat().st_size


def test_manifest_file_exists(tmp_path):
    """file_exists returns True only after add_file."""
    mm = ManifestManager(tmp_path / "manifest.json")
    f = tmp_path / "x.txt"
    f.write_text("x")

    assert not mm.file_exists("x")
    mm.add_file("x", f, source="test")
    assert mm.file_exists("x")


def test_manifest_verify_file(tmp_path):
    """verify_file returns True when the file is unchanged."""
    mm = ManifestManager(tmp_path / "manifest.json")
    f = tmp_path / "verify.txt"
    f.write_text("stable content")

    mm.add_file("verify", f, source="test")
    assert mm.verify_file("verify", f)


def test_manifest_verify_file_tampered(tmp_path):
    """verify_file returns False after the file content changes."""
    mm = ManifestManager(tmp_path / "manifest.json")
    f = tmp_path / "tamper.txt"
    f.write_text("original")

    mm.add_file("tamper", f, source="test")
    f.write_text("tampered!")
    assert not mm.verify_file("tamper", f)


def test_manifest_metadata(tmp_path):
    """add_metadata / get_metadata round-trip."""
    mm = ManifestManager(tmp_path / "manifest.json")
    mm.add_metadata("pipeline_version", "2.0")

    assert mm.get_metadata("pipeline_version") == "2.0"
    assert mm.get_metadata("nonexistent") is None


def test_manifest_persists_to_disk(tmp_path):
    """Data written by one ManifestManager instance is visible to a fresh one."""
    path = tmp_path / "manifest.json"
    mm1 = ManifestManager(path)
    mm1.add_metadata("key", "value")

    mm2 = ManifestManager(path)
    assert mm2.get_metadata("key") == "value"


# ---------------------------------------------------------------------------
# setup_logger / get_logger / LoggerContext
# ---------------------------------------------------------------------------

def test_setup_logger_returns_logger(tmp_path):
    """setup_logger returns a Logger with the correct name."""
    logger = setup_logger("test.module", log_dir=str(tmp_path))
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_setup_logger_no_duplicates(tmp_path):
    """Calling setup_logger twice for the same name does not add extra handlers."""
    logger1 = setup_logger("test.dedup", log_dir=str(tmp_path))
    handler_count = len(logger1.handlers)
    logger2 = setup_logger("test.dedup", log_dir=str(tmp_path))
    assert len(logger2.handlers) == handler_count


def test_setup_logger_creates_log_file(tmp_path):
    """setup_logger creates a log file in log_dir."""
    setup_logger("test.file", log_dir=str(tmp_path))
    log_files = list(tmp_path.glob("*.log"))
    assert len(log_files) == 1


def test_get_logger_returns_same_instance(tmp_path):
    """get_logger retrieves the same Logger object as setup_logger."""
    named = setup_logger("test.get", log_dir=str(tmp_path))
    retrieved = get_logger("test.get")
    assert named is retrieved


def test_logger_context_restores_level(tmp_path):
    """LoggerContext restores the original level after the block."""
    logger = setup_logger("test.context", log_dir=str(tmp_path))
    original_level = logger.level

    with LoggerContext(logger, "DEBUG"):
        assert logger.level == logging.DEBUG

    assert logger.level == original_level
