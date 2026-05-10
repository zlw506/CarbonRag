from __future__ import annotations

import json
import logging
import base64
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.knowledge.policy_ingestion import (
    DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS,
    CrawledDocument,
    CrawlerProvider,
    PolicyCrawlRequest,
    ScrapydCrawlerProvider,
    ScrapyCrawlerProvider,
    is_allowed_policy_url,
)
from app.rag.contracts import hash_content
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.runtime_db.compat import connect_postgres
from app.session.store import DEFAULT_SESSION_DB_PATH

logger = logging.getLogger(__name__)

PolicyCrawlRunStatus = Literal["running", "succeeded", "failed", "disabled", "unavailable", "rejected", "skipped"]
PolicyCrawlCandidateStatus = Literal["pending_review", "published", "rejected"]


class PolicyCrawlerBusyError(RuntimeError):
    pass


class PolicyCrawlerSource(BaseModel):
    source_id: str
    title: str
    source_url: str
    source_label: str
    allowed_domain: str
    is_enabled: bool = True
    schedule_interval_seconds: int | None = None
    last_run_id: str | None = None
    last_run_status: str | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyCrawlerRun(BaseModel):
    run_id: str
    source_id: str
    trigger_type: str
    triggered_by_user_id: str | None = None
    status: PolicyCrawlRunStatus
    provider_name: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    document_count: int = 0
    candidate_count: int = 0
    error_detail: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyCrawlerCandidate(BaseModel):
    candidate_id: str
    run_id: str
    source_id: str
    url: str
    title: str | None = None
    content_type: str
    content_hash: str
    source_name: str | None = None
    fetched_at: datetime | None = None
    storage_path: str
    status: PolicyCrawlCandidateStatus = "pending_review"
    reviewed_by_user_id: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    knowledge_item_id: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyCrawlerStatus(BaseModel):
    scheduler_started: bool
    scheduled_enabled: bool
    manual_enabled: bool
    auto_publish_enabled: bool
    running: bool
    crawler_backend: str
    provider_name: str
    provider_mode: str
    provider_enabled: bool
    provider_available: bool
    local_scrapy_available: bool | None = None
    scrapyd_available: bool | None = None
    scrapyd_endpoint_label: str | None = None
    provider_error: str | None = None
    external_job_id: str | None = None
    interval_seconds: int
    initial_delay_seconds: float
    source_count: int = 0
    pending_candidate_count: int = 0
    recent_run_status: str | None = None
    safe_limits: dict[str, Any] = Field(default_factory=dict)


LEGACY_MOJIBAKE_POLICY_CRAWL_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "source_id": "gov-cn-policy-library",
        "title": "中国政府网：2030年前碳达峰行动方案",
        "source_url": "https://www.gov.cn/zhengce/content/2021-10/26/content_5644984.htm",
        "source_label": "中国政府网",
        "allowed_domain": "gov.cn",
        "metadata": {"scope": "national_policy", "topic": "carbon_peak"},
    },
    {
        "source_id": "ndrc-policy-releases",
        "title": "国家发展改革委政策发布",
        "source_url": "https://www.ndrc.gov.cn/xxgk/zcfb/",
        "source_label": "国家发展改革委",
        "allowed_domain": "ndrc.gov.cn",
        "metadata": {"scope": "national_policy"},
    },
    {
        "source_id": "mee-policy-releases",
        "title": "生态环境部政策公开",
        "source_url": "https://www.mee.gov.cn/xxgklssj/",
        "source_label": "生态环境部",
        "allowed_domain": "mee.gov.cn",
        "metadata": {"scope": "environment_policy"},
    },
    {
        "source_id": "miit-policy-releases",
        "title": "工业和信息化部政策文件",
        "source_url": "https://www.miit.gov.cn/zwgk/zcwj/",
        "source_label": "工业和信息化部",
        "allowed_domain": "miit.gov.cn",
        "metadata": {"scope": "industry_policy"},
    },
    {
        "source_id": "beijing-policy-library",
        "title": "北京市政策文件",
        "source_url": "https://www.beijing.gov.cn/zhengce/",
        "source_label": "北京市人民政府",
        "allowed_domain": "beijing.gov.cn",
        "metadata": {"scope": "local_policy", "region": "北京"},
    },
    {
        "source_id": "beijing-fgw-policy",
        "title": "北京市发展改革委政策文件",
        "source_url": "https://fgw.beijing.gov.cn/fgwzwgk/2024zcwj/",
        "source_label": "北京市发展和改革委员会",
        "allowed_domain": "fgw.beijing.gov.cn",
        "metadata": {"scope": "local_policy", "region": "北京"},
    },
)


DEFAULT_POLICY_CRAWL_SOURCES = (
    {
        "source_id": "gov-cn-policy-library",
        "title": "中国政府网政策文件库",
        "source_url": "https://www.gov.cn/zhengce/",
        "source_label": "中国政府网",
        "allowed_domain": "gov.cn",
        "metadata": {
            "scope": "national_policy",
            "discovery_mode": "official_policy_search",
            "extra_start_urls": [
                "https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=%E7%A2%B3%E8%BE%BE%E5%B3%B0&t=zhengcelibrary&orpro=",
                "https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=%E5%8F%8C%E7%A2%B3&t=zhengcelibrary&orpro=",
            ],
        },
    },
    {
        "source_id": "ndrc-policy-releases",
        "title": "国家发展改革委碳达峰碳中和",
        "source_url": "https://www.ndrc.gov.cn/fggz/hjyzy/tdftzh/",
        "source_label": "国家发展改革委",
        "allowed_domain": "ndrc.gov.cn",
        "metadata": {
            "scope": "national_policy",
            "discovery_mode": "policy_listing",
            "extra_start_urls": [
                "https://www.ndrc.gov.cn/xxgk/zcfb/ghxwj/",
                "https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/",
                "https://www.ndrc.gov.cn/xxgk/zcfb/gg/",
            ],
        },
    },
    {
        "source_id": "mee-policy-releases",
        "title": "生态环境部应对气候变化",
        "source_url": "https://www.mee.gov.cn/ywgz/ydqhbh/",
        "source_label": "生态环境部",
        "allowed_domain": "mee.gov.cn",
        "metadata": {
            "scope": "environment_policy",
            "discovery_mode": "policy_listing",
            "extra_start_urls": [
                "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk03/",
                "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk06/",
                "https://www.mee.gov.cn/zcwj/zcjd/",
            ],
        },
    },
    {
        "source_id": "miit-policy-releases",
        "title": "工业和信息化部政策文件",
        "source_url": "https://www.miit.gov.cn/search/wjfb.html?websiteid=110000000000000&pg=&p=&tpl=14&category=51&q=%E8%8A%82%E8%83%BD%E9%99%8D%E7%A2%B3",
        "source_label": "工业和信息化部",
        "allowed_domain": "miit.gov.cn",
        "metadata": {
            "scope": "industry_policy",
            "discovery_mode": "official_policy_search",
            "extra_start_urls": [
                "https://www.miit.gov.cn/search/wjfb.html?websiteid=110000000000000&pg=&p=&tpl=14&category=51&q=%E7%A2%B3%E8%BE%BE%E5%B3%B0",
                "https://www.miit.gov.cn/search/wjfb.html?websiteid=110000000000000&pg=&p=&tpl=14&category=51&q=%E7%BB%BF%E8%89%B2%E5%88%B6%E9%80%A0",
            ],
        },
    },
    {
        "source_id": "beijing-policy-library",
        "title": "北京市政策文件入口",
        "source_url": "https://www.beijing.gov.cn/zhengce/",
        "source_label": "北京市人民政府",
        "allowed_domain": "beijing.gov.cn",
        "metadata": {
            "scope": "local_policy",
            "region": "北京",
            "discovery_mode": "policy_listing",
            "extra_start_urls": [
                "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
                "https://www.beijing.gov.cn/zhengce/zcjd/",
            ],
        },
    },
    {
        "source_id": "beijing-fgw-policy",
        "title": "北京市发展改革委政策文件入口",
        "source_url": "https://fgw.beijing.gov.cn/fgwzwgk/2024zcwj/",
        "source_label": "北京市发展和改革委员会",
        "allowed_domain": "fgw.beijing.gov.cn",
        "metadata": {
            "scope": "local_policy",
            "region": "北京",
            "discovery_mode": "policy_listing",
            "extra_start_urls": [
                "https://fgw.beijing.gov.cn/fgwzwgk/zcjd/",
                "https://fgw.beijing.gov.cn/fgwzwgk/tzgg/",
            ],
        },
    },
)


class PolicyCrawlerStore:
    def __init__(self, *, database_url: str | None = None, sqlite_db_path: Path | str | None = None) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    def _connect(self):
        if self.backend_kind == "postgresql":
            return connect_postgres(self.database_url)
        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def seed_default_sources(self, sources: tuple[dict[str, Any], ...] = DEFAULT_POLICY_CRAWL_SOURCES) -> list[PolicyCrawlerSource]:
        seeded: list[PolicyCrawlerSource] = []
        for source in sources:
            seeded.append(self.upsert_source(source))
        return seeded

    def upsert_source(self, payload: dict[str, Any]) -> PolicyCrawlerSource:
        now = self.utcnow()
        source_id = str(payload["source_id"])
        existing = self.get_source(source_id)
        source_url = str(payload["source_url"])
        if not is_allowed_policy_url(source_url, allowed_domains=DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS):
            raise ValueError(f"policy crawl source is outside official allowlist: {source_url}")
        domain = _host(source_url)
        allowed_domain = str(payload.get("allowed_domain") or domain)
        if not domain or not (domain == allowed_domain or domain.endswith(f".{allowed_domain}")):
            raise ValueError(f"policy crawl source domain does not match allowed domain: {source_url}")
        if existing is None:
            self._execute(
                """
                INSERT INTO policy_crawl_sources (
                    source_id, title, source_url, source_label, allowed_domain, is_enabled,
                    schedule_interval_seconds, created_at, updated_at, metadata_json
                )
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """,
                [
                    source_id,
                    payload["title"],
                    source_url,
                    payload["source_label"],
                    allowed_domain,
                    bool(payload.get("is_enabled", True)),
                    payload.get("schedule_interval_seconds"),
                    now.isoformat(),
                    now.isoformat(),
                    json.dumps(payload.get("metadata") or {}, ensure_ascii=False),
                ],
            )
        else:
            self._execute(
                """
                UPDATE policy_crawl_sources
                SET title = {p}, source_url = {p}, source_label = {p}, allowed_domain = {p},
                    is_enabled = {p}, schedule_interval_seconds = {p}, updated_at = {p}, metadata_json = {p}
                WHERE source_id = {p}
                """,
                [
                    payload["title"],
                    source_url,
                    payload["source_label"],
                    allowed_domain,
                    bool(payload.get("is_enabled", existing.is_enabled)),
                    payload.get("schedule_interval_seconds", existing.schedule_interval_seconds),
                    now.isoformat(),
                    json.dumps(payload.get("metadata") or existing.metadata, ensure_ascii=False),
                    source_id,
                ],
            )
        refreshed = self.get_source(source_id)
        if refreshed is None:
            raise RuntimeError("policy crawl source upsert failed")
        return refreshed

    def get_source(self, source_id: str) -> PolicyCrawlerSource | None:
        rows = self._select("SELECT * FROM policy_crawl_sources WHERE source_id = {p}", [source_id])
        return self._row_to_source(rows[0]) if rows else None

    def list_sources(self) -> list[PolicyCrawlerSource]:
        rows = self._select("SELECT * FROM policy_crawl_sources ORDER BY source_seq ASC", [])
        return [self._row_to_source(row) for row in rows]

    def create_run(
        self,
        *,
        source_id: str,
        trigger_type: str,
        triggered_by_user_id: str | None,
        provider_name: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyCrawlerRun:
        now = self.utcnow()
        run_id = f"pcrawl-{uuid4().hex[:12]}"
        self._execute(
            """
            INSERT INTO policy_crawl_runs (
                run_id, source_id, trigger_type, triggered_by_user_id, status, provider_name,
                started_at, metadata_json
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """,
            [
                run_id,
                source_id,
                trigger_type,
                triggered_by_user_id,
                "running",
                provider_name,
                now.isoformat(),
                json.dumps(metadata or {}, ensure_ascii=False),
            ],
        )
        self._update_source_run_state(
            source_id=source_id,
            run_id=run_id,
            status="running",
            last_run_at=now,
            next_run_at=None,
            last_error=None,
        )
        run = self.get_run(run_id)
        if run is None:
            raise RuntimeError("policy crawl run creation failed")
        return run

    def finish_run(
        self,
        *,
        run_id: str,
        status: PolicyCrawlRunStatus,
        document_count: int,
        candidate_count: int,
        error_detail: str | None = None,
        metadata: dict[str, Any] | None = None,
        next_run_at: datetime | None = None,
    ) -> PolicyCrawlerRun:
        now = self.utcnow()
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(run_id)
        merged_metadata = {**run.metadata, **(metadata or {})}
        self._execute(
            """
            UPDATE policy_crawl_runs
            SET status = {p}, finished_at = {p}, document_count = {p}, candidate_count = {p},
                error_detail = {p}, metadata_json = {p}
            WHERE run_id = {p}
            """,
            [
                status,
                now.isoformat(),
                int(document_count),
                int(candidate_count),
                error_detail,
                json.dumps(merged_metadata, ensure_ascii=False),
                run_id,
            ],
        )
        self._update_source_run_state(
            source_id=run.source_id,
            run_id=run_id,
            status=status,
            last_run_at=run.started_at,
            next_run_at=next_run_at,
            last_error=error_detail,
        )
        refreshed = self.get_run(run_id)
        if refreshed is None:
            raise RuntimeError("policy crawl run refresh failed")
        return refreshed

    def get_run(self, run_id: str) -> PolicyCrawlerRun | None:
        rows = self._select("SELECT * FROM policy_crawl_runs WHERE run_id = {p}", [run_id])
        return self._row_to_run(rows[0]) if rows else None

    def list_runs(self, *, source_id: str | None = None, limit: int = 20) -> list[PolicyCrawlerRun]:
        params: list[object] = []
        where_sql = ""
        if source_id:
            where_sql = f" WHERE source_id = {self._placeholder()}"
            params.append(source_id)
        params.append(max(1, min(limit, 100)))
        rows = self._select(
            f"SELECT * FROM policy_crawl_runs{where_sql} ORDER BY started_at DESC, run_seq DESC LIMIT {self._placeholder()}",
            params,
        )
        return [self._row_to_run(row) for row in rows]

    def upsert_candidate(
        self,
        *,
        run_id: str,
        source_id: str,
        document: CrawledDocument,
        storage_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyCrawlerCandidate:
        now = self.utcnow()
        content_hash = document.content_hash or hash_content(document.content)
        candidate_id = f"pcand-{hash_content(f'{source_id}:{document.url}:{content_hash}')[:12]}"
        existing = self.get_candidate(candidate_id)
        metadata_json = json.dumps({**document.metadata, **(metadata or {})}, ensure_ascii=False)
        if existing is None:
            self._execute(
                """
                INSERT INTO policy_crawl_candidates (
                    candidate_id, run_id, source_id, url, title, content_type, content_hash,
                    source_name, fetched_at, storage_path, status, created_at, updated_at, metadata_json
                )
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """,
                [
                    candidate_id,
                    run_id,
                    source_id,
                    document.url,
                    document.title,
                    document.content_type,
                    content_hash,
                    document.source_name,
                    document.fetched_at.isoformat() if document.fetched_at else None,
                    storage_path,
                    "pending_review",
                    now.isoformat(),
                    now.isoformat(),
                    metadata_json,
                ],
            )
        else:
            self._execute(
                """
                UPDATE policy_crawl_candidates
                SET run_id = {p}, title = {p}, content_type = {p}, source_name = {p},
                    fetched_at = {p}, storage_path = {p}, updated_at = {p}, metadata_json = {p}
                WHERE candidate_id = {p}
                """,
                [
                    run_id,
                    document.title,
                    document.content_type,
                    document.source_name,
                    document.fetched_at.isoformat() if document.fetched_at else None,
                    storage_path,
                    now.isoformat(),
                    metadata_json,
                    candidate_id,
                ],
            )
        refreshed = self.get_candidate(candidate_id)
        if refreshed is None:
            raise RuntimeError("policy crawl candidate upsert failed")
        return refreshed

    def get_candidate(self, candidate_id: str) -> PolicyCrawlerCandidate | None:
        rows = self._select("SELECT * FROM policy_crawl_candidates WHERE candidate_id = {p}", [candidate_id])
        return self._row_to_candidate(rows[0]) if rows else None

    def list_candidates(
        self,
        *,
        status: PolicyCrawlCandidateStatus | None = None,
        source_id: str | None = None,
        limit: int = 50,
    ) -> list[PolicyCrawlerCandidate]:
        clauses: list[str] = []
        params: list[object] = []
        if status:
            clauses.append(f"status = {self._placeholder()}")
            params.append(status)
        if source_id:
            clauses.append(f"source_id = {self._placeholder()}")
            params.append(source_id)
        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, min(limit, 200)))
        rows = self._select(
            f"SELECT * FROM policy_crawl_candidates{where_sql} ORDER BY updated_at DESC, candidate_seq DESC LIMIT {self._placeholder()}",
            params,
        )
        return [self._row_to_candidate(row) for row in rows]

    def update_candidate_review(
        self,
        *,
        candidate_id: str,
        status: PolicyCrawlCandidateStatus,
        reviewed_by_user_id: str | None,
        review_note: str | None = None,
        knowledge_item_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyCrawlerCandidate:
        now = self.utcnow()
        existing = self.get_candidate(candidate_id)
        if existing is None:
            raise KeyError(candidate_id)
        merged_metadata = {**existing.metadata, **(metadata or {})}
        self._execute(
            """
            UPDATE policy_crawl_candidates
            SET status = {p}, reviewed_by_user_id = {p}, reviewed_at = {p}, review_note = {p},
                knowledge_item_id = {p}, updated_at = {p}, metadata_json = {p}
            WHERE candidate_id = {p}
            """,
            [
                status,
                reviewed_by_user_id,
                now.isoformat(),
                review_note,
                knowledge_item_id,
                now.isoformat(),
                json.dumps(merged_metadata, ensure_ascii=False),
                candidate_id,
            ],
        )
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(candidate_id)
        return candidate

    def count_pending_candidates(self) -> int:
        rows = self._select("SELECT COUNT(*) AS count FROM policy_crawl_candidates WHERE status = {p}", ["pending_review"])
        return int(rows[0]["count"] or 0) if rows else 0

    def _update_source_run_state(
        self,
        *,
        source_id: str,
        run_id: str,
        status: str,
        last_run_at: datetime,
        next_run_at: datetime | None,
        last_error: str | None,
    ) -> None:
        self._execute(
            """
            UPDATE policy_crawl_sources
            SET last_run_id = {p}, last_run_status = {p}, last_run_at = {p},
                next_run_at = {p}, last_error = {p}, updated_at = {p}
            WHERE source_id = {p}
            """,
            [
                run_id,
                status,
                last_run_at.isoformat(),
                next_run_at.isoformat() if next_run_at else None,
                last_error,
                self.utcnow().isoformat(),
                source_id,
            ],
        )

    def _select(self, query: str, params: list[object]) -> list[dict[str, Any]]:
        compiled = self._compile(query)
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(compiled, tuple(params))
                    return [dict(row) for row in cursor.fetchall()]
            rows = connection.execute(compiled, tuple(params)).fetchall()
            return [dict(row) for row in rows]

    def _execute(self, query: str, params: list[object]) -> None:
        compiled = self._compile(query)
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(compiled, tuple(params))
            else:
                connection.execute(compiled, tuple(params))

    def _compile(self, query: str) -> str:
        return query.replace("{p}", self._placeholder())

    def _placeholder(self) -> str:
        return "%s" if self.backend_kind == "postgresql" else "?"

    def _row_to_source(self, row: dict[str, Any]) -> PolicyCrawlerSource:
        return PolicyCrawlerSource(
            source_id=str(row["source_id"]),
            title=str(row["title"]),
            source_url=str(row["source_url"]),
            source_label=str(row["source_label"]),
            allowed_domain=str(row["allowed_domain"]),
            is_enabled=bool(row["is_enabled"]),
            schedule_interval_seconds=_optional_int(row.get("schedule_interval_seconds")),
            last_run_id=row.get("last_run_id"),
            last_run_status=row.get("last_run_status"),
            last_run_at=_parse_datetime(row.get("last_run_at")),
            next_run_at=_parse_datetime(row.get("next_run_at")),
            last_error=row.get("last_error"),
            created_at=_parse_datetime(row.get("created_at")) or self.utcnow(),
            updated_at=_parse_datetime(row.get("updated_at")) or self.utcnow(),
            metadata=_parse_json_object(row.get("metadata_json")),
        )

    def _row_to_run(self, row: dict[str, Any]) -> PolicyCrawlerRun:
        return PolicyCrawlerRun(
            run_id=str(row["run_id"]),
            source_id=str(row["source_id"]),
            trigger_type=str(row["trigger_type"]),
            triggered_by_user_id=row.get("triggered_by_user_id"),
            status=str(row["status"]),  # type: ignore[arg-type]
            provider_name=row.get("provider_name"),
            started_at=_parse_datetime(row.get("started_at")) or self.utcnow(),
            finished_at=_parse_datetime(row.get("finished_at")),
            document_count=int(row.get("document_count") or 0),
            candidate_count=int(row.get("candidate_count") or 0),
            error_detail=row.get("error_detail"),
            metadata=_parse_json_object(row.get("metadata_json")),
        )

    def _row_to_candidate(self, row: dict[str, Any]) -> PolicyCrawlerCandidate:
        return PolicyCrawlerCandidate(
            candidate_id=str(row["candidate_id"]),
            run_id=str(row["run_id"]),
            source_id=str(row["source_id"]),
            url=str(row["url"]),
            title=row.get("title"),
            content_type=str(row["content_type"]),
            content_hash=str(row["content_hash"]),
            source_name=row.get("source_name"),
            fetched_at=_parse_datetime(row.get("fetched_at")),
            storage_path=str(row["storage_path"]),
            status=str(row["status"]),  # type: ignore[arg-type]
            reviewed_by_user_id=row.get("reviewed_by_user_id"),
            reviewed_at=_parse_datetime(row.get("reviewed_at")),
            review_note=row.get("review_note"),
            knowledge_item_id=row.get("knowledge_item_id"),
            created_at=_parse_datetime(row.get("created_at")) or self.utcnow(),
            updated_at=_parse_datetime(row.get("updated_at")) or self.utcnow(),
            metadata=_parse_json_object(row.get("metadata_json")),
        )


class PolicyCrawlerScheduler:
    def __init__(
        self,
        *,
        store: PolicyCrawlerStore | None = None,
        provider: CrawlerProvider | None = None,
        settings: Settings | None = None,
        candidate_dir: Path | str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or PolicyCrawlerStore()
        self.provider = provider or _build_default_crawler_provider(self.settings)
        self.candidate_dir = Path(candidate_dir or Path(self.settings.public_data_dir) / "policy_crawl_candidates")
        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        if self.settings.rag_policy_live_crawler_startup_seed_sources:
            self.store.seed_default_sources()
        if not self.settings.rag_policy_live_crawler_scheduled_enabled:
            logger.info("Policy live crawler scheduled mode is disabled; manual admin trigger remains available.")
            return
        self._thread = threading.Thread(target=self._schedule_loop, name="policy-crawler-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        self._started = False

    def status(self) -> PolicyCrawlerStatus:
        if self.settings.rag_policy_live_crawler_startup_seed_sources:
            self.store.seed_default_sources()
        descriptor = self.provider.describe()
        runs = self.store.list_runs(limit=1)
        latest_run = runs[0] if runs else None
        external_job_id = None
        if latest_run is not None:
            external_job_id = _metadata_string(latest_run.metadata, "external_job_id")
        return PolicyCrawlerStatus(
            scheduler_started=self._started,
            scheduled_enabled=self.settings.rag_policy_live_crawler_scheduled_enabled,
            manual_enabled=self.settings.rag_policy_live_crawler_manual_enabled,
            auto_publish_enabled=self.settings.rag_policy_live_crawler_auto_publish,
            running=self._run_lock.locked(),
            crawler_backend=descriptor.crawler_backend or _normalize_crawler_backend(self.settings.rag_policy_crawler_backend),
            provider_name=descriptor.name,
            provider_mode=descriptor.mode,
            provider_enabled=descriptor.enabled,
            provider_available=descriptor.available,
            local_scrapy_available=descriptor.local_scrapy_available,
            scrapyd_available=descriptor.scrapyd_available,
            scrapyd_endpoint_label=descriptor.scrapyd_endpoint_label,
            provider_error=descriptor.last_error,
            external_job_id=external_job_id,
            interval_seconds=self.settings.rag_policy_live_crawler_interval_seconds,
            initial_delay_seconds=self.settings.rag_policy_live_crawler_initial_delay_seconds,
            source_count=len(self.store.list_sources()),
            pending_candidate_count=self.store.count_pending_candidates(),
            recent_run_status=latest_run.status if latest_run else None,
            safe_limits={
                **self._safe_limits(),
                "allowed_domains": list(DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS),
                "scrapy_import_available": descriptor.available,
                "scrapy_install_command": "backend\\.venv\\Scripts\\python.exe -m pip install scrapy==2.15.2",
            },
        )

    def run_source_now(self, *, source_id: str, triggered_by_user_id: str | None = None) -> PolicyCrawlerRun:
        if not self.settings.rag_policy_live_crawler_manual_enabled:
            raise RuntimeError("manual policy crawler trigger is disabled")
        if not self._run_lock.acquire(blocking=False):
            raise PolicyCrawlerBusyError("policy crawler is already running")
        try:
            return self._run_source(source_id=source_id, trigger_type="manual", triggered_by_user_id=triggered_by_user_id)
        finally:
            self._run_lock.release()

    def list_sources(self) -> list[PolicyCrawlerSource]:
        self.store.seed_default_sources()
        return self.store.list_sources()

    def list_runs(self, *, source_id: str | None = None, limit: int = 20) -> list[PolicyCrawlerRun]:
        return self.store.list_runs(source_id=source_id, limit=limit)

    def list_candidates(
        self,
        *,
        status: PolicyCrawlCandidateStatus | None = None,
        source_id: str | None = None,
        limit: int = 50,
    ) -> list[PolicyCrawlerCandidate]:
        return self.store.list_candidates(status=status, source_id=source_id, limit=limit)

    def publish_candidate(self, *, candidate_id: str, reviewed_by_user_id: str | None) -> PolicyCrawlerCandidate:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(candidate_id)
        if candidate.status == "published":
            return candidate
        if candidate.status != "pending_review":
            raise ValueError("only pending_review candidates can be published")
        storage_path = Path(candidate.storage_path)
        if not storage_path.exists():
            raise FileNotFoundError(candidate.storage_path)
        document = CrawledDocument(
            url=candidate.url,
            title=candidate.title,
            content=_read_candidate_content(candidate),
            content_type=candidate.content_type,
            source_name=candidate.source_name,
            fetched_at=candidate.fetched_at or self.store.utcnow(),
            raw_storage_path=str(storage_path),
            content_hash=candidate.content_hash,
            metadata={
                **candidate.metadata,
                "policy_crawl_candidate_id": candidate.candidate_id,
                "policy_crawl_run_id": candidate.run_id,
                "review_status": "auto_published" if reviewed_by_user_id is None else "admin_published",
                "auto_publish_enabled": self.settings.rag_policy_live_crawler_auto_publish,
            },
        )
        from app.knowledge.service import get_knowledge_service

        knowledge_service = get_knowledge_service()
        task = knowledge_service.create_policy_item_from_crawled_document(
            crawled_document=document,
            staging_dir=Path(self.settings.public_data_dir) / "policy_staging",
            requested_by_user_id=reviewed_by_user_id,
        )
        reviewed = self.store.update_candidate_review(
            candidate_id=candidate_id,
            status="published",
            reviewed_by_user_id=reviewed_by_user_id,
            review_note="Auto-published to public_policy_web; crawl_ingest queued."
            if reviewed_by_user_id is None
            else "Published by admin; crawl_ingest queued.",
            knowledge_item_id=task.knowledge_item_id,
            metadata={
                "auto_publish_enabled": self.settings.rag_policy_live_crawler_auto_publish,
                "publish_mode": "auto" if reviewed_by_user_id is None else "manual",
                "index_status": "queued",
            },
        )
        try:
            processed = knowledge_service.run_queued_tasks()
            processed_ids = [item.task_id for item in processed]
            refreshed_item = knowledge_service.store.get_item(task.knowledge_item_id)
            if refreshed_item is not None and refreshed_item.index_status == "indexed":
                return self.store.update_candidate_review(
                    candidate_id=candidate_id,
                    status="published",
                    reviewed_by_user_id=reviewed_by_user_id,
                    review_note=f"Auto-published and indexed. Processed tasks: {', '.join(processed_ids) or task.task_id}.",
                    knowledge_item_id=task.knowledge_item_id,
                    metadata={"index_status": "indexed", "processed_task_ids": processed_ids or [task.task_id]},
                )
            if refreshed_item is not None and refreshed_item.last_error:
                return self.store.update_candidate_review(
                    candidate_id=candidate_id,
                    status="published",
                    reviewed_by_user_id=reviewed_by_user_id,
                    review_note=f"Auto-published, but indexing failed: {refreshed_item.last_error}",
                    knowledge_item_id=task.knowledge_item_id,
                    metadata={"index_status": "failed", "index_error": refreshed_item.last_error},
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Policy crawler candidate was published but immediate indexing failed.")
            return self.store.update_candidate_review(
                candidate_id=candidate_id,
                status="published",
                reviewed_by_user_id=reviewed_by_user_id,
                review_note=f"Auto-published, but immediate indexing failed: {exc}",
                knowledge_item_id=task.knowledge_item_id,
                metadata={"index_status": "failed", "index_error": str(exc)},
            )
        return reviewed

    def reject_candidate(self, *, candidate_id: str, reviewed_by_user_id: str | None) -> PolicyCrawlerCandidate:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(candidate_id)
        if candidate.status != "pending_review":
            raise ValueError("only pending_review candidates can be rejected")
        return self.store.update_candidate_review(
            candidate_id=candidate_id,
            status="rejected",
            reviewed_by_user_id=reviewed_by_user_id,
            review_note="Rejected by admin review.",
        )

    def _schedule_loop(self) -> None:
        if self._stop_event.wait(self.settings.rag_policy_live_crawler_initial_delay_seconds):
            return
        while not self._stop_event.is_set():
            try:
                self.run_due_sources_once()
            except Exception:
                logger.exception("Policy crawler scheduled run failed.")
            if self._stop_event.wait(self.settings.rag_policy_live_crawler_interval_seconds):
                break

    def run_due_sources_once(self) -> list[PolicyCrawlerRun]:
        if not self.settings.rag_policy_live_crawler_scheduled_enabled:
            return []
        if not self._run_lock.acquire(blocking=False):
            return []
        try:
            now = self.store.utcnow()
            runs: list[PolicyCrawlerRun] = []
            for source in self.store.list_sources():
                if not source.is_enabled:
                    continue
                if source.next_run_at is not None and source.next_run_at > now:
                    continue
                runs.append(self._run_source(source_id=source.source_id, trigger_type="scheduled", triggered_by_user_id=None))
            return runs
        finally:
            self._run_lock.release()

    def _run_source(
        self,
        *,
        source_id: str,
        trigger_type: str,
        triggered_by_user_id: str | None,
    ) -> PolicyCrawlerRun:
        self.store.seed_default_sources()
        source = self.store.get_source(source_id)
        if source is None:
            raise KeyError(source_id)
        if not source.is_enabled:
            raise RuntimeError("policy crawler source is disabled")
        if not is_allowed_policy_url(source.source_url, allowed_domains=DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS):
            raise ValueError(f"policy crawl source is outside official allowlist: {source.source_url}")
        descriptor = self.provider.describe()
        start_urls = _source_start_urls(source)
        request = PolicyCrawlRequest(
            start_urls=start_urls,
            allowed_domains=[source.allowed_domain],
            max_depth=self.settings.rag_policy_live_crawler_max_depth,
            max_pages=self.settings.rag_policy_live_crawler_max_pages,
            obey_robots=True,
            download_delay_seconds=self.settings.rag_policy_live_crawler_download_delay_seconds,
            concurrent_requests_per_domain=self.settings.rag_policy_live_crawler_concurrent_per_domain,
            timeout_seconds=self.settings.rag_policy_live_crawler_timeout_seconds,
            user_agent=self.settings.rag_policy_live_crawler_user_agent,
            metadata={
                "source_id": source.source_id,
                "trigger_type": trigger_type,
                "source_label": source.source_label,
                "auto_publish_enabled": self.settings.rag_policy_live_crawler_auto_publish,
                "topic_filter": "dual_carbon_policy_or_standard",
            },
        )
        run = self.store.create_run(
            source_id=source.source_id,
            trigger_type=trigger_type,
            triggered_by_user_id=triggered_by_user_id,
            provider_name=descriptor.name,
            metadata={"provider": descriptor.model_dump(), "safe_limits": self._safe_limits()},
        )
        result = self.provider.crawl(request)
        success_next_run_at = self.store.utcnow() + timedelta(seconds=self.settings.rag_policy_live_crawler_interval_seconds)
        failure_next_run_at = self.store.utcnow() + timedelta(seconds=self.settings.rag_policy_live_crawler_failure_backoff_seconds)
        if result.status != "succeeded":
            error_detail = "; ".join(result.errors) if result.errors else result.status
            logger.warning(
                "Policy crawler source failed; source_id=%s status=%s error=%s",
                source.source_id,
                result.status,
                error_detail,
            )
            return self.store.finish_run(
                run_id=run.run_id,
                status=result.status,  # type: ignore[arg-type]
                document_count=0,
                candidate_count=0,
                error_detail=error_detail,
                metadata=result.metadata,
                next_run_at=failure_next_run_at,
            )
        candidates: list[PolicyCrawlerCandidate] = []
        published_candidates: list[PolicyCrawlerCandidate] = []
        errors: list[str] = []
        skipped_by_topic: list[str] = []
        for document in result.documents:
            if not is_allowed_policy_url(document.url, allowed_domains=DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS):
                errors.append(f"skipped non-allowlisted crawled URL: {document.url}")
                continue
            matched_keywords = _matched_policy_topic_keywords(document)
            if not matched_keywords:
                skipped_by_topic.append(document.url)
                continue
            storage_path = self._write_candidate_document(source=source, document=document)
            candidate = self.store.upsert_candidate(
                run_id=run.run_id,
                source_id=source.source_id,
                document=document,
                storage_path=str(storage_path),
                metadata={
                    "source_title": source.title,
                    "source_label": source.source_label,
                    "allowed_domain": source.allowed_domain,
                    "seed_url": source.source_url,
                    "start_urls": start_urls,
                    "policy_review_required": False,
                    "auto_publish_enabled": self.settings.rag_policy_live_crawler_auto_publish,
                    "matched_policy_keywords": matched_keywords,
                    "candidate_summary": _candidate_summary(document),
                    "candidate_content_length": _candidate_content_length(document),
                    "candidate_depth": document.metadata.get("depth"),
                    "candidate_response_url": document.metadata.get("response_url"),
                    "provider_metadata": result.metadata,
                },
            )
            candidates.append(candidate)
            if self.settings.rag_policy_live_crawler_auto_publish:
                try:
                    published_candidates.append(
                        self.publish_candidate(candidate_id=candidate.candidate_id, reviewed_by_user_id=None)
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Policy crawler auto-publish failed; candidate_id=%s", candidate.candidate_id)
                    errors.append(f"auto-publish failed for {candidate.url}: {exc}")
                    self.store.update_candidate_review(
                        candidate_id=candidate.candidate_id,
                        status="published",
                        reviewed_by_user_id=triggered_by_user_id,
                        review_note=f"Auto-publish attempted, but indexing failed: {exc}",
                        knowledge_item_id=candidate.knowledge_item_id,
                        metadata={"index_status": "failed", "index_error": str(exc), "publish_mode": "auto"},
                    )
        if result.documents and not candidates:
            errors.append(
                "no crawled document matched the dual-carbon policy/technical-standard topic filter"
            )
        indexed_count = sum(1 for candidate in published_candidates if candidate.metadata.get("index_status") == "indexed")
        failed_index_count = sum(
            1
            for candidate in published_candidates
            if candidate.metadata.get("index_status") == "failed" or (candidate.review_note and "failed" in candidate.review_note.lower())
        )
        status: PolicyCrawlRunStatus = "succeeded" if not errors and (candidates or not result.documents) else "failed"
        run_metadata = {
            **result.metadata,
            "start_urls": start_urls,
            "auto_publish_enabled": self.settings.rag_policy_live_crawler_auto_publish,
            "auto_published_count": len(published_candidates),
            "auto_indexed_count": indexed_count,
            "auto_index_failed_count": failed_index_count,
            "skipped_topic_count": len(skipped_by_topic),
            "skipped_topic_urls": skipped_by_topic[:20],
        }
        return self.store.finish_run(
            run_id=run.run_id,
            status=status,
            document_count=len(result.documents),
            candidate_count=len(candidates),
            error_detail="; ".join(errors) if errors else None,
            metadata=run_metadata,
            next_run_at=success_next_run_at if status == "succeeded" else failure_next_run_at,
        )

    def _write_candidate_document(self, *, source: PolicyCrawlerSource, document: CrawledDocument) -> Path:
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        suffix = _suffix_for_content_type(document.content_type)
        content_hash = document.content_hash or hash_content(document.content)
        target_path = self.candidate_dir / f"{source.source_id}-{hash_content(document.url)[:10]}-{content_hash[:10]}{suffix}"
        target_path.write_bytes(_document_content_bytes(document))
        return target_path

    def _safe_limits(self) -> dict[str, Any]:
        return {
            "obey_robots": True,
            "max_depth": self.settings.rag_policy_live_crawler_max_depth,
            "max_pages": self.settings.rag_policy_live_crawler_max_pages,
            "download_delay_seconds": self.settings.rag_policy_live_crawler_download_delay_seconds,
            "concurrent_requests_per_domain": self.settings.rag_policy_live_crawler_concurrent_per_domain,
            "timeout_seconds": self.settings.rag_policy_live_crawler_timeout_seconds,
            "failure_backoff_seconds": self.settings.rag_policy_live_crawler_failure_backoff_seconds,
            "user_agent": self.settings.rag_policy_live_crawler_user_agent,
        }


@lru_cache(maxsize=1)
def get_policy_crawler_scheduler() -> PolicyCrawlerScheduler:
    return PolicyCrawlerScheduler()


def _build_default_crawler_provider(settings: Settings) -> CrawlerProvider:
    backend = _normalize_crawler_backend(settings.rag_policy_crawler_backend)
    if backend == "scrapyd":
        return ScrapydCrawlerProvider(
            enabled=settings.rag_enable_policy_crawler,
            settings=settings,
        )
    return ScrapyCrawlerProvider(
        enabled=settings.rag_enable_policy_crawler,
        settings=settings,
    )


def _normalize_crawler_backend(value: str | None) -> str:
    normalized = (value or "local_scrapy").strip().lower().replace("-", "_")
    if normalized in {"scrapyd", "remote_scrapyd"}:
        return "scrapyd"
    return "local_scrapy"


def _metadata_string(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _source_start_urls(source: PolicyCrawlerSource) -> list[str]:
    urls: list[str] = [source.source_url]
    raw_extra = source.metadata.get("extra_start_urls")
    if isinstance(raw_extra, list):
        urls.extend(str(item).strip() for item in raw_extra if str(item).strip())
    approved: list[str] = []
    for url in urls:
        if is_allowed_policy_url(url, allowed_domains=DEFAULT_POLICY_CRAWLER_ALLOWED_DOMAINS):
            approved.append(url)
    return list(dict.fromkeys(approved)) or [source.source_url]


def _matched_policy_topic_keywords(document: CrawledDocument) -> list[str]:
    haystack = " ".join(
        [
            document.title or "",
            document.url,
            _readable_preview(document.content)[:12000],
            json.dumps(document.metadata, ensure_ascii=False),
        ]
    ).lower()
    topic_keywords = (
        "双碳",
        "碳达峰",
        "碳中和",
        "降碳",
        "低碳",
        "零碳",
        "碳排放",
        "碳核算",
        "碳市场",
        "节能",
        "能耗",
        "绿色低碳",
        "绿色制造",
        "清洁生产",
        "温室气体",
        "排放权",
        "能源消费",
        "技术标准",
        "国家标准",
        "行业标准",
        "团体标准",
    )
    matched = [keyword for keyword in topic_keywords if keyword.lower() in haystack]
    if matched:
        return matched[:12]
    if any(token in haystack for token in ("carbon", "emission", "green", "energy saving")):
        return ["english-carbon-topic"]
    return []


def _host(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return (parsed.hostname or "").lower().strip(".")


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _parse_json_object(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _suffix_for_content_type(content_type: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized == "application/pdf":
        return ".pdf"
    if normalized == "application/ofd":
        return ".ofd"
    if normalized in {"text/plain", "text/markdown"}:
        return ".txt"
    return ".html"


def _document_content_bytes(document: CrawledDocument) -> bytes:
    transfer_encoding = str(document.metadata.get("content_transfer_encoding") or "text").strip().lower()
    if transfer_encoding == "base64":
        try:
            return base64.b64decode(document.content.encode("ascii"), validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid base64 crawled document payload for {document.url}") from exc
    return document.content.encode("utf-8")


def _read_candidate_content(candidate: PolicyCrawlerCandidate) -> str:
    path = Path(candidate.storage_path)
    normalized = candidate.content_type.split(";", 1)[0].strip().lower()
    if normalized in {"application/pdf", "application/ofd", "application/vnd.ofd"}:
        return base64.b64encode(path.read_bytes()).decode("ascii")
    return _read_text_candidate(path)


def _read_text_candidate(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _candidate_content_length(document: CrawledDocument) -> int:
    raw_length = document.metadata.get("content_length")
    try:
        return int(raw_length)
    except (TypeError, ValueError):
        pass
    return len(_document_content_bytes(document))


def _candidate_summary(document: CrawledDocument, *, max_length: int = 240) -> str:
    normalized = document.content_type.split(";", 1)[0].strip().lower()
    if normalized in {"application/pdf", "application/ofd", "application/vnd.ofd"}:
        return f"{normalized} binary document, {_candidate_content_length(document)} bytes"
    text = _readable_preview(document.content)
    return text[:max_length].strip()


def _readable_preview(value: str) -> str:
    text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
