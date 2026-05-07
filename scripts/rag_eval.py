from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "rag" / "rag_eval_cases.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai_runtime.providers.rerank_local import FakeRerankProvider, NoopRerankProvider  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.rag.schemas import RagExperimentalRetrievalStrategy, RagKnowledgeScope, RagQueryParams  # noqa: E402
from app.rag.service import RagEngineService  # noqa: E402


@dataclass(frozen=True)
class RagEvalCase:
    id: str
    query: str
    knowledge_scope: RagKnowledgeScope
    expected_doc_ids: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvalVariant:
    name: str
    retrieval_strategy: RagExperimentalRetrievalStrategy
    enable_rerank: bool = False


DEFAULT_VARIANTS = [
    EvalVariant(name="bm25_only", retrieval_strategy="bm25_only"),
    EvalVariant(name="vector_only", retrieval_strategy="vector_only"),
    EvalVariant(name="bm25_vector_hybrid", retrieval_strategy="bm25_vector_hybrid"),
    EvalVariant(name="bm25_vector_hybrid_rerank", retrieval_strategy="bm25_vector_hybrid", enable_rerank=True),
]


def load_eval_cases(path: Path) -> list[RagEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RAG eval dataset must be a JSON list.")
    return [_case_from_payload(item) for item in payload]


def run_eval(
    *,
    cases: list[RagEvalCase],
    variants: list[EvalVariant] | None = None,
    top_k: int = 5,
    vector_backend: str = "current",
    rerank_provider: str = "noop",
) -> dict[str, Any]:
    selected_variants = variants or DEFAULT_VARIANTS
    if not cases:
        return {
            "status": "empty_dataset",
            "message": "No RAG eval cases were provided.",
            "total_cases": 0,
            "variants": {
                variant.name: _empty_metrics()
                for variant in selected_variants
            },
        }

    return {
        "status": "ok",
        "total_cases": len(cases),
        "variants": {
            variant.name: _evaluate_variant(
                cases=cases,
                variant=variant,
                top_k=top_k,
                vector_backend=vector_backend,
                rerank_provider=rerank_provider,
            )
            for variant in selected_variants
        },
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# RAG Eval Report",
        "",
        f"- status: `{report.get('status')}`",
        f"- total_cases: `{report.get('total_cases', 0)}`",
        "",
        "| variant | hit@1 | hit@3 | hit@5 | citations | zero_hits | fallbacks | avg_latency_ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    variants = report.get("variants", {})
    if isinstance(variants, dict):
        for name, metrics in variants.items():
            if not isinstance(metrics, dict):
                continue
            lines.append(
                "| {name} | {hit_at_1} | {hit_at_3} | {hit_at_5} | {citation_count} | "
                "{zero_hit_count} | {fallback_count} | {average_latency_ms:.3f} |".format(
                    name=name,
                    hit_at_1=metrics.get("hit_at_1", 0),
                    hit_at_3=metrics.get("hit_at_3", 0),
                    hit_at_5=metrics.get("hit_at_5", 0),
                    citation_count=metrics.get("citation_count", 0),
                    zero_hit_count=metrics.get("zero_hit_count", 0),
                    fallback_count=metrics.get("fallback_count", 0),
                    average_latency_ms=float(metrics.get("average_latency_ms") or 0.0),
                )
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CarbonRag retrieval evaluation baselines.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-backend", default="current")
    parser.add_argument("--rerank-provider", choices=["noop", "fake"], default="noop")
    args = parser.parse_args(argv)

    cases = load_eval_cases(args.dataset)
    report = run_eval(
        cases=cases,
        top_k=args.top_k,
        vector_backend=args.vector_backend,
        rerank_provider=args.rerank_provider,
    )
    report["dataset_path"] = str(args.dataset)
    if args.format == "markdown":
        print(format_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _evaluate_variant(
    *,
    cases: list[RagEvalCase],
    variant: EvalVariant,
    top_k: int,
    vector_backend: str,
    rerank_provider: str,
) -> dict[str, Any]:
    settings = Settings(
        rag_engine_enabled=True,
        rag_vector_enabled=True,
        rag_vector_backend=vector_backend,
        rag_rerank_enabled=variant.enable_rerank,
    )
    service = RagEngineService(
        settings=settings,
        rerank_provider=FakeRerankProvider() if rerank_provider == "fake" else NoopRerankProvider(),
    )
    case_results = []
    for case in cases:
        result = service.retrieve(
            RagQueryParams(
                question=case.query,
                knowledge_scope=case.knowledge_scope,
                top_k=top_k,
                chunk_top_k=max(top_k, 5),
                enable_rerank=variant.enable_rerank,
                retrieval_strategy=variant.retrieval_strategy,
            )
        )
        hit_positions = _hit_positions(case=case, chunks=result.chunks)
        case_results.append(
            {
                "case_id": case.id,
                "query": case.query,
                "hit_positions": hit_positions,
                "returned_count": len(result.chunks),
                "citation_count": len(result.references),
                "fallback_used": bool(result.metadata.fallback_used),
                "fallback_reason": result.metadata.fallback_reason,
                "latency_ms": result.metadata.latency_ms or 0.0,
                "doc_ids": [chunk.doc_id for chunk in result.chunks],
                "chunk_ids": [chunk.chunk_id for chunk in result.chunks],
            }
        )
    return _metrics_from_case_results(case_results)


def _metrics_from_case_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        return _empty_metrics()
    total_cases = len(case_results)
    return {
        "total_cases": total_cases,
        "hit_at_1": sum(1 for item in case_results if _has_hit_at(item, 1)),
        "hit_at_3": sum(1 for item in case_results if _has_hit_at(item, 3)),
        "hit_at_5": sum(1 for item in case_results if _has_hit_at(item, 5)),
        "citation_count": sum(int(item["citation_count"]) for item in case_results),
        "zero_hit_count": sum(1 for item in case_results if int(item["returned_count"]) == 0),
        "fallback_count": sum(1 for item in case_results if item["fallback_used"]),
        "average_latency_ms": round(
            sum(float(item["latency_ms"]) for item in case_results) / total_cases,
            3,
        ),
        "cases": case_results,
    }


def _empty_metrics() -> dict[str, Any]:
    return {
        "total_cases": 0,
        "hit_at_1": 0,
        "hit_at_3": 0,
        "hit_at_5": 0,
        "citation_count": 0,
        "zero_hit_count": 0,
        "fallback_count": 0,
        "average_latency_ms": 0.0,
        "cases": [],
    }


def _hit_positions(*, case: RagEvalCase, chunks: list[Any]) -> list[int]:
    positions: list[int] = []
    for index, chunk in enumerate(chunks, start=1):
        if _matches_expected(case=case, chunk=chunk):
            positions.append(index)
    return positions


def _matches_expected(*, case: RagEvalCase, chunk: Any) -> bool:
    if case.expected_doc_ids and chunk.doc_id in set(case.expected_doc_ids):
        return True
    haystack = " ".join(
        str(part or "")
        for part in [
            chunk.title,
            chunk.snippet,
            chunk.source,
            chunk.doc_id,
            chunk.chunk_id,
        ]
    )
    return any(keyword in haystack for keyword in case.expected_keywords)


def _has_hit_at(case_result: dict[str, Any], n: int) -> bool:
    positions = case_result.get("hit_positions") or []
    return any(isinstance(position, int) and position <= n for position in positions)


def _case_from_payload(payload: Any) -> RagEvalCase:
    if not isinstance(payload, dict):
        raise ValueError("Each RAG eval case must be an object.")
    scope = payload.get("knowledge_scope", "mixed")
    if scope not in {"public", "private_sample", "mixed"}:
        raise ValueError(f"Invalid knowledge_scope for eval case {payload.get('id')}: {scope}")
    expected_doc_ids = payload.get("expected_doc_ids") or []
    expected_keywords = payload.get("expected_keywords") or []
    if not expected_doc_ids and not expected_keywords:
        raise ValueError(f"Eval case {payload.get('id')} must define expected_doc_ids or expected_keywords.")
    return RagEvalCase(
        id=str(payload["id"]),
        query=str(payload["query"]),
        knowledge_scope=scope,
        expected_doc_ids=[str(item) for item in expected_doc_ids],
        expected_keywords=[str(item) for item in expected_keywords],
    )


if __name__ == "__main__":
    raise SystemExit(main())
