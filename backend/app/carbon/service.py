import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.carbon.calculator import CarbonCalculator
from app.carbon.explain import CarbonExplainer
from app.carbon.factor_loader import CarbonFactorLoader, FactorLoadError, get_factor_loader
from app.carbon.schemas import CalcCarbonRequest, CalcCarbonResponse, StoredCarbonCalculation
from app.session.adapters.sqlite_store import SQLiteSessionStore, get_session_store
from app.session.service import SessionService, get_session_service


class CarbonService:
    def __init__(
        self,
        *,
        factor_loader: CarbonFactorLoader | None = None,
        calculator: CarbonCalculator | None = None,
        explainer: CarbonExplainer | None = None,
        session_service: SessionService | None = None,
        store: SQLiteSessionStore | None = None,
    ) -> None:
        self.factor_loader = factor_loader or get_factor_loader()
        self.calculator = calculator or CarbonCalculator()
        self.explainer = explainer or CarbonExplainer()
        self.session_service = session_service or get_session_service()
        self.store = store or get_session_store()
        self.db_path = Path(self.store.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS carbon_calculations (
                    calculation_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL UNIQUE,
                    session_id TEXT,
                    period_label TEXT,
                    electricity_kwh REAL NOT NULL,
                    natural_gas_m3 REAL NOT NULL,
                    diesel_l REAL NOT NULL,
                    total_emission_kgco2e REAL NOT NULL,
                    breakdown_json TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_carbon_calculations_session_created_at
                ON carbon_calculations(session_id, created_at DESC)
                """
            )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def calculate(self, payload: CalcCarbonRequest) -> CalcCarbonResponse:
        if payload.session_id is not None and self.session_service.get_session(payload.session_id) is None:
            raise KeyError(f"Unknown session: {payload.session_id}")

        factors = self.factor_loader.load()
        breakdown, total = self.calculator.calculate(request=payload, factors=factors)
        citations = self.explainer.build_citations(factors)
        formula_summary = self.explainer.build_formula_summary(breakdown)
        trace_id = f"calc-{uuid4().hex[:12]}"

        self._persist(
            StoredCarbonCalculation(
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
            )
        )

        return CalcCarbonResponse(
            status="ok",
            trace_id=trace_id,
            total_emission_kgco2e=total,
            breakdown=breakdown,
            formula_summary=formula_summary,
            citations=citations,
        )

    def _persist(self, calculation: StoredCarbonCalculation) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO carbon_calculations (
                    trace_id,
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    calculation.trace_id,
                    calculation.session_id,
                    calculation.period_label,
                    calculation.electricity_kwh,
                    calculation.natural_gas_m3,
                    calculation.diesel_l,
                    calculation.total_emission_kgco2e,
                    json.dumps([item.model_dump() for item in calculation.breakdown], ensure_ascii=False),
                    json.dumps([item.model_dump() for item in calculation.citations], ensure_ascii=False),
                    calculation.created_at.isoformat(),
                ),
            )

    def get_stored_calculation(self, trace_id: str) -> StoredCarbonCalculation | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM carbon_calculations
                WHERE trace_id = ?
                """,
                (trace_id,),
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


def get_carbon_service() -> CarbonService:
    return CarbonService()
