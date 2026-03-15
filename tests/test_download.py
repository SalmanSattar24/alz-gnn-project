"""
Tests for the real-data download scripts.

All tests use local fixtures and mock objects — no network calls are made.

Coverage:
  - src/download/download_string_network.py
  - src/download/download_ampad_rosmap.py
"""

import gzip
import io
import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

FAKE_STRING_ROWS = textwrap.dedent("""\
    protein1 protein2 neighborhood neighborhood_transferred fusion cooccurence homology coexpression coexpression_transferred experimentally_determined_interaction experimentally_determined_interaction_transferred database_annotated database_annotated_transferred textmining textmining_transferred combined_score
    9606.ENSP00000001 9606.ENSP00000002 0 0 0 0 0 50 0 900 0 900 0 0 0 900
    9606.ENSP00000003 9606.ENSP00000004 0 0 0 0 0 40 0 200 0 200 0 0 0 400
    9606.ENSP00000005 9606.ENSP00000006 0 0 0 0 0 60 0 750 0 750 0 0 0 750
    9606.ENSP00000007 9606.ENSP00000008 0 0 0 0 0 30 0 100 0 100 0 0 0 100
""")


def _make_gz(content: str) -> bytes:
    """Return gzip-compressed bytes for a string."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(content.encode())
    return buf.getvalue()


@pytest.fixture
def string_gz(tmp_path) -> Path:
    """Write a fake STRING .gz file to a temp directory."""
    gz_path = tmp_path / "9606.protein.links.detailed.v11.5.txt.gz"
    gz_path.write_bytes(_make_gz(FAKE_STRING_ROWS))
    return gz_path


# ---------------------------------------------------------------------------
# download_string_network  —  _iter_filtered_lines
# ---------------------------------------------------------------------------

class TestIterFilteredLines:
    """Unit tests for the internal streaming-filter function."""

    def test_header_always_included(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=0))
        # First line should be the header (tab-separated)
        assert "protein1" in lines[0]
        assert "combined_score" in lines[0]

    def test_threshold_700_keeps_high_scores(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=700))
        # Header + rows with score 900 and 750 (not 400 or 100)
        assert len(lines) == 3   # header + 2 data rows

    def test_threshold_900_exact(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=900))
        assert len(lines) == 2   # header + 1 row with score exactly 900

    def test_threshold_0_keeps_all(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=0))
        assert len(lines) == 5   # header + 4 data rows

    def test_taxon_prefix_stripped(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=0))
        data_lines = lines[1:]
        for line in data_lines:
            fields = line.split("\t")
            assert not fields[0].startswith("9606.")
            assert not fields[1].startswith("9606.")

    def test_output_is_tab_separated(self, string_gz):
        from src.download.download_string_network import _iter_filtered_lines

        lines = list(_iter_filtered_lines(string_gz, score_threshold=0))
        for line in lines:
            # Every line should have tabs (not spaces) as delimiter
            assert "\t" in line


# ---------------------------------------------------------------------------
# download_string_network  —  string_network_present
# ---------------------------------------------------------------------------

class TestStringNetworkPresent:
    def test_returns_false_when_no_file(self, tmp_path):
        from src.download.download_string_network import string_network_present

        mock_m = MagicMock()
        mock_m.file_exists.return_value = False
        with patch("src.download.download_string_network.ManifestManager", return_value=mock_m):
            present, path = string_network_present(output_dir=tmp_path)
        assert present is False

    def test_returns_true_when_file_exists(self, tmp_path):
        from src.download.download_string_network import (
            HIGHCONF_FILENAME,
            string_network_present,
        )

        tsv = tmp_path / HIGHCONF_FILENAME
        tsv.write_text("protein1\tprotein2\tcombined_score\nENSP1\tENSP2\t900\n")

        mock_m = MagicMock()
        mock_m.file_exists.return_value = False
        with patch("src.download.download_string_network.ManifestManager", return_value=mock_m):
            present, path = string_network_present(output_dir=tmp_path)
        assert present is True
        assert path == tsv

    def test_returns_false_for_empty_file(self, tmp_path):
        from src.download.download_string_network import (
            HIGHCONF_FILENAME,
            string_network_present,
        )

        tsv = tmp_path / HIGHCONF_FILENAME
        tsv.write_bytes(b"")   # zero bytes

        mock_m = MagicMock()
        mock_m.file_exists.return_value = False
        with patch("src.download.download_string_network.ManifestManager", return_value=mock_m):
            present, _ = string_network_present(output_dir=tmp_path)
        assert present is False


# ---------------------------------------------------------------------------
# download_string_network  —  full flow (mocked HTTP)
# ---------------------------------------------------------------------------

class TestDownloadStringNetworkFull:
    @patch("src.download.download_string_network.download_file")
    def test_writes_filtered_tsv(self, mock_dl, tmp_path, string_gz):
        """download_string_network writes only edges above the threshold."""
        from src.download.download_string_network import (
            HIGHCONF_FILENAME,
            download_string_network,
        )

        # Make download_file copy the fake .gz into the expected location
        def fake_download(url, dest_path, **kwargs):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(string_gz.read_bytes())
            return True

        mock_dl.side_effect = fake_download

        ok = download_string_network(
            output_dir=tmp_path,
            score_threshold=700,
            keep_gz=False,
        )

        assert ok is True
        tsv_path = tmp_path / HIGHCONF_FILENAME
        assert tsv_path.exists()

        lines = tsv_path.read_text().splitlines()
        # Header + 2 rows (scores 900 and 750)
        assert len(lines) == 3

    @patch("src.download.download_string_network.download_file")
    def test_keeps_gz_when_requested(self, mock_dl, tmp_path, string_gz):
        """With keep_gz=True the source .gz is not deleted."""
        from src.download.download_string_network import (
            _GZ_FILENAME,
            download_string_network,
        )

        def fake_download(url, dest_path, **kwargs):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(string_gz.read_bytes())
            return True

        mock_dl.side_effect = fake_download

        download_string_network(output_dir=tmp_path, score_threshold=700, keep_gz=True)

        gz_path = tmp_path / _GZ_FILENAME
        assert gz_path.exists()

    @patch("src.download.download_string_network.download_file", return_value=False)
    def test_returns_false_on_download_failure(self, mock_dl, tmp_path):
        """Returns False and does not create TSV when download_file fails."""
        from src.download.download_string_network import (
            HIGHCONF_FILENAME,
            download_string_network,
        )

        ok = download_string_network(output_dir=tmp_path, score_threshold=700)

        assert ok is False
        assert not (tmp_path / HIGHCONF_FILENAME).exists()


# ---------------------------------------------------------------------------
# download_ampad_rosmap  —  _build_syn_client
# ---------------------------------------------------------------------------

class TestBuildSynClient:
    def test_returns_none_when_synapseclient_missing(self, monkeypatch):
        """Returns None and logs an error if synapseclient is not installed."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "synapseclient":
                raise ImportError("No module named 'synapseclient'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        from src.download.download_ampad_rosmap import _build_syn_client

        result = _build_syn_client()
        assert result is None

    def test_returns_none_when_login_fails(self):
        """Returns None when Synapse login raises an exception."""
        mock_syn = MagicMock()
        mock_syn.login.side_effect = Exception("invalid credentials")

        with patch("synapseclient.Synapse", return_value=mock_syn):
            from src.download.download_ampad_rosmap import _build_syn_client

            result = _build_syn_client(username="u", password="bad")
        assert result is None

    def test_returns_client_with_auth_token(self):
        """Returns authenticated client when auth_token is valid."""
        mock_syn = MagicMock()
        mock_syn.login.return_value = None  # success

        with patch("synapseclient.Synapse", return_value=mock_syn):
            from src.download.download_ampad_rosmap import _build_syn_client

            result = _build_syn_client(auth_token="fake_token")

        assert result is mock_syn
        mock_syn.login.assert_called_once_with(authToken="fake_token", silent=True)

    def test_uses_env_var_when_no_args(self, monkeypatch):
        """Reads SYNAPSE_AUTH_TOKEN from environment when not passed directly."""
        monkeypatch.setenv("SYNAPSE_AUTH_TOKEN", "env_token")

        mock_syn = MagicMock()
        mock_syn.login.return_value = None

        with patch("synapseclient.Synapse", return_value=mock_syn):
            from src.download.download_ampad_rosmap import _build_syn_client

            result = _build_syn_client()

        assert result is mock_syn
        call_kwargs = mock_syn.login.call_args[1]
        assert call_kwargs["authToken"] == "env_token"


# ---------------------------------------------------------------------------
# download_ampad_rosmap  —  rosmap_files_present
# ---------------------------------------------------------------------------

class TestRosmapFilesPresent:
    def test_returns_false_when_empty_dir(self, tmp_path):
        from src.download.download_ampad_rosmap import rosmap_files_present

        mock_m = MagicMock()
        mock_m.file_exists.return_value = False
        with patch("src.download.download_ampad_rosmap.ManifestManager", return_value=mock_m):
            present, path = rosmap_files_present(output_dir=tmp_path)
        assert present is False

    def test_returns_true_when_csv_present(self, tmp_path):
        from src.download.download_ampad_rosmap import rosmap_files_present

        rosmap_dir = tmp_path / "ROSMAP"
        rosmap_dir.mkdir()
        csv = rosmap_dir / "proteomics.csv"
        csv.write_text("protein,value\nENSP1,1.0\n")

        mock_m = MagicMock()
        mock_m.file_exists.return_value = False
        with patch("src.download.download_ampad_rosmap.ManifestManager", return_value=mock_m):
            present, path = rosmap_files_present(output_dir=tmp_path)
        assert present is True
        assert path == csv


# ---------------------------------------------------------------------------
# download_ampad_rosmap  —  download_rosmap_proteomics  (mocked Synapse)
# ---------------------------------------------------------------------------

class TestDownloadRosmapProteomics:
    def _make_mock_entity(self, tmp_path: Path, filename: str) -> MagicMock:
        """Create a mock Synapse entity that points to a real temp file."""
        fpath = tmp_path / filename
        fpath.write_text("mock_content")
        entity = MagicMock()
        entity.path = str(fpath)
        return entity

    def test_returns_false_when_synapse_unavailable(self, tmp_path):
        """Returns False immediately if _build_syn_client fails."""
        with patch(
            "src.download.download_ampad_rosmap._build_syn_client",
            return_value=None,
        ):
            from src.download.download_ampad_rosmap import download_rosmap_proteomics

            ok = download_rosmap_proteomics(output_dir=tmp_path)
        assert ok is False

    def test_downloads_primary_proteomics_file(self, tmp_path):
        """Returns True and records manifest entry when primary file downloads."""
        mock_syn = MagicMock()
        rosmap_dir = tmp_path / "ROSMAP"
        rosmap_dir.mkdir(parents=True)

        entities = {
            "syn21261359": self._make_mock_entity(rosmap_dir, "proteomics_tmt.csv"),
            "syn21261360": self._make_mock_entity(rosmap_dir, "metadata.csv"),
            "syn3191087":  self._make_mock_entity(rosmap_dir, "clinical.csv"),
        }
        mock_syn.get.side_effect = lambda syn_id, **kwargs: entities[syn_id]

        with patch(
            "src.download.download_ampad_rosmap._build_syn_client",
            return_value=mock_syn,
        ):
            from src.download.download_ampad_rosmap import download_rosmap_proteomics

            ok = download_rosmap_proteomics(output_dir=tmp_path)

        assert ok is True

    def test_skip_clinical_flag(self, tmp_path):
        """With skip_clinical=True the clinical Synapse ID is never requested."""
        mock_syn = MagicMock()
        rosmap_dir = tmp_path / "ROSMAP"
        rosmap_dir.mkdir(parents=True)

        def make_entity(syn_id, **kwargs):
            name = {
                "syn21261359": "proteomics_tmt.csv",
                "syn21261360": "metadata.csv",
            }[syn_id]
            return self._make_mock_entity(rosmap_dir, name)

        mock_syn.get.side_effect = make_entity

        with patch(
            "src.download.download_ampad_rosmap._build_syn_client",
            return_value=mock_syn,
        ):
            from src.download.download_ampad_rosmap import (
                ROSMAP_SYNAPSE_IDS,
                download_rosmap_proteomics,
            )

            ok = download_rosmap_proteomics(
                output_dir=tmp_path,
                skip_clinical=True,
            )

        assert ok is True
        # syn3191087 (clinical) should NOT have been fetched
        fetched_ids = [call.args[0] for call in mock_syn.get.call_args_list]
        assert ROSMAP_SYNAPSE_IDS["clinical"] not in fetched_ids

    def test_returns_false_when_primary_file_fails(self, tmp_path):
        """Returns False if the primary proteomics_tmt download raises."""
        mock_syn = MagicMock()
        mock_syn.get.side_effect = Exception("access denied")

        # Use a fresh in-memory manifest so previous test runs don't interfere
        mock_manifest = MagicMock()
        mock_manifest.file_exists.return_value = False

        with patch(
            "src.download.download_ampad_rosmap._build_syn_client",
            return_value=mock_syn,
        ), patch(
            "src.download.download_ampad_rosmap.ManifestManager",
            return_value=mock_manifest,
        ):
            from src.download.download_ampad_rosmap import download_rosmap_proteomics

            ok = download_rosmap_proteomics(output_dir=tmp_path, skip_clinical=True)

        assert ok is False
