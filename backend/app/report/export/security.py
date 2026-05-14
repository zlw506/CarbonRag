import hashlib
from pathlib import Path


def ensure_child_path(base_dir: Path, candidate: Path) -> Path:
    resolved_base = base_dir.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_base != resolved_candidate and resolved_base not in resolved_candidate.parents:
        raise ValueError("Export path escapes the configured report output directory.")
    return resolved_candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
