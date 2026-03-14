"""
Download utilities for managing multi-omics datasets.

Provides retry logic, manifest tracking, and common utilities.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


def compute_file_hash(file_path: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Compute file hash.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5)
        chunk_size: Chunk size for reading

    Returns:
        File hash string
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(
    url: str,
    output_path: Path,
    max_retries: int = 3,
    timeout: int = 30,
) -> bool:
    """
    Download file with retry logic.

    Args:
        url: Download URL
        output_path: Where to save file
        max_retries: Maximum retry attempts
        timeout: Request timeout in seconds

    Returns:
        True if successful
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = (downloaded / total_size) * 100
                            print(f"  Downloaded: {pct:.1f}%", end="\r")

            print(f"  Successfully downloaded: {output_path.name}")
            return True

        except requests.RequestException as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Retrying in {wait_time}s...")
                time.sleep(wait_time)

    print(f"  Failed to download after {max_retries} attempts")
    return False


class ManifestManager:
    """Manage download manifest with file hashes and metadata."""

    def __init__(self, manifest_path: Path = Path("data/manifest.json")):
        """
        Initialize manifest manager.

        Args:
            manifest_path: Path to manifest file
        """
        self.path = manifest_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load manifest from file."""
        if self.path.exists():
            with open(self.path, "r") as f:
                return json.load(f)
        return {"files": {}, "metadata": {}}

    def save(self) -> None:
        """Save manifest to file."""
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_file(
        self,
        name: str,
        path: Path,
        source: str,
        algorithm: str = "sha256",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add file to manifest.

        Args:
            name: File identifier
            path: Path to file
            source: Data source
            algorithm: Hash algorithm
            metadata: Additional metadata
        """
        file_hash = compute_file_hash(path, algorithm)
        self.data["files"][name] = {
            "path": str(path),
            "hash": file_hash,
            "algorithm": algorithm,
            "source": source,
            "size": path.stat().st_size,
            "timestamp": str(Path(path).stat().st_mtime),
        }
        if metadata:
            self.data["files"][name]["metadata"] = metadata
        self.save()

    def get_file(self, name: str) -> Optional[Dict[str, Any]]:
        """Get file info from manifest."""
        return self.data["files"].get(name)

    def file_exists(self, name: str) -> bool:
        """Check if file is in manifest."""
        return name in self.data["files"]

    def verify_file(self, name: str, file_path: Path) -> bool:
        """
        Verify file against manifest hash.

        Args:
            name: File identifier
            file_path: Path to file

        Returns:
            True if hash matches
        """
        if name not in self.data["files"]:
            return False

        file_info = self.data["files"][name]
        expected_hash = file_info["hash"]
        algorithm = file_info.get("algorithm", "sha256")
        current_hash = compute_file_hash(file_path, algorithm)

        return current_hash == expected_hash

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to manifest."""
        self.data["metadata"][key] = value
        self.save()

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata from manifest."""
        return self.data["metadata"].get(key)
