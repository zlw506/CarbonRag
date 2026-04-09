from app.private_samples.overrides import load_private_sample_override_map
from app.retrieval.private_corpus_loader import load_private_sample_catalog, load_private_sample_manifest
from app.retrieval.private_schemas import PrivateSampleCatalogItem


def list_attachable_private_sample_catalog(
    *,
    database_url: str | None = None,
    sqlite_db_path=None,
) -> list[PrivateSampleCatalogItem]:
    overrides = load_private_sample_override_map(database_url=database_url, sqlite_db_path=sqlite_db_path)
    items: list[PrivateSampleCatalogItem] = []
    for metadata in load_private_sample_manifest():
        override = overrides.get(metadata.doc_id, {})
        is_enabled = override.get("is_enabled", True)
        session_attachable = override.get("session_attachable", metadata.session_attachable)
        if not is_enabled or not session_attachable:
            continue
        items.append(
            PrivateSampleCatalogItem(
                doc_id=metadata.doc_id,
                title=metadata.title,
                source_type=metadata.source_type,
                sample_type=metadata.sample_type,
                business_topic=metadata.business_topic,
                session_attachable=session_attachable,
            )
        )
    return items


def list_admin_private_sample_catalog(
    *,
    database_url: str | None = None,
    sqlite_db_path=None,
) -> list[dict]:
    overrides = load_private_sample_override_map(database_url=database_url, sqlite_db_path=sqlite_db_path)
    items: list[dict] = []
    for metadata in load_private_sample_manifest():
        override = overrides.get(metadata.doc_id, {})
        items.append(
            {
                "doc_id": metadata.doc_id,
                "title": metadata.title,
                "source_type": metadata.source_type,
                "sample_type": metadata.sample_type,
                "business_topic": metadata.business_topic,
                "session_attachable": override.get("session_attachable", metadata.session_attachable),
                "is_enabled": override.get("is_enabled", True),
            }
        )
    return items


def refresh_private_sample_catalog() -> None:
    load_private_sample_manifest.cache_clear()
    load_private_sample_catalog.cache_clear()
