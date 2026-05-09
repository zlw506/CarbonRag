import pytest

from app.files.service import FileService, MAX_UPLOAD_BYTES


class _FakeSessionService:
    pass


def _service() -> FileService:
    return FileService(session_service=_FakeSessionService())  # type: ignore[arg-type]


def test_file_upload_security_accepts_supported_document_types() -> None:
    service = _service()

    service.validate_upload(filename="bill.pdf", mime_type="application/pdf", size=128)
    service.validate_upload(filename="ledger.xlsx", mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", size=128)
    service.validate_upload(filename="notes.md", mime_type="text/markdown", size=128)


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("malware.exe", "application/octet-stream"),
        ("script.ps1", "text/plain"),
        ("archive.zip", "application/octet-stream"),
        ("macro.docm", "application/vnd.ms-word.document.macroEnabled.12"),
        ("legacy.doc", "application/msword"),
    ],
)
def test_file_upload_security_rejects_risky_extensions(filename: str, mime_type: str) -> None:
    with pytest.raises(TypeError):
        _service().validate_upload(filename=filename, mime_type=mime_type, size=128)


def test_file_upload_security_rejects_oversized_file() -> None:
    with pytest.raises(ValueError, match="20 MB"):
        _service().validate_upload(filename="bill.pdf", mime_type="application/pdf", size=MAX_UPLOAD_BYTES + 1)
