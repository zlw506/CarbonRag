import json
from functools import lru_cache

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.factors.schema import FactorRecord
from app.carbon_factors.carbonstop import CARBONSTOP_MAPPING_VERSION, CarbonStopImportPayload, CarbonStopPublicAdapter
from app.carbon_factors.schemas import (
    CarbonFactorDetail,
    CarbonFactorFacets,
    CarbonFactorImportJob,
    CarbonFactorImportRequest,
    CarbonFactorSearchResponse,
    CarbonFactorSource,
    CarbonFactorSummary,
)
from app.carbon_factors.store import CarbonFactorStore, get_carbon_factor_store


class CarbonFactorDatabaseService:
    def __init__(
        self,
        *,
        store: CarbonFactorStore | None = None,
        factor_loader: CarbonFactorLoader | None = None,
        carbonstop_adapter: CarbonStopPublicAdapter | None = None,
    ) -> None:
        self.store = store or get_carbon_factor_store()
        self.factor_loader = factor_loader or CarbonFactorLoader()
        self.carbonstop_adapter = carbonstop_adapter or CarbonStopPublicAdapter()

    def ensure_seeded(self) -> None:
        if not self._has_current_carbonstop_seed():
            self.import_carbonstop_seed(owner_user_id="system")
        if self.store.count_factors() > 0:
            return
        records = self.factor_loader.load_records()
        self.import_records(
            owner_user_id="system",
            source_kind="seed",
            source={
                "title": "CarbonRag 内置碳因子种子库",
                "publisher": "CarbonRag",
                "source_url": None,
                "license": "project-curated",
                "published_year": None,
                "source_type": "internal_curated",
            },
            records=records,
        )

    def import_carbonstop_seed(self, *, owner_user_id: str) -> CarbonFactorImportJob:
        payload = self.carbonstop_adapter.load_seed_payload()
        return self.import_carbonstop_payload(owner_user_id=owner_user_id, payload=payload, source_kind="carbonstop_public_seed")

    def sync_carbonstop_public(self, *, owner_user_id: str) -> CarbonFactorImportJob:
        payload = self.carbonstop_adapter.fetch_public_payload()
        return self.import_carbonstop_payload(owner_user_id=owner_user_id, payload=payload, source_kind="carbonstop_public")

    def import_carbonstop_payload(
        self,
        *,
        owner_user_id: str,
        payload: CarbonStopImportPayload,
        source_kind: str,
    ) -> CarbonFactorImportJob:
        source_ids: dict[str, str] = {}
        for item in payload.rows:
            source_key = json.dumps(item.source, ensure_ascii=False, sort_keys=True)
            source_id = source_ids.get(source_key)
            if source_id is None:
                source_id = self.store.upsert_source(**item.source)
                source_ids[source_key] = source_id
            self.store.upsert_factor_record(
                record=item.record,
                source_id=source_id,
                quality="public_ccdb",
                metadata_extra=item.raw,
            )
        job = self.store.create_import_job(
            owner_user_id=owner_user_id,
            source_kind=source_kind,
            status="succeeded",
            summary={
                "source": "CarbonStop CCDB 中国碳数据库",
                "origin": payload.origin,
                "mapping_version": CARBONSTOP_MAPPING_VERSION,
                "accepted_count": len(payload.rows),
                "skipped_count": len(payload.skipped_rows),
                "category_count": len(payload.categories),
                "categories": payload.categories,
                "skipped_examples": payload.skipped_rows[:20],
            },
        )
        return self._row_to_import_job(job)

    def search(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        industry: str | None = None,
        region: str | None = None,
        year: int | None = None,
        source_type: str | None = None,
        quality: str | None = None,
        unit: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CarbonFactorSearchResponse:
        self.ensure_seeded()
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        rows, total = self.store.search_factors(
            q=q,
            category=category,
            industry=industry,
            region=region,
            year=year,
            source_type=source_type,
            quality=quality,
            unit=unit,
            page=page,
            page_size=page_size,
        )
        return CarbonFactorSearchResponse(
            items=[self._row_to_summary(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_factor(self, *, factor_id: str) -> CarbonFactorDetail | None:
        self.ensure_seeded()
        row = self.store.get_factor(factor_id=factor_id)
        if row is None:
            return None
        summary = self._row_to_summary(row)
        metadata = json.loads(row.get("metadata_json") or "{}")
        return CarbonFactorDetail(
            **summary.model_dump(),
            aliases=self.store.list_aliases(factor_id=factor_id),
            metadata=metadata,
            is_enabled=bool(row.get("is_enabled", True)),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_sources(self) -> list[CarbonFactorSource]:
        self.ensure_seeded()
        return [self._row_to_source(row, prefix="") for row in self.store.list_sources()]

    def facets(self) -> CarbonFactorFacets:
        self.ensure_seeded()
        values = self.store.facets()
        values["category_tree"] = self._build_category_tree()
        return CarbonFactorFacets.model_validate(values)

    def import_payload(self, *, owner_user_id: str, payload: CarbonFactorImportRequest) -> CarbonFactorImportJob:
        records = [FactorRecord.model_validate(item) for item in payload.factor_records]
        return self.import_records(
            owner_user_id=owner_user_id,
            source_kind=payload.source_kind,
            source=payload.source.model_dump(),
            records=records,
        )

    def import_records(self, *, owner_user_id: str, source_kind: str, source: dict, records: list[FactorRecord]) -> CarbonFactorImportJob:
        source_id = self.store.upsert_source(
            title=source["title"],
            publisher=source["publisher"],
            source_url=source.get("source_url"),
            license=source.get("license"),
            published_year=source.get("published_year"),
            source_type=source.get("source_type") or "internal_curated",
        )
        for record in records:
            self.store.upsert_factor_record(record=record, source_id=source_id)
        job = self.store.create_import_job(
            owner_user_id=owner_user_id,
            source_kind=source_kind,
            status="succeeded",
            summary={
                "source_id": source_id,
                "accepted_count": len(records),
                "rejected_count": 0,
            },
        )
        return self._row_to_import_job(job)

    def list_import_jobs(self) -> list[CarbonFactorImportJob]:
        return [self._row_to_import_job(row) for row in self.store.list_import_jobs()]

    def update_factor(self, *, factor_id: str, is_enabled: bool | None, quality: str | None = None) -> CarbonFactorDetail | None:
        updated = self.store.set_factor_enabled(factor_id=factor_id, is_enabled=is_enabled, quality=quality)
        if not updated:
            return None
        return self.get_factor(factor_id=factor_id)

    @staticmethod
    def _row_to_source(row: dict, *, prefix: str = "source_") -> CarbonFactorSource | None:
        source_id = row.get(f"{prefix}source_id")
        if not source_id:
            return None
        return CarbonFactorSource(
            source_id=source_id,
            title=row.get(f"{prefix}title") or "",
            publisher=row.get(f"{prefix}publisher") or "",
            source_url=row.get(f"{prefix}source_url"),
            license=row.get(f"{prefix}license"),
            published_year=row.get(f"{prefix}published_year"),
            source_type=row.get(f"{prefix}source_type") or "internal_curated",
            created_at=row.get(f"{prefix}created_at") or "",
            updated_at=row.get(f"{prefix}updated_at") or "",
        )

    def _row_to_summary(self, row: dict) -> CarbonFactorSummary:
        metadata = json.loads(row.get("metadata_json") or "{}")
        return CarbonFactorSummary(
            factor_id=row["factor_id"],
            name=row["name"],
            category=row["category"],
            industry=row.get("industry"),
            scope=row["scope"],
            region=row.get("region"),
            region_code=row.get("region_code"),
            region_name=row.get("region_name"),
            year=row.get("year"),
            factor_value=float(row["factor_value"]),
            factor_unit=row["factor_unit"],
            activity_unit=row["activity_unit"],
            co2e_unit=row.get("co2e_unit") or "kgCO2e",
            quality=row["quality"],
            version=row["version"],
            source=self._row_to_source(row),
            tags=metadata.get("tags") or [],
        )

    @staticmethod
    def _row_to_import_job(row: dict) -> CarbonFactorImportJob:
        return CarbonFactorImportJob(
            job_id=row["job_id"],
            source_kind=row["source_kind"],
            status=row["status"],
            summary=json.loads(row.get("summary_json") or "{}"),
            error_message=row.get("error_message"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _build_category_tree(self) -> list[dict]:
        accepted_counts: dict[tuple[str, str], int] = {}
        rows, _ = self.store.search_factors(quality="public_ccdb", page=1, page_size=10000)
        for row in rows:
            metadata = json.loads(row.get("metadata_json") or "{}")
            group = metadata.get("ccdb_group_label") or row.get("industry") or "其他"
            child = metadata.get("ccdb_classify_label") or row.get("category") or "其他"
            accepted_counts[(group, child)] = accepted_counts.get((group, child), 0) + 1

        ordered_categories = self._latest_carbonstop_categories()
        if not ordered_categories:
            return self._category_tree_from_counts(accepted_counts)

        tree: dict[str, dict] = {}
        for item in ordered_categories:
            group = item.get("groupLabel") or "其他"
            child = item.get("classifyLabel") or "其他"
            count = accepted_counts.get((group, child), 0)
            node = tree.setdefault(
                group,
                {
                    "label": group,
                    "value": item.get("groupValue"),
                    "count": 0,
                    "children": [],
                },
            )
            node["count"] += count
            node["children"].append(
                {
                    "label": child,
                    "value": item.get("classifyValue"),
                    "count": count,
                    "raw_count": item.get("count") or 0,
                }
            )

        # Keep CarbonStop's classification order, but surface accepted/calculation-ready
        # counts so encrypted public rows are not mistaken for usable calculation factors.
        return list(tree.values())

    def _has_current_carbonstop_seed(self) -> bool:
        for row in self.store.list_import_jobs():
            summary = json.loads(row.get("summary_json") or "{}")
            if summary.get("source") != "CarbonStop CCDB 中国碳数据库":
                continue
            if summary.get("mapping_version") == CARBONSTOP_MAPPING_VERSION:
                return True
        return False

    def _latest_carbonstop_categories(self) -> list[dict]:
        for row in self.store.list_import_jobs():
            summary = json.loads(row.get("summary_json") or "{}")
            if summary.get("source") != "CarbonStop CCDB 中国碳数据库":
                continue
            categories = summary.get("categories") or []
            if categories:
                return categories
        return []

    @staticmethod
    def _category_tree_from_counts(accepted_counts: dict[tuple[str, str], int]) -> list[dict]:
        tree: dict[str, dict] = {}
        for (group, child), count in sorted(accepted_counts.items()):
            node = tree.setdefault(group, {"label": group, "value": group, "count": 0, "children": []})
            node["count"] += count
            node["children"].append({"label": child, "value": child, "count": count, "raw_count": count})
        return list(tree.values())


@lru_cache(maxsize=1)
def get_carbon_factor_database_service() -> CarbonFactorDatabaseService:
    return CarbonFactorDatabaseService()
