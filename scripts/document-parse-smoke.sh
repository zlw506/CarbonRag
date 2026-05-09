#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${REPO_ROOT}/backend/.conda/python.exe"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="python"
fi

cd "${REPO_ROOT}"
echo "==> Running document parse smoke"
"${PYTHON}" - <<'PY'
from pathlib import Path
import csv
import sys
import tempfile

repo = Path.cwd()
sys.path.insert(0, str(repo / "backend"))

from app.files.parser.registry import FileParserRegistry

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    samples = []
    text_file = root / "sample.txt"
    text_file.write_text("electricity bill: usage 1200 kWh", encoding="utf-8")
    samples.append((text_file, "text/plain"))

    md_file = root / "sample.md"
    md_file.write_text("# Electricity note\n\nusage 800 kWh", encoding="utf-8")
    samples.append((md_file, "text/markdown"))

    csv_file = root / "sample.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["period", "electricity_kwh"])
        writer.writerow(["2026-01", "1200"])
    samples.append((csv_file, "text/csv"))

    html_file = root / "sample.html"
    html_file.write_text("<h1>Bill</h1><p>usage 500 kWh</p>", encoding="utf-8")
    samples.append((html_file, "text/html"))

    try:
        from openpyxl import Workbook
        xlsx_file = root / "sample.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append(["period", "electricity_kwh"])
        ws.append(["2026-01", 1200])
        wb.save(xlsx_file)
        samples.append((xlsx_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
    except Exception as exc:
        print(f"skip xlsx fixture: {exc}")

    try:
        from docx import Document
        docx_file = root / "sample.docx"
        doc = Document()
        doc.add_paragraph("natural gas bill: 800 m3")
        doc.save(docx_file)
        samples.append((docx_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    except Exception as exc:
        print(f"skip docx fixture: {exc}")

    parser = FileParserRegistry()
    ok = 0
    for path, mime_type in samples:
        parsed = parser.parse(path=path, mime_type=mime_type)
        assert parsed.text.strip(), path
        print(f"parsed {path.name}: {parsed.parser_name}, chars={len(parsed.text)}")
        ok += 1
    assert ok >= 5, f"expected at least 5 parsed samples, got {ok}"

print("document parse smoke ok")
PY
