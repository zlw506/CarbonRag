import json
import re
from functools import lru_cache
from pathlib import Path

from app.ai_runtime.config import get_ai_runtime_config
from app.core.config import REPO_ROOT
from app.retrieval.schemas import PublicPolicyDocument, PublicPolicyDocumentMetadata

FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\r?\n(?P<meta>.*?)\r?\n---\s*\r?\n(?P<body>.*)$",
    re.DOTALL,
)


def resolve_public_corpus_dir() -> Path:
    public_data_dir = Path(get_ai_runtime_config().public_data_dir)
    if not public_data_dir.is_absolute():
        public_data_dir = (REPO_ROOT / public_data_dir).resolve()
    return public_data_dir / "corpus"


def _parse_frontmatter(markdown_text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_PATTERN.match(markdown_text.strip())
    if not match:
        raise ValueError("Markdown document is missing valid frontmatter.")

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
def load_public_policy_documents() -> list[PublicPolicyDocument]:
    corpus_dir = resolve_public_corpus_dir()
    manifest_path = corpus_dir / "manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    documents: list[PublicPolicyDocument] = []
    for entry in manifest_payload:
        metadata = PublicPolicyDocumentMetadata.model_validate(entry)
        doc_path = corpus_dir / metadata.filepath
        if not doc_path.exists():
            raise FileNotFoundError(f"Policy document is missing: {doc_path}")

        frontmatter, body = _parse_frontmatter(doc_path.read_text(encoding="utf-8"))
        for key in ("doc_id", "title", "source", "source_url", "issued_at", "region", "doc_type"):
            if frontmatter.get(key) != str(getattr(metadata, key)):
                raise ValueError(f"Frontmatter mismatch for {metadata.doc_id}: {key}")

        documents.append(PublicPolicyDocument(metadata=metadata, body=body))

    return documents
