import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.carbon.factors.schema import FactorRecord
from app.core.config import get_settings
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.runtime_db.compat import connect_postgres
from app.session.store import DEFAULT_SESSION_DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_source_id(*, title: str, publisher: str, source_url: str | None, source_type: str) -> str:
    raw = "|".join([title.strip(), publisher.strip(), source_url or "", source_type.strip()])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"carbon-source-{digest}"


def row_to_dict(row) -> dict:
    return dict(row) if row is not None else {}


class CarbonFactorStore:
    def __init__(self, *, database_url: str | None = None, sqlite_db_path: Path | str | None = None) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        if self.backend_kind == "sqlite":
            self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    def _connect(self):
        if self.backend_kind == "postgresql":
            return connect_postgres(self.database_url)
        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @property
    def placeholder(self) -> str:
        return "%s" if self.backend_kind == "postgresql" else "?"

    def count_factors(self) -> int:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS count FROM carbon_factor_records")
                    return int(cursor.fetchone()["count"])
            row = connection.execute("SELECT COUNT(*) AS count FROM carbon_factor_records").fetchone()
            return int(row["count"])

    def count_catalog_entries(self) -> int:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS count FROM carbon_factor_catalog_entries")
                    return int(cursor.fetchone()["count"])
            row = connection.execute("SELECT COUNT(*) AS count FROM carbon_factor_catalog_entries").fetchone()
            return int(row["count"])

    def upsert_source(
        self,
        *,
        title: str,
        publisher: str,
        source_url: str | None,
        license: str | None,
        published_year: int | None,
        source_type: str,
        now: str | None = None,
    ) -> str:
        now = now or utc_now()
        source_id = stable_source_id(
            title=title,
            publisher=publisher,
            source_url=source_url,
            source_type=source_type,
        )
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO carbon_factor_sources (
                            source_id, title, publisher, source_url, license, published_year, source_type, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            publisher = EXCLUDED.publisher,
                            source_url = EXCLUDED.source_url,
                            license = EXCLUDED.license,
                            published_year = EXCLUDED.published_year,
                            source_type = EXCLUDED.source_type,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (source_id, title, publisher, source_url, license, published_year, source_type, now, now),
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO carbon_factor_sources (
                        source_id, title, publisher, source_url, license, published_year, source_type, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_id) DO UPDATE SET
                        title = excluded.title,
                        publisher = excluded.publisher,
                        source_url = excluded.source_url,
                        license = excluded.license,
                        published_year = excluded.published_year,
                        source_type = excluded.source_type,
                        updated_at = excluded.updated_at
                    """,
                    (source_id, title, publisher, source_url, license, published_year, source_type, now, now),
                )
        return source_id

    def upsert_factor_record(
        self,
        *,
        record: FactorRecord,
        source_id: str,
        quality: str | None = None,
        now: str | None = None,
        metadata_extra: dict | None = None,
    ) -> None:
        now = now or utc_now()
        metadata = {
            "factor_version": record.factor_version,
            "source_type": record.source_type,
            "source_name": record.source_name,
            "source_url": record.source_url,
            "activity_name": record.activity_name,
            "method_type": record.method_type,
            "source_priority": record.source_priority,
            "applicable_standard": record.applicable_standard,
            "quality_level": record.quality_level,
            "is_official": record.is_official,
            "is_default": record.is_default,
            "is_deprecated": record.is_deprecated,
            "notes": record.notes,
            "tags": record.tags,
        }
        if metadata_extra:
            metadata.update(metadata_extra)
        params = (
            record.factor_id,
            source_id,
            record.activity_name,
            record.activity_category,
            record.applicable_industry,
            record.scope,
            record.region,
            record.region_level,
            record.region_code,
            record.region_name,
            record.year,
            record.effective_year,
            "CO2e",
            record.method_type,
            record.factor_value,
            record.factor_unit,
            record.activity_unit,
            record.result_unit,
            quality or record.quality_level or record.source_type,
            not record.is_deprecated,
            record.factor_version,
            json.dumps(metadata, ensure_ascii=False),
            now,
            now,
        )
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO carbon_factor_records (
                            factor_id, source_id, name, category, industry, scope, region, region_level, region_code, region_name,
                            year, effective_year, gas, method_type, factor_value, factor_unit, activity_unit, co2e_unit,
                            quality, is_enabled, version, metadata_json, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (factor_id) DO UPDATE SET
                            source_id = EXCLUDED.source_id,
                            name = EXCLUDED.name,
                            category = EXCLUDED.category,
                            industry = EXCLUDED.industry,
                            scope = EXCLUDED.scope,
                            region = EXCLUDED.region,
                            region_level = EXCLUDED.region_level,
                            region_code = EXCLUDED.region_code,
                            region_name = EXCLUDED.region_name,
                            year = EXCLUDED.year,
                            effective_year = EXCLUDED.effective_year,
                            gas = EXCLUDED.gas,
                            method_type = EXCLUDED.method_type,
                            factor_value = EXCLUDED.factor_value,
                            factor_unit = EXCLUDED.factor_unit,
                            activity_unit = EXCLUDED.activity_unit,
                            co2e_unit = EXCLUDED.co2e_unit,
                            quality = EXCLUDED.quality,
                            is_enabled = EXCLUDED.is_enabled,
                            version = EXCLUDED.version,
                            metadata_json = EXCLUDED.metadata_json,
                            updated_at = EXCLUDED.updated_at
                        """,
                        params,
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO carbon_factor_records (
                        factor_id, source_id, name, category, industry, scope, region, region_level, region_code, region_name,
                        year, effective_year, gas, method_type, factor_value, factor_unit, activity_unit, co2e_unit,
                        quality, is_enabled, version, metadata_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(factor_id) DO UPDATE SET
                        source_id = excluded.source_id,
                        name = excluded.name,
                        category = excluded.category,
                        industry = excluded.industry,
                        scope = excluded.scope,
                        region = excluded.region,
                        region_level = excluded.region_level,
                        region_code = excluded.region_code,
                        region_name = excluded.region_name,
                        year = excluded.year,
                        effective_year = excluded.effective_year,
                        gas = excluded.gas,
                        method_type = excluded.method_type,
                        factor_value = excluded.factor_value,
                        factor_unit = excluded.factor_unit,
                        activity_unit = excluded.activity_unit,
                        co2e_unit = excluded.co2e_unit,
                        quality = excluded.quality,
                        is_enabled = excluded.is_enabled,
                        version = excluded.version,
                        metadata_json = excluded.metadata_json,
                        updated_at = excluded.updated_at
                    """,
                    params,
                )
        self.replace_aliases(record=record)

    def upsert_catalog_entry(self, *, entry, now: str | None = None) -> None:
        now = now or utc_now()
        metadata_json = json.dumps(entry.metadata, ensure_ascii=False)
        params = (
            entry.entry_id,
            "CarbonStop CCDB 中国碳数据库",
            entry.source_url,
            entry.name,
            entry.category,
            entry.industry,
            entry.region,
            entry.year,
            entry.factor_unit,
            entry.activity_unit,
            entry.value_status,
            entry.raw_value,
            entry.factor_value,
            entry.source_title,
            entry.publisher,
            metadata_json,
            entry.is_calculation_ready if self.backend_kind == "postgresql" else int(entry.is_calculation_ready),
            now,
            now,
        )
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO carbon_factor_catalog_entries (
                            entry_id, source_platform, source_url, name, category, industry, region, year,
                            factor_unit, activity_unit, value_status, raw_value, factor_value, source_title,
                            publisher, metadata_json, is_calculation_ready, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (entry_id) DO UPDATE SET
                            source_platform = EXCLUDED.source_platform,
                            source_url = EXCLUDED.source_url,
                            name = EXCLUDED.name,
                            category = EXCLUDED.category,
                            industry = EXCLUDED.industry,
                            region = EXCLUDED.region,
                            year = EXCLUDED.year,
                            factor_unit = EXCLUDED.factor_unit,
                            activity_unit = EXCLUDED.activity_unit,
                            value_status = EXCLUDED.value_status,
                            raw_value = EXCLUDED.raw_value,
                            factor_value = EXCLUDED.factor_value,
                            source_title = EXCLUDED.source_title,
                            publisher = EXCLUDED.publisher,
                            metadata_json = EXCLUDED.metadata_json,
                            is_calculation_ready = EXCLUDED.is_calculation_ready,
                            updated_at = EXCLUDED.updated_at
                        """,
                        params,
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO carbon_factor_catalog_entries (
                        entry_id, source_platform, source_url, name, category, industry, region, year,
                        factor_unit, activity_unit, value_status, raw_value, factor_value, source_title,
                        publisher, metadata_json, is_calculation_ready, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entry_id) DO UPDATE SET
                        source_platform = excluded.source_platform,
                        source_url = excluded.source_url,
                        name = excluded.name,
                        category = excluded.category,
                        industry = excluded.industry,
                        region = excluded.region,
                        year = excluded.year,
                        factor_unit = excluded.factor_unit,
                        activity_unit = excluded.activity_unit,
                        value_status = excluded.value_status,
                        raw_value = excluded.raw_value,
                        factor_value = excluded.factor_value,
                        source_title = excluded.source_title,
                        publisher = excluded.publisher,
                        metadata_json = excluded.metadata_json,
                        is_calculation_ready = excluded.is_calculation_ready,
                        updated_at = excluded.updated_at
                    """,
                    params,
                )

    def replace_aliases(self, *, record: FactorRecord) -> None:
        aliases = list(dict.fromkeys([record.activity_name, record.region_name or "", *(record.tags or [])]))
        aliases = [item for item in aliases if item]
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM carbon_factor_aliases WHERE factor_id = %s", (record.factor_id,))
                    for alias in aliases:
                        cursor.execute(
                            """
                            INSERT INTO carbon_factor_aliases (alias_id, factor_id, alias, locale)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (alias_id) DO NOTHING
                            """,
                            (f"alias-{hashlib.sha1((record.factor_id + alias).encode('utf-8')).hexdigest()[:16]}", record.factor_id, alias, "zh-CN"),
                        )
        else:
            with self._connect() as connection:
                connection.execute("DELETE FROM carbon_factor_aliases WHERE factor_id = ?", (record.factor_id,))
                for alias in aliases:
                    connection.execute(
                        """
                        INSERT INTO carbon_factor_aliases (alias_id, factor_id, alias, locale)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(alias_id) DO NOTHING
                        """,
                        (f"alias-{hashlib.sha1((record.factor_id + alias).encode('utf-8')).hexdigest()[:16]}", record.factor_id, alias, "zh-CN"),
                    )

    def search_factors(
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
    ) -> tuple[list[dict], int]:
        where = ["r.is_enabled = " + ("TRUE" if self.backend_kind == "postgresql" else "1")]
        params: list = []
        p = self.placeholder
        if q:
            like = f"%{q.strip()}%"
            where.append(
                "(r.name LIKE {p} OR r.category LIKE {p} OR r.region_name LIKE {p} OR r.metadata_json LIKE {p} OR EXISTS (SELECT 1 FROM carbon_factor_aliases a WHERE a.factor_id = r.factor_id AND a.alias LIKE {p}))".format(p=p)
            )
            params.extend([like, like, like, like, like])
        if category:
            where.append(f"r.category = {p}")
            params.append(category)
        if industry:
            where.append(f"r.industry = {p}")
            params.append(industry)
        if region:
            where.append(f"(r.region = {p} OR r.region_code = {p} OR r.region_name = {p})")
            params.extend([region, region, region])
        if year is not None:
            where.append(f"r.year = {p}")
            params.append(year)
        if source_type:
            where.append(f"s.source_type = {p}")
            params.append(source_type)
        if quality:
            where.append(f"r.quality = {p}")
            params.append(quality)
        if unit:
            where.append(f"(r.factor_unit = {p} OR r.activity_unit = {p} OR r.co2e_unit = {p})")
            params.extend([unit, unit, unit])
        where_sql = " AND ".join(where)
        offset = max(page - 1, 0) * page_size
        select_sql = f"""
            SELECT r.*, s.source_id AS source_source_id, s.title AS source_title, s.publisher AS source_publisher,
                   s.source_url AS source_source_url, s.license AS source_license,
                   s.published_year AS source_published_year, s.source_type AS source_source_type,
                   s.created_at AS source_created_at, s.updated_at AS source_updated_at
            FROM carbon_factor_records r
            LEFT JOIN carbon_factor_sources s ON s.source_id = r.source_id
            WHERE {where_sql}
            ORDER BY r.year DESC, r.updated_at DESC, r.factor_seq DESC
            LIMIT {p} OFFSET {p}
        """
        count_sql = f"""
            SELECT COUNT(*) AS count
            FROM carbon_factor_records r
            LEFT JOIN carbon_factor_sources s ON s.source_id = r.source_id
            WHERE {where_sql}
        """
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(count_sql, tuple(params))
                    total = int(cursor.fetchone()["count"])
                    cursor.execute(select_sql, tuple([*params, page_size, offset]))
                    rows = cursor.fetchall()
        else:
            with self._connect() as connection:
                total = int(connection.execute(count_sql, params).fetchone()["count"])
                rows = connection.execute(select_sql, [*params, page_size, offset]).fetchall()
        return [row_to_dict(row) for row in rows], total

    def search_catalog_entries(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        industry: str | None = None,
        year: int | None = None,
        value_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where = ["1 = 1"]
        params: list = []
        p = self.placeholder
        if q:
            like = f"%{q.strip()}%"
            where.append(f"(name LIKE {p} OR category LIKE {p} OR industry LIKE {p} OR source_title LIKE {p} OR publisher LIKE {p} OR metadata_json LIKE {p})")
            params.extend([like, like, like, like, like, like])
        if category:
            where.append(f"category = {p}")
            params.append(category)
        if industry:
            where.append(f"industry = {p}")
            params.append(industry)
        if year is not None:
            where.append(f"year = {p}")
            params.append(year)
        if value_status:
            where.append(f"value_status = {p}")
            params.append(value_status)
        where_sql = " AND ".join(where)
        offset = max(page - 1, 0) * page_size
        count_sql = f"SELECT COUNT(*) AS count FROM carbon_factor_catalog_entries WHERE {where_sql}"
        select_sql = f"""
            SELECT *
            FROM carbon_factor_catalog_entries
            WHERE {where_sql}
            ORDER BY is_calculation_ready DESC, year DESC, updated_at DESC, entry_id ASC
            LIMIT {p} OFFSET {p}
        """
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(count_sql, tuple(params))
                    total = int(cursor.fetchone()["count"])
                    cursor.execute(select_sql, tuple([*params, page_size, offset]))
                    rows = cursor.fetchall()
        else:
            with self._connect() as connection:
                total = int(connection.execute(count_sql, params).fetchone()["count"])
                rows = connection.execute(select_sql, [*params, page_size, offset]).fetchall()
        return [row_to_dict(row) for row in rows], total

    def get_factor(self, *, factor_id: str) -> dict | None:
        p = self.placeholder
        sql = f"""
            SELECT r.*, s.source_id AS source_source_id, s.title AS source_title, s.publisher AS source_publisher,
                   s.source_url AS source_source_url, s.license AS source_license,
                   s.published_year AS source_published_year, s.source_type AS source_source_type,
                   s.created_at AS source_created_at, s.updated_at AS source_updated_at
            FROM carbon_factor_records r
            LEFT JOIN carbon_factor_sources s ON s.source_id = r.source_id
            WHERE r.factor_id = {p}
        """
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(sql, (factor_id,))
                    row = cursor.fetchone()
            else:
                row = connection.execute(sql, (factor_id,)).fetchone()
        return row_to_dict(row) if row else None

    def list_aliases(self, *, factor_id: str) -> list[str]:
        p = self.placeholder
        sql = f"SELECT alias FROM carbon_factor_aliases WHERE factor_id = {p} ORDER BY alias"
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(sql, (factor_id,))
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(sql, (factor_id,)).fetchall()
        return [row["alias"] for row in rows]

    def list_sources(self) -> list[dict]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM carbon_factor_sources ORDER BY updated_at DESC")
                    rows = cursor.fetchall()
            else:
                rows = connection.execute("SELECT * FROM carbon_factor_sources ORDER BY updated_at DESC").fetchall()
        return [row_to_dict(row) for row in rows]

    def facets(self) -> dict[str, list]:
        def fetch(column: str) -> list:
            sql = f"SELECT DISTINCT {column} AS value FROM carbon_factor_records WHERE {column} IS NOT NULL AND {column} <> '' ORDER BY {column}"
            with self._connect() as connection:
                if self.backend_kind == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        rows = cursor.fetchall()
                else:
                    rows = connection.execute(sql).fetchall()
            return [row["value"] for row in rows]

        source_types = []
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT source_type AS value FROM carbon_factor_sources ORDER BY source_type")
                    source_types = [row["value"] for row in cursor.fetchall()]
            else:
                source_types = [row["value"] for row in connection.execute("SELECT DISTINCT source_type AS value FROM carbon_factor_sources ORDER BY source_type").fetchall()]

        return {
            "categories": fetch("category"),
            "industries": fetch("industry"),
            "regions": fetch("region_name"),
            "years": [int(value) for value in fetch("year")],
            "source_types": source_types,
            "qualities": fetch("quality"),
        }

    def set_factor_enabled(self, *, factor_id: str, is_enabled: bool | None, quality: str | None = None) -> bool:
        updates = []
        params: list = []
        p = self.placeholder
        if is_enabled is not None:
            updates.append(f"is_enabled = {p}")
            params.append(is_enabled if self.backend_kind == "postgresql" else int(is_enabled))
        if quality is not None:
            updates.append(f"quality = {p}")
            params.append(quality)
        updates.append(f"updated_at = {p}")
        params.append(utc_now())
        params.append(factor_id)
        if not updates:
            return self.get_factor(factor_id=factor_id) is not None
        sql = f"UPDATE carbon_factor_records SET {', '.join(updates)} WHERE factor_id = {p}"
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(sql, tuple(params))
                    return cursor.rowcount > 0
            cursor = connection.execute(sql, params)
            return cursor.rowcount > 0

    def create_import_job(self, *, owner_user_id: str, source_kind: str, status: str, summary: dict, error_message: str | None = None) -> dict:
        now = utc_now()
        job_id = f"carbon-factor-import-{uuid4().hex}"
        summary_json = json.dumps(summary, ensure_ascii=False)
        params = (job_id, owner_user_id, source_kind, status, summary_json, error_message, now, now)
        if self.backend_kind == "postgresql":
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO carbon_factor_import_jobs (
                            job_id, owner_user_id, source_kind, status, summary_json, error_message, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        params,
                    )
        else:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO carbon_factor_import_jobs (
                        job_id, owner_user_id, source_kind, status, summary_json, error_message, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    params,
                )
        return {
            "job_id": job_id,
            "source_kind": source_kind,
            "status": status,
            "summary_json": summary_json,
            "error_message": error_message,
            "created_at": now,
            "updated_at": now,
        }

    def list_import_jobs(self) -> list[dict]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM carbon_factor_import_jobs ORDER BY created_at DESC LIMIT 100")
                    rows = cursor.fetchall()
            else:
                rows = connection.execute("SELECT * FROM carbon_factor_import_jobs ORDER BY created_at DESC LIMIT 100").fetchall()
        return [row_to_dict(row) for row in rows]

    def list_enabled_factor_records(self) -> list[FactorRecord]:
        rows, _ = self.search_factors(page=1, page_size=10000)
        return [self.row_to_factor_record(row) for row in rows]

    @staticmethod
    def row_to_factor_record(row: dict) -> FactorRecord:
        metadata = json.loads(row.get("metadata_json") or "{}")
        return FactorRecord(
            factor_id=row["factor_id"],
            factor_version=row["version"],
            source_type=metadata.get("source_type") or row.get("source_source_type") or row["quality"],
            source_name=metadata.get("source_name") or row.get("source_title") or "CarbonRag 碳因子库",
            source_url=metadata.get("source_url") or row.get("source_source_url"),
            scope=row["scope"],
            activity_category=row["category"],
            activity_name=metadata.get("activity_name") or row["name"],
            region=row.get("region"),
            region_level=row.get("region_level"),
            region_code=row.get("region_code"),
            region_name=row.get("region_name"),
            year=row.get("year"),
            effective_year=row.get("effective_year"),
            method_type=row.get("method_type") or metadata.get("method_type"),
            source_priority=metadata.get("source_priority") or 0,
            applicable_industry=row.get("industry"),
            applicable_standard=metadata.get("applicable_standard"),
            quality_level=metadata.get("quality_level") or row.get("quality"),
            is_official=bool(metadata.get("is_official")),
            factor_value=float(row["factor_value"]),
            factor_unit=row["factor_unit"],
            activity_unit=row["activity_unit"],
            result_unit=row["co2e_unit"],
            is_default=bool(metadata.get("is_default")),
            is_deprecated=not bool(row.get("is_enabled", True)) or bool(metadata.get("is_deprecated")),
            notes=metadata.get("notes"),
            tags=metadata.get("tags") or [],
        )


@lru_cache(maxsize=1)
def get_carbon_factor_store() -> CarbonFactorStore:
    return CarbonFactorStore()
