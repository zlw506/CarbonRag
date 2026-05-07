import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rag_eval import EvalVariant, RagEvalCase, format_markdown, load_eval_cases, run_eval


def test_rag_eval_empty_dataset_returns_clear_status() -> None:
    report = run_eval(cases=[], variants=[EvalVariant(name="bm25_only", retrieval_strategy="bm25_only")])

    assert report["status"] == "empty_dataset"
    assert report["total_cases"] == 0
    assert report["variants"]["bm25_only"]["total_cases"] == 0


def test_rag_eval_loads_cases_from_json(tmp_path: Path) -> None:
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "id": "case-001",
                    "query": "碳核算",
                    "knowledge_scope": "public",
                    "expected_doc_ids": ["policy_002"],
                    "expected_keywords": ["核算"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_eval_cases(dataset)

    assert cases == [
        RagEvalCase(
            id="case-001",
            query="碳核算",
            knowledge_scope="public",
            expected_doc_ids=["policy_002"],
            expected_keywords=["核算"],
        )
    ]


def test_rag_eval_runs_single_case_and_reports_metrics() -> None:
    report = run_eval(
        cases=[
            RagEvalCase(
                id="policy-smoke",
                query="2030年前碳达峰行动方案有哪些重点？",
                knowledge_scope="public",
                expected_doc_ids=["policy_001"],
                expected_keywords=["碳达峰"],
            )
        ],
        variants=[EvalVariant(name="bm25_only", retrieval_strategy="bm25_only")],
        top_k=3,
    )

    metrics = report["variants"]["bm25_only"]
    assert report["status"] == "ok"
    assert metrics["total_cases"] == 1
    assert metrics["hit_at_3"] == 1
    assert metrics["citation_count"] >= 1
    assert metrics["zero_hit_count"] == 0
    assert metrics["average_latency_ms"] >= 0


def test_rag_eval_markdown_contains_required_metrics() -> None:
    markdown = format_markdown(
        {
            "status": "ok",
            "total_cases": 1,
            "variants": {
                "bm25_only": {
                    "hit_at_1": 1,
                    "hit_at_3": 1,
                    "hit_at_5": 1,
                    "citation_count": 2,
                    "zero_hit_count": 0,
                    "fallback_count": 1,
                    "average_latency_ms": 1.25,
                }
            },
        }
    )

    assert "hit@1" in markdown
    assert "zero_hits" in markdown
    assert "avg_latency_ms" in markdown


def test_rag_eval_cli_can_run_empty_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "empty.json"
    dataset.write_text("[]", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "scripts" / "rag_eval.py"),
            "--dataset",
            str(dataset),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "empty_dataset"
