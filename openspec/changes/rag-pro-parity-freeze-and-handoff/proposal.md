# Change: rag-pro-parity-freeze-and-handoff

## Why

CarbonRag already has the RAG-Pro style spine: KB, documents, chunks, direct upload, quick/acceptance pipeline, search, test QA, answer, eval, timing trace, Ollama provider, and Milvus Docker runtime. The remaining risk is that the team still treats the RAG line as an open construction zone instead of a frozen baseline with explicit handoff boundaries.

## What Changes

- Freeze README and plan status at V1.6.33.
- Define `快速建立 RAG` as the quick pipeline and `完整验收 RAG` as the acceptance pipeline.
- Add V1.6.33 parity checklist and performance gap audit documents.
- Prove Milvus vector-store adapter and client reuse with targeted tests.
- Add Workbench/search/Test QA/AskPage consistency evidence for the Qingmu `217,650 kWh` fixture.
- Mark #1-owned RAG runtime/eval/isolation work separately from #3-owned visual/UX polish.

## Out Of Scope

- No new retrieval algorithm.
- No knowledge graph UI.
- No carbon accounting changes.
- No new model runtime.
- No third-party source tree submission.
