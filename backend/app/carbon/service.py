import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.carbon.calculator import CarbonCalculator
from app.carbon.explain import CarbonExplainer
from app.carbon.factor_loader import CarbonFactorLoader, get_factor_loader
from app.carbon.schemas import (
    CalcCarbonRequest,
    CalcCarbonResponse,
    CarbonCalculationSummary,
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

        factors = self.factor_loader.load()
        breakdown, total = self.calculator.calculate(request=payload, factors=factors)
        citations = self.explainer.build_citations(factors)
        formula_summary = self.explainer.build_formula_summary(breakdown)
        trace_id = f"calc-{uuid4().hex[:12]}"

        self._persist(
            owner_user_id=owner_user_id,
            calculation=StoredCarbonCalculation(
                trace_id=trace_id,
                session_id=payload.session_id,
                period_label=payload.period_label,
                electricity_kwh=payload.electricity_kwh,
                natural_gas_m3=payload.natural_gas_m3,
                diesel_l=payload.diesel_l,
                total_emission_kgco2e=total,
                breakdown=breakdown,
                citations=citations,
                created_at=self._utcnow(),
            ),
        )

        return CalcCarbonResponse(
            status="ok",
            trace_id=trace_id,
            total_emission_kgco2e=total,
            breakdown=breakdown,
            formula_summary=formula_summary,
            citations=citations,
        )

    def _persist(self, *, owner_user_id: str, calculation: StoredCarbonCalculation) -> None:
        breakdown_json = json.dumps([item.model_dump() for item in calculation.breakdown], ensure_ascii=False)
        citations_json = json.dumps([item.model_dump() for item in calculation.citations], ensure_ascii=False)

        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO carbon_calculations (
                            trace_id,
                            owner_user_id,
                            session_id,
                            period_label,
                            electricity_kwh,
                            natural_gas_m3,
                            diesel_l,
                            total_emission_kgco2e,
                            breakdown_json,
                            citations_json,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            calculation.trace_id,
                            owner_user_id,
                            calculation.session_id,
                            calculation.period_label,
                            calculation.electricity_kwh,
                            calculation.natural_gas_m3,
                            calculation.diesel_l,
                            calculation.total_emission_kgco2e,
                            breakdown_json,
                            citations_json,
                            calculation.created_at.isoformat(),
                        ),
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO carbon_calculations (
                        trace_id,
                        owner_user_id,
                        session_id,
                        period_label,
                        electricity_kwh,
                        natural_gas_m3,
                        diesel_l,
                        total_emission_kgco2e,
                        breakdown_json,
                        citations_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        calculation.trace_id,
                        owner_user_id,
                        calculation.session_id,
                        calculation.period_label,
                        calculation.electricity_kwh,
                        calculation.natural_gas_m3,
                        calculation.diesel_l,
                        calculation.total_emission_kgco2e,
                        breakdown_json,
                        citations_json,
                        calculation.created_at.isoformat(),
                    ),
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
            session_id=payload["session_id"],
            period_label=payload["period_label"],
            electricity_kwh=payload["electricity_kwh"],
            natural_gas_m3=payload["natural_gas_m3"],
            diesel_l=payload["diesel_l"],
            total_emission_kgco2e=payload["total_emission_kgco2e"],
            breakdown=json.loads(payload["breakdown_json"]),
            citations=json.loads(payload["citations_json"]),
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
