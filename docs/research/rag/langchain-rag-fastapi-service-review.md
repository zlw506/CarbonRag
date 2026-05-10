# LangChain-RAG-FastAPI-Service Review

## Scope

Reference path: `3rdparty/LangChain-RAG-FastAPI-Service-master/LangChain-RAG-FastAPI-Service-master`.

This repository is used as a business-logic reference for CarbonRag V1.6.1. Its source is not vendored into CarbonRag. A root `LICENSE` file was not found in the local snapshot during review, so CarbonRag ports the architecture and behavior into native modules and avoids wholesale file copying.

## Useful Reference Points

- `backend/app/rag/rag_service.py`: shows `RagService`, HyDE query generation, document retrieval, reranking, and answer-summary orchestration.
- `backend/app/rag/vector_store.py`: shows a combined Chroma vector store, LangChain BM25 retriever, `EnsembleRetriever`, and query-length-aware sparse/vector weights.
- `backend/app/rag/reorder_service.py`: shows CrossEncoder-based reranking and model-loading boundaries.
- `backend/app/rag/text_spliter.py`: shows `RecursiveCharacterTextSplitter` with Chinese-aware separators.
- `backend/app/agent/agent_tools.py`: shows RAG exposed as an agent tool rather than hidden in route code.
- `backend/app/utils/factory.py`: shows provider factory ideas for embeddings and chat models.
- `backend/pyproject.toml`: confirms dependency families for LangChain, Chroma, sentence-transformers, torch, and LangSmith.

## CarbonRag Mapping

| Reference concept | CarbonRag implementation |
| --- | --- |
| RagService | `backend/app/langchain_rag/service.py` |
| VectorStoreService / Chroma | `backend/app/langchain_rag/vector_store.py` |
| BM25 + EnsembleRetriever | `backend/app/langchain_rag/bm25_store.py` and `retriever.py` |
| HyDE | `backend/app/langchain_rag/hyde.py` |
| CrossEncoder rerank | `backend/app/langchain_rag/reranker.py` |
| Agent tool | `backend/app/langchain_rag/tool.py` registered in AI runtime |
| Structured source references | `backend/app/langchain_rag/citations.py` and ask citations |

## What We Did Not Port

- Django/JWT, MySQL, Redis, and Vue surfaces.
- Full upstream route/service layout.
- LangSmith tracing as a default runtime dependency.
- Any unreviewed local model path assumptions.

## V1.6.1 Principle

CarbonRag keeps its existing auth, session, file parsing, knowledge governance, and React workbench. The port supplies the missing RAG core: metadata-rich documents, Chroma vector indexing, BM25, HyDE, rerank, direct RAG APIs, ask integration, citations, and retrieval traces.
