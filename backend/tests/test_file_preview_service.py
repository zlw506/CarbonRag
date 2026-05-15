from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.auth.schemas import AuthenticatedUser
from app.file_preview.service import FilePreviewService


def _user(role: str = "user") -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id="user-001",
        username="tester",
        display_name="tester",
        role=role,  # type: ignore[arg-type]
        is_active=True,
        password_must_change=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _patch_preview_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = SimpleNamespace(upload_dir=str(tmp_path / "uploads"), public_data_dir=str(tmp_path / "public"))
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.public_data_dir).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.file_preview.service.get_settings", lambda: settings)
    monkeypatch.setattr("app.file_preview.service.resolve_repo_path", lambda value: Path(value))


def test_session_file_preview_returns_markdown_text_chunks_and_raw(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_preview_roots(monkeypatch, tmp_path)
    raw_file = tmp_path / "uploads" / "report.md"
    raw_file.write_text("# 报告\n\n外购电力 217,650 kWh", encoding="utf-8")

    chunk = SimpleNamespace(
        chunk_id="chunk-001",
        order_index=0,
        snippet="外购电力 217,650 kWh",
        title="青木报告",
        source_type="private_upload",
        source_url=None,
        metadata={"page_number": 2, "section_title": "用电数据"},
    )

    class FakeStore:
        def get_uploaded_file_detail(self, *, owner_user_id: str, file_id: str) -> dict:
            assert owner_user_id == "user-001"
            assert file_id == "file-001"
            return {
                "file_id": file_id,
                "owner_user_id": owner_user_id,
                "filename": "report.md",
                "mime_type": "text/markdown",
                "size": raw_file.stat().st_size,
                "storage_path": str(raw_file),
                "parse_status": "parsed",
                "knowledge_item_id": "ki-001",
            }

        def get_file_parse_result(self, *, file_id: str) -> dict:
            assert file_id == "file-001"
            return {
                "extracted_markdown": "# 青木报告\n\n外购电力 217,650 kWh",
                "extracted_text": "青木报告 外购电力 217,650 kWh",
            }

        def list_chunks(self, *, knowledge_item_id: str) -> list:
            assert knowledge_item_id == "ki-001"
            return [chunk]

    monkeypatch.setattr("app.file_preview.service.get_knowledge_service", lambda: SimpleNamespace(store=FakeStore()))

    preview = FilePreviewService().preview(source_type="session_file", source_id="file-001", current_user=_user())

    assert preview.title == "report.md"
    assert "217,650 kWh" in (preview.markdown or "")
    assert preview.raw_available is True
    assert preview.chunks[0].page_number == 2
    assert preview.chunks[0].section_title == "用电数据"


def test_rag_document_preview_requires_kb_id() -> None:
    with pytest.raises(KeyError):
        FilePreviewService().preview(source_type="rag_document", source_id="doc-001", current_user=_user())


def test_crawler_candidate_preview_is_admin_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_preview_roots(monkeypatch, tmp_path)
    raw_file = tmp_path / "public" / "candidate.txt"
    md_file = tmp_path / "public" / "candidate.md"
    raw_file.write_text("碳达峰政策原文", encoding="utf-8")
    md_file.write_text("# 碳达峰政策\n\n清洗后的 Markdown", encoding="utf-8")

    class FakeCandidate:
        candidate_id = "cand-001"
        run_id = "run-001"
        source_id = "gov-cn-policy-library"
        url = "https://www.gov.cn/policy/example"
        title = "碳达峰政策"
        content_type = "text/html"
        content_hash = "hash-001"
        source_name = "gov.cn"
        fetched_at = datetime.now(timezone.utc)
        storage_path = str(raw_file)
        status = "pending_review"
        metadata = {"markdown_storage_path": str(md_file), "canonical_url": url}

        def model_dump(self, mode: str = "python") -> dict:  # noqa: ARG002
            return {
                "candidate_id": self.candidate_id,
                "run_id": self.run_id,
                "source_id": self.source_id,
                "url": self.url,
                "title": self.title,
                "content_type": self.content_type,
                "content_hash": self.content_hash,
                "source_name": self.source_name,
                "fetched_at": self.fetched_at,
                "storage_path": self.storage_path,
                "status": self.status,
                "metadata": self.metadata,
            }

    scheduler = SimpleNamespace(store=SimpleNamespace(get_candidate=lambda candidate_id: FakeCandidate()))
    monkeypatch.setattr("app.file_preview.service.get_policy_crawler_scheduler", lambda: scheduler)

    service = FilePreviewService()
    with pytest.raises(PermissionError):
        service.preview(source_type="crawler_candidate", source_id="cand-001", current_user=_user("user"))

    preview = service.preview(source_type="crawler_candidate", source_id="cand-001", current_user=_user("admin"))
    assert preview.source_url == "https://www.gov.cn/policy/example"
    assert "清洗后的 Markdown" in (preview.markdown or "")
    assert preview.raw_available is True


def test_crawler_candidate_preview_resolves_backend_relative_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    backend_root = repo_root / "backend"
    artifact_dir = backend_root / "data" / "public" / "policy_crawl_artifacts" / "run-001" / "cand-001"
    artifact_dir.mkdir(parents=True)
    markdown_file = artifact_dir / "document.md"
    cleaned_file = artifact_dir / "cleaned.txt"
    raw_file = artifact_dir / "raw.html"
    markdown_file.write_text("# 国务院关于推进服务业扩能提质的意见\n\n正文 Markdown", encoding="utf-8")
    cleaned_file.write_text("国务院关于推进服务业扩能提质的意见 正文纯文本", encoding="utf-8")
    raw_file.write_text("<html>raw</html>", encoding="utf-8")

    settings = SimpleNamespace(upload_dir="./data/outputs/uploads", public_data_dir="./data/public")
    monkeypatch.setattr("app.file_preview.service.REPO_ROOT", repo_root)
    monkeypatch.setattr("app.file_preview.service.get_settings", lambda: settings)
    monkeypatch.setattr("app.file_preview.service.resolve_repo_path", lambda value: repo_root / value)

    class FakeCandidate:
        candidate_id = "cand-001"
        run_id = "run-001"
        source_id = "gov-cn-policy-library"
        url = "https://www.gov.cn/zhengce/content/202604/content_7066483.htm"
        title = "国务院关于推进服务业扩能提质的意见"
        content_type = "text/html"
        content_hash = "hash-001"
        source_name = "gov.cn"
        fetched_at = datetime.now(timezone.utc)
        storage_path = "data/public/policy_crawl_artifacts/run-001/cand-001/raw.html"
        status = "pending_review"
        metadata = {
            "markdown_storage_path": "data/public/policy_crawl_artifacts/run-001/cand-001/document.md",
            "cleaned_storage_path": "data/public/policy_crawl_artifacts/run-001/cand-001/cleaned.txt",
            "raw_storage_path": "data/public/policy_crawl_artifacts/run-001/cand-001/raw.html",
        }

        def model_dump(self, mode: str = "python") -> dict:  # noqa: ARG002
            return {
                "candidate_id": self.candidate_id,
                "run_id": self.run_id,
                "source_id": self.source_id,
                "url": self.url,
                "title": self.title,
                "content_type": self.content_type,
                "content_hash": self.content_hash,
                "source_name": self.source_name,
                "fetched_at": self.fetched_at,
                "storage_path": self.storage_path,
                "status": self.status,
                "metadata": self.metadata,
            }

    scheduler = SimpleNamespace(store=SimpleNamespace(get_candidate=lambda candidate_id: FakeCandidate()))
    monkeypatch.setattr("app.file_preview.service.get_policy_crawler_scheduler", lambda: scheduler)

    preview = FilePreviewService().preview(source_type="crawler_candidate", source_id="cand-001", current_user=_user("admin"))

    assert "正文 Markdown" in (preview.markdown or "")
    assert "正文纯文本" in (preview.text or "")
    assert preview.raw_available is True


def test_raw_preview_rejects_unregistered_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_preview_roots(monkeypatch, tmp_path)
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("should not be exposed", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        FilePreviewService()._raw_from_metadata({"storage_path": str(outside_file)}, fallback_filename="outside.txt")
