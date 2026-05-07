import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.carbon.calculator import CarbonCalculator
from app.carbon.explain import CarbonExplainer
from app.carbon.factor_loader import CarbonFactorLoader, get_factor_loader
from app.carbon.engine import CarbonCalculationEngine
from app.carbon.schemas import (
    CarbonActivityBatch,
    CarbonActivityItem,
    CalcCarbonRequest,
    CalcCarbonResponse,
    CarbonCalculationSummary,
    CarbonScopeSummary,
    StoredCarbonCalculation,
)
from app.core.config import get_settings
from app.runtime_db.compat import connect_postgres
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.session.service import SessionService, get_session_service
from app.session.store import DEFAULT_SESSION_DB_PATH, SessionStore, get_session_store


class CarbonService:
    def __init__(
        self,
        *,
        factor_loader: CarbonFactorLoader | None = None,
        calculator: CarbonCalculator | None = None,
        explainer: CarbonExplainer | None = None,
        session_service: SessionService | None = None,
        store: SessionStore | None = None,
        database_url: str | None = None,
        sqlite_db_path: Path | str | None = None,
    ) -> None:
        self.factor_loader = factor_loader or get_factor_loader()
        self.calculator = calculator or CarbonCalculator()
        self.explainer = explainer or CarbonExplainer()
        self.session_service = session_service or get_session_service()
        self.store = store or get_session_store()
        settings = get_settings()
        self.database_url = database_url or getattr(self.store, "database_url", None) or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or getattr(self.store, "db_path", DEFAULT_SESSION_DB_PATH))
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(
            database_url=self.database_url,
            sqlite_db_path=self.sqlite_db_path,
        )

    def _connect(self):
        if self.backend_kind == "postgresql":
            return connect_postgres(self.database_url)

        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def calculate(self, *, owner_user_id: str, payload: CalcCarbonRequest) -> CalcCarbonResponse:
        if payload.session_id is not None:
            self.session_service.require_session(owner_user_id=owner_user_id, session_id=payload.session_id)

        registry = self.factor_loader.load_registry()
        activity_batch = payload.to_activity_batch()
        engine_result = CarbonCalculationEngine(registry=registry).calculate(activity_batch)
        formula_summary = self.explainer.build_formula_summary_from_trace(engine_result.formula_trace)
        trace_id = f"calc-{uuid4().hex[:12]}"
        inventory_id = f"inv-{uuid4().hex[:12]}"
        created_at = self._utcnow()
        raw_activity_items = [
            item.model_dump(mode="json")
            for item in activity_batch.activity_items
        ]

        self._persist(
            owner_user_id=owner_user_id,
            payload=payload,
            activity_batch=activity_batch,
            calculation=StoredCarbonCalculation(
                trace_id=trace_id,
                inventory_id=inventory_id,
                session_id=payload.session_id,
                period_label=payload.period_label,
                electricity_kwh=payload.electricity_kwh,
                natural_gas_m3=payload.natural_gas_m3,
                diesel_l=payload.diesel_l,
                total_emission_kgco2e=engine_result.total_emission_kgco2e,
                total_kgco2e=engine_result.total_emission_kgco2e,
                scope_summary=engine_result.scope_summary,
                activity_count=engine_result.activity_count,
                official_factor_count=engine_result.official_factor_count,
                fallback_factor_count=engine_result.fallback_factor_count,
                activity_items_raw=raw_activity_items,
                breakdown=engine_result.breakdown,
                citations=engine_result.citations,
                factor_snapshot=engine_result.factor_snapshot,
                unit_conversion_trace=engine_result.unit_conversion_trace,
                formula_trace=engine_result.formula_trace,
                source_summary=engine_result.source_summary,
                warnings=engine_result.warnings,
                created_at=created_at,
            ),
        )

        return CalcCarbonResponse(
            status="ok",
            trace_id=trace_id,
            inventory_id=inventory_id,
            total_emission_kgco2e=engine_result.total_emission_kgco2e,
            total_kgco2e=engine_result.total_emission_kgco2e,
            breakdown=engine_result.breakdown,
            formula_summary=formula_summary,
            citations=engine_result.citations,
            scope_summary=engine_result.scope_summary,
            activity_count=engine_result.activity_count,
            official_factor_count=engine_result.official_factor_count,
            fallback_factor_count=engine_result.fallback_factor_count,
            factor_snapshot=engine_result.factor_snapshot,
            unit_conversion_trace=engine_result.unit_conversion_trace,
            formula_trace=engine_result.formula_trace,
            source_summary=engine_result.source_summary,
            warnings=engine_result.warnings,
        )

    def _persist(
        self,
        *,
        owner_user_id: str,
        payload: CalcCarbonRequest,
        activity_batch: CarbonActivityBatch,
        calculation: StoredCarbonCalculation,
    ) -> None:
        breakdown_json = json.dumps([item.model_dump() for item in calculation.breakdown], ensure_ascii=False)
        citations_json = json.dumps([item.model_dump() for item in calculation.citations], ensure_ascii=False)
        factor_snapshot_json = json.dumps([item.model_dump() for item in calculation.factor_snapshot], ensure_ascii=False)
        unit_conversion_trace_json = json.dumps(
            [item.model_dump() for item in calculation.unit_conversion_trace],
            ensure_ascii=False,
        )
        formula_trace_json = json.dumps([item.model_dump() for item in calculation.formula_trace], ensure_ascii=False)
        source_summary_json = json.dumps([item.model_dump() for item in calculation.source_summary], ensure_ascii=False)
        warnings_json = json.dumps(calculation.warnings, ensure_ascii=False)
        activity_items_raw_json = json.dumps(calculation.activity_items_raw, ensure_ascii=False)
        scope_summary_json = calculation.scope_summary.model_dump_json()
        raw_payload_json = payload.model_dump_json()

        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    self._persist_inventory_postgres(
                        cursor=cursor,
                        owner_user_id=owner_user_id,
                        payload=payload,
                        activity_batch=activity_batch,
                        calculation=calculation,
                        raw_payload_json=raw_payload_json,
                    )
                    cursor.execute(
                        """
                        INSERT INTO carbon_calculations (
                            trace_id,
                            inventory_id,
                            owner_user_id,
                            session_id,
                            period_label,
                            electricity_kwh,
                            natural_gas_m3,
                            diesel_l,
                            total_emission_kgco2e,
                            breakdown_json,
                            citations_json,
                            factor_snapshot_json,
                            unit_conversion_trace_json,
                            formula_trace_json,
                            source_summary_json,
                            warnings_json,
                            activity_items_raw_json,
                            scope_summary_json,
                            activity_count,
                            official_factor_count,
                            fallback_factor_count,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            calculation.trace_id,
                            calculation.inventory_id,
                            owner_user_id,
                            calculation.session_id,
                            calculation.period_label,
                            calculation.electricity_kwh,
                            calculation.natural_gas_m3,
                            calculation.diesel_l,
                            calculation.total_emission_kgco2e,
                            breakdown_json,
                            citations_json,
                            factor_snapshot_json,
                            unit_conversion_trace_json,
                            formula_trace_json,
                            source_summary_json,
                            warnings_json,
                            activity_items_raw_json,
                            scope_summary_json,
                            calculation.activity_count,
                            calculation.official_factor_count,
                            calculation.fallback_factor_count,
                            calculation.created_at.isoformat(),
                        ),
                    )
            else:
                self._persist_inventory_sqlite(
                    connection=connection,
                    owner_user_id=owner_user_id,
                    payload=payload,
                    activity_batch=activity_batch,
                    calculation=calculation,
                    raw_payload_json=raw_payload_json,
                )
                connection.execute(
                    """
                    INSERT INTO carbon_calculations (
                        trace_id,
                        inventory_id,
                        owner_user_id,
                        session_id,
                        period_label,
                        electricity_kwh,
                        natural_gas_m3,
                        diesel_l,
                        total_emission_kgco2e,
                        breakdown_json,
                        citations_json,
                        factor_snapshot_json,
                        unit_conversion_trace_json,
                        formula_trace_json,
                        source_summary_json,
                        warnings_json,
                        activity_items_raw_json,
                        scope_summary_json,
                        activity_count,
                        official_factor_count,
                        fallback_factor_count,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        calculation.trace_id,
                        calculation.inventory_id,
                        owner_user_id,
                        calculation.session_id,
                        calculation.period_label,
                        calculation.electricity_kwh,
                        calculation.natural_gas_m3,
                        calculation.diesel_l,
                        calculation.total_emission_kgco2e,
                        breakdown_json,
                        citations_json,
                        factor_snapshot_json,
                        unit_conversion_trace_json,
                        formula_trace_json,
                        source_summary_json,
                        warnings_json,
                        activity_items_raw_json,
                        scope_summary_json,
                        calculation.activity_count,
                        calculation.official_factor_count,
                        calculation.fallback_factor_count,
                        calculation.created_at.isoformat(),
                    ),
                )

    def _persist_inventory_sqlite(
        self,
        *,
        connection: sqlite3.Connection,
        owner_user_id: str,
        payload: CalcCarbonRequest,
        activity_batch: CarbonActivityBatch,
        calculation: StoredCarbonCalculation,
        raw_payload_json: str,
    ) -> None:
        self._persist_inventory_common(
            executor=connection,
            placeholder="?",
            owner_user_id=owner_user_id,
            payload=payload,
            activity_batch=activity_batch,
            calculation=calculation,
            raw_payload_json=raw_payload_json,
        )

    def _persist_inventory_postgres(
        self,
        *,
        cursor,
        owner_user_id: str,
        payload: CalcCarbonRequest,
        activity_batch: CarbonActivityBatch,
        calculation: StoredCarbonCalculation,
        raw_payload_json: str,
    ) -> None:
        self._persist_inventory_common(
            executor=cursor,
            placeholder="%s",
            owner_user_id=owner_user_id,
            payload=payload,
            activity_batch=activity_batch,
            calculation=calculation,
            raw_payload_json=raw_payload_json,
        )

    def _persist_inventory_common(
        self,
        *,
        executor,
        placeholder: str,
        owner_user_id: str,
        payload: CalcCarbonRequest,
        activity_batch: CarbonActivityBatch,
        calculation: StoredCarbonCalculation,
        raw_payload_json: str,
    ) -> None:
        q = placeholder
        activity_items_raw_json = json.dumps(calculation.activity_items_raw, ensure_ascii=False)
        scope_summary_json = calculation.scope_summary.model_dump_json()
        values = (
            calculation.inventory_id,
            owner_user_id,
            calculation.session_id,
            payload.organization_id,
            payload.facility_id,
            payload.period_start.isoformat() if payload.period_start else None,
            payload.period_end.isoformat() if payload.period_end else None,
            activity_batch.inventory_standard,
            "factor_driven_v2",
            calculation.trace_id,
            activity_items_raw_json,
            raw_payload_json,
            calculation.total_emission_kgco2e,
            scope_summary_json,
            calculation.activity_count,
            calculation.official_factor_count,
            calculation.fallback_factor_count,
            json.dumps(calculation.warnings, ensure_ascii=False),
            calculation.created_at.isoformat(),
            calculation.created_at.isoformat(),
        )
        executor.execute(
            f"""
            INSERT INTO carbon_inventories (
                inventory_id,
                owner_user_id,
                session_id,
                organization_id,
                facility_id,
                period_start,
                period_end,
                inventory_standard,
                calculation_method,
                trace_id,
                activity_items_raw_json,
                raw_payload_json,
                total_kgco2e,
                scope_summary_json,
                activity_count,
                official_factor_count,
                fallback_factor_count,
                warnings_json,
                created_at,
                updated_at
            )
            VALUES ({", ".join([q] * 20)})
            """,
            values,
        )

        activity_ids: list[str] = []
        for index, activity in enumerate(activity_batch.activity_items):
            activity_id = f"act-{uuid4().hex[:12]}"
            activity_ids.append(activity_id)
            self._execute_insert(
                executor,
                placeholder,
                "carbon_activity_items",
                (
                    "activity_item_id",
                    "inventory_id",
                    "order_index",
                    "scope",
                    "activity_category",
                    "activity_name",
                    "activity_value",
                    "activity_unit",
                    "region",
                    "province",
                    "year",
                    "data_quality",
                    "evidence_reference",
                    "source_document_id",
                    "entry_method",
                    "requested_factor_id",
                    "raw_payload_json",
                    "created_at",
                ),
                (
                    activity_id,
                    calculation.inventory_id,
                    index,
                    activity.scope,
                    activity.activity_category,
                    activity.activity_name,
                    activity.activity_value,
                    activity.activity_unit,
                    activity.region,
                    activity.province,
                    activity.year,
                    activity.data_quality,
                    activity.evidence_reference,
                    activity.source_document_id,
                    activity.entry_method,
                    activity.requested_factor_id,
                    activity.model_dump_json(),
                    calculation.created_at.isoformat(),
                ),
            )
            self._execute_insert(
                executor,
                placeholder,
                "carbon_evidence_references",
                (
                    "evidence_id",
                    "inventory_id",
                    "activity_item_id",
                    "data_quality",
                    "evidence_reference",
                    "source_document_id",
                    "entry_method",
                    "created_at",
                ),
                (
                    f"evd-{uuid4().hex[:12]}",
                    calculation.inventory_id,
                    activity_id,
                    activity.data_quality,
                    activity.evidence_reference,
                    activity.source_document_id,
                    activity.entry_method,
                    calculation.created_at.isoformat(),
                ),
            )

        positive_activity_ids = [
            activity_id
            for activity_id, activity in zip(activity_ids, activity_batch.activity_items, strict=False)
            if activity.activity_value > 0
        ]
        for index, breakdown in enumerate(calculation.breakdown):
            line_id = f"line-{uuid4().hex[:12]}"
            activity_id = positive_activity_ids[index] if index < len(positive_activity_ids) else None
            self._execute_insert(
                executor,
                placeholder,
                "carbon_calculation_lines",
                (
                    "line_id",
                    "inventory_id",
                    "activity_item_id",
                    "scope",
                    "activity_category",
                    "activity_name",
                    "emission_kgco2e",
                    "factor_id",
                    "line_payload_json",
                    "created_at",
                ),
                (
                    line_id,
                    calculation.inventory_id,
                    activity_id,
                    breakdown.scope,
                    breakdown.activity_category,
                    breakdown.activity_name,
                    breakdown.emission_kgco2e,
                    breakdown.factor_id,
                    breakdown.model_dump_json(),
                    calculation.created_at.isoformat(),
                ),
            )

        for snapshot in calculation.factor_snapshot:
            self._execute_insert(
                executor,
                placeholder,
                "carbon_factor_snapshots",
                (
                    "factor_snapshot_id",
                    "inventory_id",
                    "factor_id",
                    "factor_version",
                    "source_type",
                    "source_name",
                    "source_url",
                    "factor_value",
                    "factor_unit",
                    "activity_unit",
                    "result_unit",
                    "snapshot_json",
                    "created_at",
                ),
                (
                    f"fs-{uuid4().hex[:12]}",
                    calculation.inventory_id,
                    snapshot.factor_id,
                    snapshot.factor_version,
                    snapshot.source_type,
                    snapshot.source_name,
                    snapshot.source_url,
                    snapshot.factor_value,
                    snapshot.factor_unit,
                    snapshot.activity_unit,
                    snapshot.result_unit,
                    snapshot.model_dump_json(),
                    calculation.created_at.isoformat(),
                ),
            )

        self._execute_insert(
            executor,
            placeholder,
            "carbon_inventory_summaries",
            (
                "inventory_id",
                "scope_summary_json",
                "activity_count",
                "official_factor_count",
                "fallback_factor_count",
                "warnings_json",
                "created_at",
            ),
            (
                calculation.inventory_id,
                scope_summary_json,
                calculation.activity_count,
                calculation.official_factor_count,
                calculation.fallback_factor_count,
                json.dumps(calculation.warnings, ensure_ascii=False),
                calculation.created_at.isoformat(),
            ),
        )

    @staticmethod
    def _execute_insert(executor, placeholder: str, table: str, columns: tuple[str, ...], values: tuple) -> None:
        placeholders = ", ".join([placeholder] * len(columns))
        column_list = ", ".join(columns)
        executor.execute(
            f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
            values,
        )

    def get_stored_calculation(self, *, owner_user_id: str, trace_id: str) -> StoredCarbonCalculation | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                        FROM carbon_calculations
                        WHERE trace_id = %s
                          AND owner_user_id = %s
                        """,
                        (trace_id, owner_user_id),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT *
                    FROM carbon_calculations
                    WHERE trace_id = ?
                      AND owner_user_id = ?
                    """,
                    (trace_id, owner_user_id),
                ).fetchone()

        if row is None:
            return None

        payload = dict(row)
        return StoredCarbonCalculation(
            trace_id=payload["trace_id"],
            inventory_id=payload.get("inventory_id"),
            session_id=payload["session_id"],
            period_label=payload["period_label"],
            electricity_kwh=payload["electricity_kwh"],
            natural_gas_m3=payload["natural_gas_m3"],
            diesel_l=payload["diesel_l"],
            total_emission_kgco2e=payload["total_emission_kgco2e"],
            total_kgco2e=payload.get("total_emission_kgco2e"),
            scope_summary=CarbonScopeSummary.model_validate_json(payload.get("scope_summary_json") or "{}"),
            activity_count=payload.get("activity_count") or 0,
            official_factor_count=payload.get("official_factor_count") or 0,
            fallback_factor_count=payload.get("fallback_factor_count") or 0,
            activity_items_raw=json.loads(payload.get("activity_items_raw_json") or "[]"),
            breakdown=json.loads(payload["breakdown_json"]),
            citations=json.loads(payload["citations_json"]),
            factor_snapshot=json.loads(payload.get("factor_snapshot_json") or "[]"),
            unit_conversion_trace=json.loads(payload.get("unit_conversion_trace_json") or "[]"),
            formula_trace=json.loads(payload.get("formula_trace_json") or "[]"),
            source_summary=json.loads(payload.get("source_summary_json") or "[]"),
            warnings=json.loads(payload.get("warnings_json") or "[]"),
            created_at=datetime.fromisoformat(payload["created_at"]),
        )

    def list_session_calculations(self, *, owner_user_id: str, session_id: str) -> list[CarbonCalculationSummary]:
        self.session_service.require_session(owner_user_id=owner_user_id, session_id=session_id)
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT trace_id, period_label, total_emission_kgco2e, created_at
                        FROM carbon_calculations
                        WHERE session_id = %s
                          AND owner_user_id = %s
                        ORDER BY created_at DESC
                        """,
                        (session_id, owner_user_id),
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT trace_id, period_label, total_emission_kgco2e, created_at
                    FROM carbon_calculations
                    WHERE session_id = ?
                      AND owner_user_id = ?
                    ORDER BY created_at DESC
                    """,
                    (session_id, owner_user_id),
                ).fetchall()

        return [
            CarbonCalculationSummary(
                trace_id=row["trace_id"],
                period_label=row["period_label"],
                total_emission_kgco2e=row["total_emission_kgco2e"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


def get_carbon_service() -> CarbonService:
    return CarbonService()
