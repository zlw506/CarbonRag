## Why

CarbonRag now has BM25, vector adapter, and BM25+vector hybrid retrieval paths. V1.6.0 needs a repeatable way to compare these strategies before adding heavier retrieval improvements. Reranking should remain optional and local-test safe, with a no-op default and deterministic fake implementation for evaluation and tests.

## What Changes

- Add explicit no-op and fake rerank providers behind the existing AI runtime rerank provider boundary.
- Keep `/ask` defaults unchanged and keep rerank disabled unless explicitly enabled by settings and request parameters.
- Add a fixed RAG retrieval evaluation dataset with public-policy and private-sample cases.
- Add `scripts/rag_eval.py` to run retrieval baselines for BM25, vector, hybrid, and hybrid+rerank and output JSON or Markdown metrics.
- Add tests for no-op/fake rerank behavior and eval script handling, including empty datasets.

## Capabilities

### Modified Capabilities

- `ai-runtime`: Clarify optional rerank provider behavior and deterministic fake reranking.
- `knowledge-rag`: Add a fixed retrieval evaluation baseline for comparing retriever strategies.

## Impact

- Affected modules: M1 AI Runtime, M5 Knowledge/RAG, M8 test/evaluation assets.
- Apply-stage areas: backend AI runtime providers, RAG eval fixtures/script, tests, and OpenSpec change files.
- No GraphRAG, Neo4j, LangGraph, calc/report/session change, or mandatory online rerank provider is proposed.
