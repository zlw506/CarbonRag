import csv
import json
import re
from functools import lru_cache
from pathlib import Path

from app.ai_runtime.config import get_ai_runtime_config
from app.core.config import REPO_ROOT
from app.retrieval.private_schemas import (
    PrivateSampleCatalogItem,
    PrivateSampleDocument,
    PrivateSampleDocumentMetadata,
)

FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\r?\n(?P<meta>.*?)\r?\n---\s*\r?\n(?P<body>.*)$",
    re.DOTALL,
)


def resolve_private_corpus_dir() -> Path:
    private_data_dir = Path(get_ai_runtime_config().private_sample_dir)
    if not private_data_dir.is_absolute():
        private_data_dir = (REPO_ROOT / private_data_dir).resolve()
    return private_data_dir / "corpus"


def _parse_frontmatter(markdown_text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_PATTERN.match(markdown_text.strip())
    if not match:
        raise ValueError("Private sample markdown document is missing valid frontmatter.")

    metadata: dict[str, str] = {}
    for raw_line in match.group("meta").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {raw_line}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, match.group("body").strip()


@lru_cache(maxsize=1)
def load_private_sample_manifest() -> list[PrivateSampleDocumentMetadata]:
    manifest_path = resolve_private_corpus_dir() / "manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [PrivateSampleDocumentMetadata.model_validate(entry) for entry in manifest_payload]


@lru_cache(maxsize=1)
def load_private_sample_catalog() -> list[PrivateSampleCatalogItem]:
    return [
        PrivateSampleCatalogItem(
            doc_id=item.doc_id,
            title=item.title,
            source_type=item.source_type,
            sample_type=item.sample_type,
            business_topic=item.business_topic,
            session_attachable=item.session_attachable,
        )
        for item in load_private_sample_manifest()
    ]


def _load_csv_as_text(doc_path: Path, title: str) -> str:
    with doc_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    lines = [f"样例表《{title}》包含以下记录："]
    for index, row in enumerate(rows, start=1):
        cell_summary = "；".join(f"{key}={value}" for key, value in row.items())
        lines.append(f"第 {index} 行：{cell_summary}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def load_private_sample_documents() -> list[PrivateSampleDocument]:
    corpus_dir = resolve_private_corpus_dir()
    documents: list[PrivateSampleDocument] = []
    for metadata in load_private_sample_manifest():
        doc_path = corpus_dir / metadata.filepath
        if not doc_path.exists():
            raise FileNotFoundError(f"Private sample is missing: {doc_path}")

        if metadata.sample_type == "doc":
            frontmatter, body = _parse_frontmatter(doc_path.read_text(encoding="utf-8"))
            for key in ("doc_id", "title", "source_type", "sample_type", "business_topic"):
                if frontmatter.get(key) != str(getattr(metadata, key)):
                    raise ValueError(f"Frontmatter mismatch for {metadata.doc_id}: {key}")
        else:
            body = _load_csv_as_text(doc_path, metadata.title)

        documents.append(PrivateSampleDocument(metadata=metadata, body=body))
    return documents
